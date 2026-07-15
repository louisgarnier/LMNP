# Étape 4 — Ingestion unifiée + saisie manuelle — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer un point d'entrée unique `ingest_transactions` pour toute transaction entrante (CSV aujourd'hui, API demain, manuel), rebrancher l'import CSV dessus sans changer un chiffre, et ajouter la saisie manuelle (créer / éclater / écriture croisée).

**Architecture:** Un service `ingestion_service.py` factorise le bloc post-parsing de l'import CSV existant (`transactions.py:1262-1297` : dédoublonnage → insertion → `recalculate_all_balances` → `enrich_transaction` → `recalculate_transaction_amortization`). L'import CSV et les 3 endpoints de saisie manuelle appellent tous ce service. Les lignes « parente éclatée » (`is_split_parent=True`, `category_id=NULL`) sont exclues du solde, de la liste et de l'inbox ; elles sont naturellement exclues du CR/bilan (qui n'agrègent que `category_id IS NOT NULL`).

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pytest. Montants en centimes via `EuroCents` (`backend/database/money.py`). Frontend Next.js/React/TS (client `frontend/src/api/client.ts`, `CategorySelector`).

## Global Constraints

- **Golden master à 0 écart** après chaque tâche touchant les données/calculs : `PYTHONPATH=$PWD python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel` (backend :8000 redémarré sur le code courant). Exit 0 = OK.
- **Non-régression règles à 0** : `PYTHONPATH=$PWD python3 backend/scripts/check_rules_no_regression.py`.
- **Montants en centimes** : toute colonne monétaire = `Column(EuroCents, ...)` ; jamais de float en base.
- **Source de vérité du schéma** = `backend/database/models.py` (ORM) + une migration Python autonome dans `backend/database/migrations/` (sqlite3 direct, idempotente via `PRAGMA table_info`). `schema.sql` est obsolète, NE PAS le maintenir.
- **Sauvegarde `.db` horodatée** dans `backups/` avant toute migration.
- **Erreurs jamais avalées** pour la saisie manuelle (remontée HTTP). Pour le rebranchement CSV, on **préserve à l'identique** le comportement actuel (amortissement best-effort inclus) afin de garantir golden 0.
- **Tests dans le harnais isolé** (`db_session`/`client`), jamais sur la base de prod. Ne jamais utiliser `SessionLocal`/`next(get_db())` dans un test (quarantaine `conftest.py`).
- **Commits** git natifs (pas `git_ops.py`), périmètre `backend`/`frontend`. Ne jamais stager `backend/data/input/trades/trades_evry_2025.csv`.
- **`property_id` explicite** partout (pas d'auth).

---

## File Structure

- `backend/database/models.py` — +classe `BankAccount`, +5 colonnes sur `Transaction`, +relation `Property.bank_accounts`.
- `backend/database/migrations/add_ingestion_fields.py` — **créé** : migration (colonnes + table + index partiel + backfill `source='csv'`).
- `backend/api/services/ingestion_service.py` — **créé** : `ingest_transactions`, `_deduplicate`, `_insert_and_process`.
- `backend/api/utils/balance_utils.py` — modifié : exclure `is_split_parent` du recalcul de solde.
- `backend/api/routes/transactions.py` — modifié : rebranche `POST /transactions/import` ; +`POST /transactions/manual`, `POST/DELETE /transactions/{id}/split`, `POST /transactions/cross-entry` ; exclut `is_split_parent` dans `GET /transactions`.
- `backend/api/routes/inbox.py` — modifié : exclut `is_split_parent` de la liste inbox.
- `backend/api/models.py` — +champs `is_split_parent`/`parent_transaction_id`/`source` dans `TransactionResponse` ; +modèles Pydantic `ManualTransactionIn`, `SplitIn`, `CrossEntryIn`.
- `frontend/src/api/client.ts` — +`transactionsAPI.createManual/splitTransaction/undoSplit/crossEntry`.
- `frontend/src/components/TransactionsTable.tsx` (ou composant frère) — +bouton ➕, action ✂️, formulaire ⇄.
- Tests : `backend/tests/test_ingestion_service.py`, `test_csv_import_rewire.py`, `test_split_exclusion.py`, `test_manual_transactions.py`, `test_split_transactions.py`, `test_cross_entry.py` ; `frontend/__tests__/manual-entry.test.tsx`.

---

### Task 1 : Schéma — colonnes ingestion + table bank_accounts + migration

**Files:**
- Modify: `backend/database/models.py:56-77` (classe `Transaction`), `backend/database/models.py:20-35` (classe `Property`)
- Create: `backend/database/migrations/add_ingestion_fields.py`
- Test: `backend/tests/test_ingestion_schema.py`

**Interfaces:**
- Produces: `Transaction.account_id`, `Transaction.external_id`, `Transaction.source`, `Transaction.parent_transaction_id`, `Transaction.is_split_parent` ; classe `BankAccount` ; migration `migrate()`.

- [ ] **Step 1 : Test d'échec (colonnes + table absentes → présentes après migration logique ORM)**

Créer `backend/tests/test_ingestion_schema.py` :
```python
from datetime import date
from backend.database.models import Transaction, BankAccount, Property


def test_transaction_has_ingestion_fields(db_session):
    prop = Property(name="T-schema")
    db_session.add(prop)
    db_session.flush()
    tx = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=10.0,
                     nom="X", solde=10.0, source="manual", is_split_parent=False)
    db_session.add(tx)
    db_session.flush()
    assert tx.source == "manual"
    assert tx.is_split_parent is False
    assert tx.account_id is None
    assert tx.external_id is None
    assert tx.parent_transaction_id is None


def test_bank_account_model(db_session):
    prop = Property(name="T-bank")
    db_session.add(prop)
    db_session.flush()
    acc = BankAccount(property_id=prop.id, bank_name="Boursorama", iban_masked="FR76****1234")
    db_session.add(acc)
    db_session.flush()
    assert acc.id is not None
    assert acc.property_id == prop.id
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_ingestion_schema.py -q`
Expected: FAIL (`ImportError: cannot import name 'BankAccount'` puis `TypeError` sur champs inconnus).

- [ ] **Step 3 : Modifier les modèles ORM**

Dans `backend/database/models.py`, classe `Transaction`, ajouter APRÈS `category_id` (l.66) :
```python
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)
    source = Column(String(10), nullable=False, default="csv")  # csv | api | manual
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, index=True)
    is_split_parent = Column(Boolean, nullable=False, default=False)
```
Dans `__table_args__` de `Transaction`, ajouter un index partiel d'unicité :
```python
        Index('idx_tx_account_external_unique', 'account_id', 'external_id',
              unique=True, sqlite_where=text('external_id IS NOT NULL')),
```
(importer en tête si absent : `from sqlalchemy import text` — vérifier l'import existant `Boolean` dans la ligne `from sqlalchemy import (...)`).

Ajouter la classe `BankAccount` après la classe `Transaction` :
```python
class BankAccount(Base):
    """Compte bancaire d'un bien. Peuplé à l'étape 5 (Enable Banking) ; vide en étape 4."""
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(255))
    iban_masked = Column(String(64))
    eb_account_uid = Column(String(255), nullable=True)
    eb_session_id = Column(String(255), nullable=True)
    session_valid_until = Column(Date, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_tx_cursor = Column(String(255), nullable=True)

    property = relationship("Property", back_populates="bank_accounts")
```
Dans la classe `Property` (l.20-35), ajouter la relation :
```python
    bank_accounts = relationship("BankAccount", back_populates="property", cascade="all, delete-orphan")
```

- [ ] **Step 4 : Vérifier que le test passe**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_ingestion_schema.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5 : Écrire la migration Python autonome**

Créer `backend/database/migrations/add_ingestion_fields.py` (modèle : `add_loan_dates_to_loan_configs.py`) :
```python
"""Étape 4 : colonnes d'ingestion sur transactions + table bank_accounts. Idempotent."""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "lmnp.db"


def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def migrate():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        existing = _cols(conn, "transactions")
        adds = [
            ("account_id", "INTEGER"),
            ("external_id", "VARCHAR(255)"),
            ("source", "VARCHAR(10) NOT NULL DEFAULT 'csv'"),
            ("parent_transaction_id", "INTEGER"),
            ("is_split_parent", "BOOLEAN NOT NULL DEFAULT 0"),
        ]
        for name, decl in adds:
            if name not in existing:
                cur.execute(f"ALTER TABLE transactions ADD COLUMN {name} {decl}")
                print(f"   ✅ transactions.{name} ajoutée")
            else:
                print(f"   ⏭️  transactions.{name} déjà présente")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                bank_name VARCHAR(255),
                iban_masked VARCHAR(64),
                eb_account_uid VARCHAR(255),
                eb_session_id VARCHAR(255),
                session_valid_until DATE,
                last_sync_at DATETIME,
                last_tx_cursor VARCHAR(255)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bank_accounts_property_id ON bank_accounts(property_id)")
        cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_account_external_unique
                       ON transactions(account_id, external_id) WHERE external_id IS NOT NULL""")
        # backfill de sûreté (les lignes existantes n'ont pas de source explicite)
        cur.execute("UPDATE transactions SET source='csv' WHERE source IS NULL OR source=''")
        conn.commit()
        print("✅ Migration add_ingestion_fields terminée")
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
```

- [ ] **Step 6 : Backup + exécuter la migration sur la base de prod**

```bash
cp backend/database/lmnp.db "backups/lmnp_avant_etape4_$(date +%Y%m%d_%H%M%S).db"
PYTHONPATH=$PWD python3 backend/database/migrations/add_ingestion_fields.py
```
Expected: lignes `✅ ... ajoutée` puis `✅ Migration ... terminée`. Ré-exécuter une 2e fois → tout en `⏭️ déjà présente` (idempotence).

- [ ] **Step 7 : Vérifier golden inchangé (colonnes only, aucun chiffre bougé)**

Redémarrer le backend sur le code courant puis :
```bash
PYTHONPATH=$PWD python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel
```
Expected: `Aucune différence détectée. OK.`

- [ ] **Step 8 : Commit**
```bash
git add backend/database/models.py backend/database/migrations/add_ingestion_fields.py backend/tests/test_ingestion_schema.py
git commit -m "[REFONTE] feat(back): schéma ingestion (bank_accounts + champs transaction)"
```

---

### Task 2 : Service d'ingestion unifié

**Files:**
- Create: `backend/api/services/ingestion_service.py`
- Test: `backend/tests/test_ingestion_service.py`

**Interfaces:**
- Consumes: `enrich_transaction(transaction, db, rules=None)` (`enrichment_service.py:56`), `recalculate_all_balances(db, property_id)` (`balance_utils.py:52`), `recalculate_transaction_amortization(db, transaction_id)` (`amortization_service.py:131`), `EuroCents` (montants ORM en euros).
- Produces:
  `ingest_transactions(db, property_id, account_id, rows, source) -> dict` avec `rows` = `list[dict]` de forme `{"date": date, "quantite": float, "nom": str, "external_id": str|None}`, retour `{"inserted": int, "deduplicated": int, "ids": list[int]}`.

- [ ] **Step 1 : Test d'échec — dédoublonnage + insertion + classification + solde**

Créer `backend/tests/test_ingestion_service.py` :
```python
from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup, ClassificationRule
from backend.api.services.ingestion_service import ingest_transactions


def _seed_property_with_rule(db_session):
    grp = CategoryGroup(label="Produits", nature="produits")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False)
    db_session.add(cat); db_session.flush()
    prop = Property(name="Ingest-1")
    db_session.add(prop); db_session.flush()
    rule = ClassificationRule(pattern="LOYER", match_type="prefix", category_id=cat.id,
                              property_id=None, priority=0, source="manual", strict_ratio=False)
    db_session.add(rule); db_session.flush()
    return prop, cat


def test_ingest_inserts_and_classifies(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    res = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert res["inserted"] == 1
    assert res["deduplicated"] == 0
    tx = db_session.query(Transaction).filter(Transaction.property_id == prop.id).one()
    assert tx.category_id == cat.id          # classé par la règle
    assert tx.source == "csv"
    assert tx.solde == 390.0                  # solde recalculé


def test_ingest_dedup_fallback_key(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    ingest_transactions(db_session, prop.id, None, rows, "csv")
    res2 = ingest_transactions(db_session, prop.id, None, rows, "csv")   # même ligne
    assert res2["inserted"] == 0
    assert res2["deduplicated"] == 1
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 1


def test_ingest_dedup_external_id(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 2, 1), "quantite": 100.0, "nom": "VIR", "external_id": "EB-123"}]
    ingest_transactions(db_session, prop.id, None, rows, "api")
    # même external_id, nom/montant différents → toujours un doublon
    rows2 = [{"date": date(2023, 2, 2), "quantite": 999.0, "nom": "AUTRE", "external_id": "EB-123"}]
    res = ingest_transactions(db_session, prop.id, None, rows2, "api")
    assert res["inserted"] == 0 and res["deduplicated"] == 1
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_ingestion_service.py -q`
Expected: FAIL (`ModuleNotFoundError: ingestion_service`).

- [ ] **Step 3 : Implémenter le service**

Créer `backend/api/services/ingestion_service.py` :
```python
"""Point d'entrée unique d'ingestion : CSV, API, manuel. Étape 4."""
import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from backend.database.models import Transaction
from backend.api.services.enrichment_service import enrich_transaction
from backend.api.utils.balance_utils import recalculate_all_balances

logger = logging.getLogger(__name__)


def _is_duplicate(db: Session, property_id: int, account_id: Optional[int],
                  d: date, quantite: float, nom: str, external_id: Optional[str]) -> bool:
    if external_id is not None:
        exists = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.external_id == external_id,
        ).first()
        return exists is not None
    exists = db.query(Transaction).filter(
        Transaction.property_id == property_id,
        Transaction.date == d,
        Transaction.quantite == quantite,   # EuroCents : égalité au centime
        Transaction.nom == nom,
    ).first()
    return exists is not None


def ingest_transactions(db: Session, property_id: int, account_id: Optional[int],
                        rows: list[dict], source: str) -> dict:
    """Normalise → dédoublonne → insère → classe → recalcule soldes + amortissements.
    Retourne {"inserted", "deduplicated", "ids"}. L'appelant gère le commit final
    (enrich_transaction/recalculate_all_balances committent déjà, comme dans l'import CSV)."""
    inserted, deduplicated, new_ids = 0, 0, []
    new_txs = []
    for r in rows:
        nom = (r["nom"] or "").strip()
        if _is_duplicate(db, property_id, account_id, r["date"], r["quantite"], nom, r.get("external_id")):
            deduplicated += 1
            continue
        tx = Transaction(
            property_id=property_id, account_id=account_id,
            date=r["date"], quantite=r["quantite"], nom=nom,
            solde=0.0, source=source, external_id=r.get("external_id"),
            is_split_parent=False,
        )
        db.add(tx)
        new_txs.append(tx)
        inserted += 1
    db.flush()

    recalculate_all_balances(db, property_id)   # solde correct (exclut is_split_parent — Task 4)

    for tx in new_txs:
        new_ids.append(tx.id)
        enrich_transaction(tx, db)              # pose category_id via règles étape 3
        try:
            from backend.api.services.amortization_service import recalculate_transaction_amortization
            recalculate_transaction_amortization(db, tx.id)
        except Exception as e:                  # best-effort, identique à l'import CSV actuel
            logger.warning(f"[ingest] amortissement tx {tx.id} ignoré: {e}")

    db.commit()
    return {"inserted": inserted, "deduplicated": deduplicated, "ids": new_ids}
```

- [ ] **Step 4 : Vérifier que les tests passent**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_ingestion_service.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5 : Commit**
```bash
git add backend/api/services/ingestion_service.py backend/tests/test_ingestion_service.py
git commit -m "[REFONTE] feat(back): service d'ingestion unifié (dédoublonnage + classif + recalculs)"
```

---

### Task 3 : Rebrancher l'import CSV sur le service (golden-critique)

**Files:**
- Modify: `backend/api/routes/transactions.py:1210-1297` (boucle d'insertion de `import_file`)
- Test: `backend/tests/test_csv_import_rewire.py`

**Interfaces:**
- Consumes: `ingest_transactions(db, property_id, account_id, rows, source)` (Task 2).

**Contexte pour l'implémenteur :** `import_file` (transactions.py:951-1347) parse le CSV, gère les colonnes combinées, valide, génère les noms `nom_a_justifier_N`, puis (l.1210-1297) fait la boucle dédoublonnage+insertion+solde+enrich+amortissement, puis enregistre le `FileImport`. **Ne PAS toucher au parsing/validation** (l.951-1209). Remplacer UNIQUEMENT le bloc l.1210-1297 : construire la liste `rows` normalisée (date `_date_parsed.date()`, `quantite` float, `nom` — y compris la génération `nom_a_justifier_N` et le comptage des doublons pour les stats affichées) puis appeler `ingest_transactions(db, property_id, account_id=None, rows, source="csv")`. Les compteurs `imported_count`/`duplicates_count` du `FileImportResponse` viennent désormais du retour `{"inserted", "deduplicated"}`. Conserver l'enregistrement `FileImport` (l.1300-1321) tel quel avec ces compteurs.

- [ ] **Step 1 : Test d'échec — réimport = 0 nouveau, mêmes données**

Créer `backend/tests/test_csv_import_rewire.py` :
```python
import io
from datetime import date
from backend.database.models import Property, Transaction
from backend.api.services.ingestion_service import ingest_transactions


def test_reimport_same_rows_is_idempotent(db_session):
    prop = Property(name="Reimport")
    db_session.add(prop); db_session.flush()
    rows = [
        {"date": date(2023, 1, 1), "quantite": 100.0, "nom": "A", "external_id": None},
        {"date": date(2023, 1, 2), "quantite": -50.0, "nom": "B", "external_id": None},
    ]
    r1 = ingest_transactions(db_session, prop.id, None, rows, "csv")
    r2 = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert r1["inserted"] == 2
    assert r2["inserted"] == 0 and r2["deduplicated"] == 2
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 2
```
(Le test HTTP complet de la route via `client` est difficile à seeder proprement — la garantie de non-régression sur la vraie route est le **golden master** en Step 4.)

- [ ] **Step 2 : Vérifier l'échec puis rebrancher**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_csv_import_rewire.py -q` → PASS (le service existe déjà, ce test valide l'invariant). Puis appliquer la modification de `import_file` décrite dans le Contexte ci-dessus.

- [ ] **Step 3 : Vérifier que la suite backend passe**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests -q`
Expected: tout vert (le nombre peut varier ; aucune régression).

- [ ] **Step 4 : GOLDEN — réimport réel ne change rien**

Redémarrer le backend sur le code courant. Le golden compare les états calculés à la référence. Comme la classification et les soldes sont recalculés à l'identique :
```bash
PYTHONPATH=$PWD python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel
PYTHONPATH=$PWD python3 backend/scripts/check_rules_no_regression.py
```
Expected: `Aucune différence détectée. OK.` et `0 divergence(s)`.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/transactions.py backend/tests/test_csv_import_rewire.py
git commit -m "[REFONTE] refactor(back): import CSV rebranché sur ingest_transactions (golden 0)"
```

---

### Task 4 : Exclure les lignes parentes éclatées (solde + liste + inbox)

**Files:**
- Modify: `backend/api/utils/balance_utils.py:12` et `:52` (les deux recalculs)
- Modify: `backend/api/routes/transactions.py:106` (`GET /transactions`)
- Modify: `backend/api/routes/inbox.py` (requête de liste inbox)
- Test: `backend/tests/test_split_exclusion.py`

**Interfaces:**
- Produces: garantie que `is_split_parent=True` est exclu de tout solde, de la liste transactions et de l'inbox. (CR/bilan : exclusion naturelle via `category_id IS NULL`, aucune modif — vérifié par test.)

- [ ] **Step 1 : Test d'échec**

Créer `backend/tests/test_split_exclusion.py` :
```python
from datetime import date
from backend.database.models import Property, Transaction
from backend.api.utils.balance_utils import recalculate_all_balances


def test_split_parent_excluded_from_balance(db_session):
    prop = Property(name="Excl")
    db_session.add(prop); db_session.flush()
    # parente masquée (ne doit PAS compter), 2 enfants qui la remplacent
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=280.0, nom="MATERA",
                         solde=0.0, source="csv", is_split_parent=True, category_id=None)
    c1 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=450.0, nom="loyer",
                     solde=0.0, source="manual", is_split_parent=False)
    c2 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=-170.0, nom="agence",
                     solde=0.0, source="manual", is_split_parent=False)
    db_session.add_all([parent, c1, c2]); db_session.flush()
    recalculate_all_balances(db_session, prop.id)
    db_session.refresh(c2)
    # solde final = 450 - 170 = 280 (la parente 280 n'est PAS comptée en plus)
    last = db_session.query(Transaction).filter(
        Transaction.property_id == prop.id, Transaction.is_split_parent == False
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).first()
    assert last.solde == 280.0
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_split_exclusion.py -q`
Expected: FAIL (solde = 560, la parente compte deux fois).

- [ ] **Step 3 : Ajouter le filtre `is_split_parent == False`**

Dans `backend/api/utils/balance_utils.py`, dans **les deux** fonctions (`recalculate_balances_from_date` l.12, `recalculate_all_balances` l.52), ajouter à la requête qui itère les transactions le filtre `.filter(Transaction.is_split_parent == False)`. Exemple pour `recalculate_all_balances` :
```python
    transactions = db.query(Transaction).filter(
        Transaction.property_id == property_id,
        Transaction.is_split_parent == False,
    ).order_by(Transaction.date, Transaction.id).all()
```
Dans `backend/api/routes/transactions.py:106`, ajouter le même filtre à la requête de base de `get_transactions` :
```python
    base_query = db.query(Transaction).filter(
        Transaction.property_id == property_id,
        Transaction.is_split_parent == False,
    )
```
Dans `backend/api/routes/inbox.py`, à la requête qui liste les transactions non classées (`category_id IS NULL`), ajouter `Transaction.is_split_parent == False`.

- [ ] **Step 4 : Vérifier que le test passe + suite + golden**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_split_exclusion.py backend/tests -q`
Expected: PASS. Puis (backend redémarré) golden + non-régression = 0 (aucune ligne `is_split_parent` en prod → comportement inchangé).

- [ ] **Step 5 : Commit**
```bash
git add backend/api/utils/balance_utils.py backend/api/routes/transactions.py backend/api/routes/inbox.py backend/tests/test_split_exclusion.py
git commit -m "[REFONTE] feat(back): exclusion des lignes parentes éclatées (solde/liste/inbox)"
```

---

### Task 5 : Endpoint de saisie manuelle simple

**Files:**
- Modify: `backend/api/routes/transactions.py` (nouvel endpoint), `backend/api/models.py` (Pydantic `ManualTransactionIn`)
- Test: `backend/tests/test_manual_transactions.py`

**Interfaces:**
- Consumes: `ingest_transactions` (Task 2), `update_transaction_classification`/`assign_category` non requis (catégorie posée directement si fournie).
- Produces: `POST /api/transactions/manual` body `{property_id:int, date:str(YYYY-MM-DD), quantite:float, nom:str, category_id:int|null}` → `{id, category_id}`.

- [ ] **Step 1 : Test d'échec**

Créer `backend/tests/test_manual_transactions.py` :
```python
from datetime import date
from backend.database.models import Property, Category, CategoryGroup, Transaction


def test_manual_create_with_category(client, db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="Manual"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/manual", json={
        "property_id": prop.id, "date": "2023-03-01", "quantite": 390.0,
        "nom": "Loyer manuel", "category_id": cat.id,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    tx = db_session.query(Transaction).get(body["id"])
    assert tx.source == "manual"
    assert tx.category_id == cat.id
    assert tx.quantite == 390.0


def test_manual_create_without_category_goes_unclassified(client, db_session):
    prop = Property(name="Manual2"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/manual", json={
        "property_id": prop.id, "date": "2023-03-02", "quantite": -50.0,
        "nom": "Inconnu", "category_id": None,
    })
    assert resp.status_code == 200
    tx = db_session.query(Transaction).get(resp.json()["id"])
    assert tx.category_id is None   # → apparaîtra dans l'inbox
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_manual_transactions.py -q`
Expected: FAIL (404 route inconnue).

- [ ] **Step 3 : Implémenter le modèle Pydantic + l'endpoint**

Dans `backend/api/models.py`, ajouter :
```python
class ManualTransactionIn(BaseModel):
    property_id: int
    date: date
    quantite: float
    nom: str
    category_id: Optional[int] = None
```
(vérifier les imports `date`, `Optional`, `BaseModel` en tête.)

Dans `backend/api/routes/transactions.py`, ajouter :
```python
@router.post("/transactions/manual")
def create_manual_transaction(body: ManualTransactionIn, db: Session = Depends(get_db)):
    validate_property_id(db, body.property_id)
    if body.category_id is not None and db.get(Category, body.category_id) is None:
        raise HTTPException(400, f"category_id inconnu: {body.category_id}")
    from backend.api.services.ingestion_service import ingest_transactions
    res = ingest_transactions(db, body.property_id, None,
                              [{"date": body.date, "quantite": body.quantite,
                                "nom": body.nom, "external_id": None}], "manual")
    if not res["ids"]:
        raise HTTPException(409, "Transaction identique déjà existante (doublon)")
    tx = db.get(Transaction, res["ids"][0])
    # catégorie explicite fournie : prime sur la classification auto
    if body.category_id is not None and tx.category_id != body.category_id:
        tx.category_id = body.category_id
        db.commit()
    return {"id": tx.id, "category_id": tx.category_id}
```
(vérifier imports `ManualTransactionIn`, `Category`, `Transaction`, `HTTPException`, `Depends`, `get_db`, `validate_property_id` — tous déjà présents dans le fichier sauf `ManualTransactionIn` à ajouter à l'import de `models`.)

- [ ] **Step 4 : Vérifier que les tests passent**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_manual_transactions.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/transactions.py backend/api/models.py backend/tests/test_manual_transactions.py
git commit -m "[REFONTE] feat(back): POST /transactions/manual (saisie manuelle simple)"
```

---

### Task 6 : Endpoints d'éclatement (split + annulation)

**Files:**
- Modify: `backend/api/routes/transactions.py` (2 endpoints), `backend/api/models.py` (`SplitIn`, `SplitPartIn`)
- Test: `backend/tests/test_split_transactions.py`

**Interfaces:**
- Consumes: `recalculate_all_balances`, `enrich_transaction`.
- Produces: `POST /api/transactions/{id}/split` body `{parts:[{quantite:float, nom:str, category_id:int|null}]}` → `{parent_id, child_ids}` ; `DELETE /api/transactions/{id}/split` → `{restored_id}`.

- [ ] **Step 1 : Test d'échec**

Créer `backend/tests/test_split_transactions.py` :
```python
from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup


def _seed(db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="Split"); db_session.add(prop); db_session.flush()
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 5), quantite=280.0,
                         nom="MATERA", solde=280.0, source="csv", is_split_parent=False, category_id=cat.id)
    db_session.add(parent); db_session.commit()
    return prop, cat, parent


def test_split_replaces_parent_with_children(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 450.0, "nom": "loyer", "category_id": cat.id},
        {"quantite": -170.0, "nom": "frais agence", "category_id": cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    db_session.refresh(parent)
    assert parent.is_split_parent is True
    assert parent.category_id is None            # masquée → hors CR/bilan
    children = db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).all()
    assert len(children) == 2
    assert sum(c.quantite for c in children) == 280.0


def test_split_rejects_wrong_sum(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 100.0, "nom": "x", "category_id": None},
    ]})
    assert resp.status_code == 400
    db_session.refresh(parent)
    assert parent.is_split_parent is False       # rien n'a changé
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0


def test_undo_split_restores_parent(client, db_session):
    prop, cat, parent = _seed(db_session)
    client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 280.0, "nom": "tout", "category_id": cat.id},
    ]})
    resp = client.delete(f"/api/transactions/{parent.id}/split")
    assert resp.status_code == 200
    db_session.refresh(parent)
    assert parent.is_split_parent is False
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_split_transactions.py -q`
Expected: FAIL (404).

- [ ] **Step 3 : Implémenter modèles + endpoints**

Dans `backend/api/models.py` :
```python
class SplitPartIn(BaseModel):
    quantite: float
    nom: str
    category_id: Optional[int] = None

class SplitIn(BaseModel):
    parts: list[SplitPartIn]
```
Dans `backend/api/routes/transactions.py` :
```python
@router.post("/transactions/{transaction_id}/split")
def split_transaction(transaction_id: int, body: SplitIn, db: Session = Depends(get_db)):
    parent = db.get(Transaction, transaction_id)
    if not parent:
        raise HTTPException(404, "Transaction introuvable")
    if parent.is_split_parent:
        raise HTTPException(400, "Transaction déjà éclatée")
    if not body.parts:
        raise HTTPException(400, "Au moins une ligne requise")
    # garde-fou dur : somme au centime == montant parent
    total_cents = sum(round(p.quantite * 100) for p in body.parts)
    if total_cents != round(parent.quantite * 100):
        raise HTTPException(400, f"La somme des lignes ({total_cents/100:.2f}) doit égaler {parent.quantite:.2f}")
    for p in body.parts:
        if p.category_id is not None and db.get(Category, p.category_id) is None:
            raise HTTPException(400, f"category_id inconnu: {p.category_id}")

    parent.is_split_parent = True
    parent.category_id = None
    child_ids = []
    for p in body.parts:
        child = Transaction(property_id=parent.property_id, account_id=parent.account_id,
                            date=parent.date, quantite=p.quantite, nom=p.nom, solde=0.0,
                            source="manual", parent_transaction_id=parent.id, is_split_parent=False)
        db.add(child); db.flush()
        if p.category_id is not None:
            child.category_id = p.category_id
        else:
            enrich_transaction(child, db)
        child_ids.append(child.id)
    db.flush()
    recalculate_all_balances(db, parent.property_id)
    db.commit()
    return {"parent_id": parent.id, "child_ids": child_ids}


@router.delete("/transactions/{transaction_id}/split")
def undo_split(transaction_id: int, db: Session = Depends(get_db)):
    parent = db.get(Transaction, transaction_id)
    if not parent or not parent.is_split_parent:
        raise HTTPException(404, "Aucun éclatement à annuler")
    db.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).delete()
    parent.is_split_parent = False
    db.flush()
    recalculate_all_balances(db, parent.property_id)
    db.commit()
    return {"restored_id": parent.id}
```
(vérifier imports `SplitIn`, `enrich_transaction`, `recalculate_all_balances` en tête du fichier route.)

- [ ] **Step 4 : Vérifier que les tests passent**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_split_transactions.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/transactions.py backend/api/models.py backend/tests/test_split_transactions.py
git commit -m "[REFONTE] feat(back): éclatement d'une ligne (split + annulation)"
```

---

### Task 7 : Endpoint d'écriture croisée (paire qui s'annule)

**Files:**
- Modify: `backend/api/routes/transactions.py` (endpoint), `backend/api/models.py` (`CrossEntryIn`)
- Test: `backend/tests/test_cross_entry.py`

**Interfaces:**
- Produces: `POST /api/transactions/cross-entry` body `{property_id:int, date:str, montant:float, debit:{nom:str, category_id:int|null}, credit:{nom:str, category_id:int|null}}` → `{debit_id, credit_id}`. Crée `−montant` (debit) et `+montant` (credit).

- [ ] **Step 1 : Test d'échec**

Créer `backend/tests/test_cross_entry.py` :
```python
from backend.database.models import Property, Transaction, Category, CategoryGroup


def test_cross_entry_nets_to_zero(client, db_session):
    g1 = CategoryGroup(label="Frais d'acquisition", nature="charges_deductibles"); db_session.add(g1); db_session.flush()
    c_notaire = Category(label="Frais de notaire", group_id=g1.id, is_custom=False); db_session.add(c_notaire)
    g2 = CategoryGroup(label="Compte courant d'associé", nature="passif"); db_session.add(g2); db_session.flush()
    c_cc = Category(label="Compte courant d'associé", group_id=g2.id, is_custom=False); db_session.add(c_cc)
    prop = Property(name="Cross"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/cross-entry", json={
        "property_id": prop.id, "date": "2023-04-01", "montant": 15000.0,
        "debit": {"nom": "Frais de notaire", "category_id": c_notaire.id},
        "credit": {"nom": "Apport compte courant", "category_id": c_cc.id},
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    debit = db_session.query(Transaction).get(body["debit_id"])
    credit = db_session.query(Transaction).get(body["credit_id"])
    assert debit.quantite == -15000.0 and credit.quantite == 15000.0
    assert debit.quantite + credit.quantite == 0.0
    assert debit.source == "manual" and credit.source == "manual"
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_cross_entry.py -q`
Expected: FAIL (404).

- [ ] **Step 3 : Implémenter modèle + endpoint**

Dans `backend/api/models.py` :
```python
class CrossEntryLegIn(BaseModel):
    nom: str
    category_id: Optional[int] = None

class CrossEntryIn(BaseModel):
    property_id: int
    date: date
    montant: float           # montant positif ; debit = -montant, credit = +montant
    debit: CrossEntryLegIn
    credit: CrossEntryLegIn
```
Dans `backend/api/routes/transactions.py` :
```python
@router.post("/transactions/cross-entry")
def create_cross_entry(body: CrossEntryIn, db: Session = Depends(get_db)):
    validate_property_id(db, body.property_id)
    for leg in (body.debit, body.credit):
        if leg.category_id is not None and db.get(Category, leg.category_id) is None:
            raise HTTPException(400, f"category_id inconnu: {leg.category_id}")
    from backend.api.services.ingestion_service import ingest_transactions
    res = ingest_transactions(db, body.property_id, None, [
        {"date": body.date, "quantite": -abs(body.montant), "nom": body.debit.nom, "external_id": None},
        {"date": body.date, "quantite": abs(body.montant), "nom": body.credit.nom, "external_id": None},
    ], "manual")
    if len(res["ids"]) != 2:
        raise HTTPException(409, "Écriture croisée : au moins une ligne est un doublon")
    debit_id, credit_id = res["ids"][0], res["ids"][1]
    debit, credit = db.get(Transaction, debit_id), db.get(Transaction, credit_id)
    if body.debit.category_id is not None:
        debit.category_id = body.debit.category_id
    if body.credit.category_id is not None:
        credit.category_id = body.credit.category_id
    db.commit()
    return {"debit_id": debit_id, "credit_id": credit_id}
```

- [ ] **Step 4 : Vérifier que le test passe**

Run: `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_cross_entry.py -q`
Expected: PASS.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/transactions.py backend/api/models.py backend/tests/test_cross_entry.py
git commit -m "[REFONTE] feat(back): écriture croisée (paire qui s'annule)"
```

---

### Task 8 : Frontend — saisie manuelle sur « Toutes les transactions »

**Files:**
- Modify: `frontend/src/api/client.ts` (méthodes client)
- Modify: `frontend/src/components/TransactionsTable.tsx` (bouton ➕, action ✂️, formulaire ⇄)
- Test: `frontend/__tests__/manual-entry.test.tsx`

**Interfaces:**
- Consumes: endpoints Tasks 5/6/7, `CategorySelector` (`frontend/src/components/CategorySelector.tsx`).
- Produces: `transactionsAPI.createManual(payload)`, `.splitTransaction(id, parts)`, `.undoSplit(id)`, `.crossEntry(payload)`.

- [ ] **Step 1 : Ajouter les méthodes client**

Dans `frontend/src/api/client.ts`, dans l'objet `transactionsAPI`, ajouter (suivre le style `fetchAPI` existant, `property_id` explicite) :
```ts
  createManual: (p: { property_id: number; date: string; quantite: number; nom: string; category_id: number | null }) =>
    fetchAPI(`/api/transactions/manual`, { method: 'POST', body: JSON.stringify(p) }),
  splitTransaction: (id: number, parts: { quantite: number; nom: string; category_id: number | null }[]) =>
    fetchAPI(`/api/transactions/${id}/split`, { method: 'POST', body: JSON.stringify({ parts }) }),
  undoSplit: (id: number) =>
    fetchAPI(`/api/transactions/${id}/split`, { method: 'DELETE' }),
  crossEntry: (p: { property_id: number; date: string; montant: number;
                    debit: { nom: string; category_id: number | null };
                    credit: { nom: string; category_id: number | null } }) =>
    fetchAPI(`/api/transactions/cross-entry`, { method: 'POST', body: JSON.stringify(p) }),
```

- [ ] **Step 2 : Test d'échec (rendu du formulaire + appel client)**

Créer `frontend/__tests__/manual-entry.test.tsx` : monter le composant de saisie manuelle, remplir date/montant/nom, choisir une catégorie via `CategorySelector` (mocké), cliquer « Ajouter », et affirmer que `transactionsAPI.createManual` est appelé avec le bon payload. (Suivre le style des tests existants `frontend/__tests__/` — mock de `../src/api/client`.)

- [ ] **Step 3 : Implémenter l'UI**

Sur l'onglet « Toutes les transactions » (`TransactionsTable.tsx`) :
- Un bouton **➕ Ajouter** ouvre un petit formulaire (date, montant €, nom, `CategorySelector`) → `createManual` → refetch de la liste.
- Une action **✂️ Éclater** sur une ligne ouvre un formulaire à N lignes (montant + nom + `CategorySelector` chacune), affiche en direct la somme et **désactive « Valider »** tant que somme ≠ montant d'origine → `splitTransaction` → refetch. Les lignes `is_split_parent` ne sont pas renvoyées par le backend (Task 4), donc rien à filtrer côté front.
- Un bouton **⇄ Écriture croisée** ouvre un formulaire (date, montant, 2 volets nom+catégorie) → `crossEntry` → refetch.
- Toute erreur API affichée en bannière `role="alert"` (jamais avalée), style cohérent avec `InboxScreen`/`RulesScreen`.

- [ ] **Step 4 : Vérifier build + jest**

Run: `cd frontend && npm test -- --watchAll=false` puis `npm run build`
Expected: tests verts, build OK.

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/api/client.ts frontend/src/components/TransactionsTable.tsx frontend/__tests__/manual-entry.test.tsx
git commit -m "[REFONTE] feat(front): saisie manuelle (créer / éclater / écriture croisée)"
```

---

## Livrable de fin d'étape

- Table `bank_accounts` créée (vide) ; `transactions` + `account_id`/`external_id`/`source`/`parent_transaction_id`/`is_split_parent`.
- Service `ingest_transactions` unique ; import CSV rebranché (comportement inchangé, golden 0).
- Saisie manuelle : créer / éclater / écriture croisée, sur « Toutes les transactions ».
- Suite backend verte ; **golden 0** ; **non-régression 0** ; build + jest front verts.
- Prêt étape 5 : brancher le client Enable Banking sur `ingest_transactions(source="api")` + remplir `bank_accounts`.
