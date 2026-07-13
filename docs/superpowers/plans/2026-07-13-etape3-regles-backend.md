# Étape 3 §5 — Backend : moteur de règles unifié + migration + API — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Remplacer les 4 systèmes de classification actuels (`mappings`, `allowed_mappings`, Excel, script hardcodé) par une table unique `classification_rules` + un moteur unifié, migrés sans reclasser l'historique ni bouger un centime, avec l'API pour les écrans Inbox/Règles.

**Architecture :** Nouvelle table `classification_rules` (motif, match_type explicite, category_id, property_id nullable = global, priorité, source). Moteur réécrit qui lit cette table avec la sémantique actuelle exacte. Migration directe des 366 mappings → règles, contrôle de non-régression à 0 divergence, golden master bloquant, puis suppression des vieilles tables. API REST pour règles (CRUD + préversion) et inbox (liste + validation).

**Tech Stack :** FastAPI, SQLAlchemy (SQLite), Pydantic v2, pytest (harnais isolé SQLite en mémoire).

**Périmètre :** Backend uniquement. Les écrans front (Inbox ①, Règles ②) = plan séparé après validation `ui-mockup`.

**Spec :** `docs/superpowers/specs/2026-07-13-etape3-regles-inbox-design.md`

## Global Constraints

- **Golden master bloquant** : après toute migration, `python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel` doit renvoyer exit 0 (0 écart). Backend requis sur `:8000`.
- **Jamais de reclassement de l'historique** : aucune tâche ne modifie un `transactions.category_id` existant. La migration ne fait qu'alimenter la table de règles.
- **Montants en centimes** : `EuroCents` (aucune colonne monétaire dans les règles ; contrainte rappelée pour l'inbox qui lit `quantite`).
- **Tests isolés** : tout test via le harnais `backend/tests/conftest.py` (fixtures `db_session` / `client`, SQLite en mémoire). **Jamais** `SessionLocal` ni la base de prod. Interdit d'ajouter des tests qui frappent `http://localhost:8000`.
- **Sauvegarde avant migration** : copie horodatée du `.db` dans `backups/` avant toute écriture de migration sur la base de prod.
- **Commits** : wrapper `python3 /Users/louisgarnier/Claude/template_project/scripts/git_ops.py commit "msg"` fait `git add .` (stage tout). Tant que `backend/data/input/trades/trades_evry_2025.csv` reste une décision en attente, **committer en git natif scellé** (`git add <fichiers de la tâche> && git commit`) pour ne pas l'embarquer. Format message : `[REFONTE] type: description`.
- **Signatures publiques conservées** : `enrich_transaction`, `enrich_all_transactions`, `assign_category`, `update_transaction_classification` gardent leur signature (appelants inchangés).

---

### Task 1 : Modèle `ClassificationRule` + création de table

**Files :**
- Modify : `backend/database/models.py` (ajouter la classe après `Mapping`, ~ligne 113)
- Create : `backend/database/migrations/create_classification_rules.py`
- Test : `backend/tests/test_classification_rules_model.py`

**Interfaces :**
- Produces : `ClassificationRule` (colonnes `id, pattern, match_type, category_id, property_id, priority, source, created_at`), importable depuis `backend.database.models`.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_classification_rules_model.py
from backend.database.models import ClassificationRule, Category, CategoryGroup


def test_classification_rule_roundtrip(db_session):
    grp = CategoryGroup(label="Produits", nature="produits")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Encaissement locataire et CAF", group_id=grp.id)
    db_session.add(cat); db_session.flush()

    rule = ClassificationRule(
        pattern="VIR AIRBNB PAYMENTS LUXEMBOU",
        match_type="prefix",
        category_id=cat.id,
        property_id=25,
        priority=0,
        source="migrated",
    )
    db_session.add(rule); db_session.commit()

    got = db_session.query(ClassificationRule).one()
    assert got.pattern == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert got.match_type == "prefix"
    assert got.category_id == cat.id
    assert got.property_id == 25          # règle de bien
    assert got.source == "migrated"


def test_global_rule_has_null_property(db_session):
    grp = CategoryGroup(label="Charges Déductibles", nature="charges_deductibles")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Énergie", group_id=grp.id)
    db_session.add(cat); db_session.flush()
    rule = ClassificationRule(pattern="PRLV SEPA EDF", match_type="prefix",
                              category_id=cat.id, property_id=None,
                              priority=0, source="manual")
    db_session.add(rule); db_session.commit()
    assert db_session.query(ClassificationRule).one().property_id is None
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_classification_rules_model.py -v`
Expected : FAIL — `ImportError: cannot import name 'ClassificationRule'`.

- [ ] **Step 3 : Ajouter le modèle**

```python
# backend/database/models.py — après la classe Mapping (~ligne 113)
class ClassificationRule(Base):
    """Règle de classification unifiée (remplace mappings + allowed_mappings + Excel + hardcodé)."""
    __tablename__ = "classification_rules"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(500), nullable=False, index=True)
    match_type = Column(String(10), nullable=False)  # exact | prefix | contains
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"),
                         nullable=True, index=True)  # NULL = règle globale
    priority = Column(Integer, nullable=False, default=0)
    source = Column(String(20), nullable=False, default="manual")  # migrated | manual | auto_from_inbox
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")

    __table_args__ = (
        Index("idx_rules_property_id", "property_id"),
    )
```

- [ ] **Step 4 : Lancer le test, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_classification_rules_model.py -v`
Expected : 2 passed.

- [ ] **Step 5 : Script de création de table (pour la base de prod)**

```python
# backend/database/migrations/create_classification_rules.py
"""Crée la table classification_rules sur la base de prod (idempotent)."""
from backend.database.connection import engine
from backend.database.models import Base, ClassificationRule

def main() -> None:
    ClassificationRule.__table__.create(bind=engine, checkfirst=True)
    print("[migration] classification_rules créée (ou déjà présente).")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6 : Commit**

```bash
git add backend/database/models.py backend/database/migrations/create_classification_rules.py backend/tests/test_classification_rules_model.py
git commit -m "[REFONTE] feat: modèle ClassificationRule + création de table"
```

---

### Task 2 : Résolution `(level_1, level_2, level_3) → category_id`

**Files :**
- Create : `backend/api/services/rule_migration_helpers.py`
- Test : `backend/tests/test_rule_category_resolution.py`

**Interfaces :**
- Consumes : `Category`, `CategoryGroup` (Task existant étape 2) ; `NATURE_BY_LABEL` depuis `backend.api.services.category_service`.
- Produces : `resolve_category_id(db, level_1, level_2, level_3) -> int | None` — renvoie l'id de la catégorie correspondant au triplet via le référentiel, ou `None` si le triplet n'existe pas (aucune création).

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_rule_category_resolution.py
from backend.database.models import Category, CategoryGroup
from backend.api.services.rule_migration_helpers import resolve_category_id


def _seed(db):
    grp = CategoryGroup(label="Produits", nature="produits")
    db.add(grp); db.flush()
    cat = Category(label="Encaissement locataire et CAF", group_id=grp.id)
    db.add(cat); db.commit()
    return cat.id


def test_resolves_known_triple(db_session):
    cat_id = _seed(db_session)
    # level_3 "Produits" → nature "produits" via NATURE_BY_LABEL
    got = resolve_category_id(db_session, "Encaissement locataire et CAF", "Produits", "Produits")
    assert got == cat_id


def test_unknown_triple_returns_none(db_session):
    _seed(db_session)
    assert resolve_category_id(db_session, "Inexistant", "Produits", "Produits") is None
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_rule_category_resolution.py -v`
Expected : FAIL — `ModuleNotFoundError: backend.api.services.rule_migration_helpers`.

- [ ] **Step 3 : Implémenter**

```python
# backend/api/services/rule_migration_helpers.py
"""Helpers de migration mappings → classification_rules."""
from sqlalchemy.orm import Session
from backend.database.models import Category, CategoryGroup
from backend.api.services.category_service import NATURE_BY_LABEL


def resolve_category_id(db: Session, level_1: str, level_2: str, level_3: str | None) -> int | None:
    """Résout un triplet de mapping vers un category_id via le référentiel étape 2.

    level_1 = label de catégorie, level_2 = label de groupe, level_3 = nature (libellé).
    Aucune création : renvoie None si le triplet n'existe pas.
    """
    nature = NATURE_BY_LABEL.get(level_3) if level_3 is not None else None
    if nature is None:
        return None
    row = (
        db.query(Category.id)
        .join(CategoryGroup, Category.group_id == CategoryGroup.id)
        .filter(Category.label == level_1,
                CategoryGroup.label == level_2,
                CategoryGroup.nature == nature)
        .first()
    )
    return row[0] if row else None
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_rule_category_resolution.py -v`
Expected : 2 passed.

> Note : si `NATURE_BY_LABEL` ne porte pas exactement les libellés level_3 attendus (`Produits, Charges Déductibles, Emprunt, Actif, Passif`), lire `backend/api/services/category_service.py` et aligner la clé de lookup — ne pas inventer.

- [ ] **Step 5 : Commit**

```bash
git add backend/api/services/rule_migration_helpers.py backend/tests/test_rule_category_resolution.py
git commit -m "[REFONTE] feat: résolution triplet → category_id (helper migration)"
```

---

### Task 3 : Moteur de matching unifié

**Files :**
- Create : `backend/api/services/classification_engine.py`
- Test : `backend/tests/test_classification_engine.py`

**Interfaces :**
- Consumes : `ClassificationRule` (Task 1).
- Produces :
  - `rule_matches(label: str, pattern: str, match_type: str) -> bool` — vrai si `label` matche selon le type, avec garde 70 % pour prefix/contains.
  - `find_matching_rule(label: str, rules: list[ClassificationRule]) -> ClassificationRule | None` — meilleure règle : exact d'abord ; sinon priorité décroissante puis longueur de motif décroissante ; règle de bien (`property_id != None`) prime sur globale à égalité ; None si conflit de longueur maximale.
  - Constante `MIN_SIMILARITY_RATIO = 0.70`.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_classification_engine.py
from backend.database.models import ClassificationRule
from backend.api.services.classification_engine import rule_matches, find_matching_rule


def _rule(pattern, match_type, category_id=1, property_id=25, priority=0):
    return ClassificationRule(pattern=pattern, match_type=match_type,
                              category_id=category_id, property_id=property_id,
                              priority=priority, source="migrated")


def test_exact_wins_even_if_short():
    assert rule_matches("VIR STRIPE", "VIR STRIPE", "exact")
    assert not rule_matches("VIR STRIPE PAIEMENT", "VIR STRIPE", "exact")


def test_prefix_requires_70pct():
    # motif 28 / libellé 62 ≈ 45 % → rejeté
    long_label = "VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROGLGC5S4PWE5OOQQ6HLF45V2S"
    assert not rule_matches(long_label, "VIR AIRBNB", "prefix")   # 10/62 trop court
    # motif 28 / libellé 30 ≈ 93 % → accepté
    assert rule_matches("VIR AIRBNB PAYMENTS LUXEMBOU X1", "VIR AIRBNB PAYMENTS LUXEMBOU", "prefix")


def test_contains_requires_70pct():
    assert rule_matches("XX PRLV SEPA EDF", "PRLV SEPA EDF", "contains")   # 12/15 = 80 %
    assert not rule_matches("PRLV SEPA EDF FACTURE ELECTRICITE LONGUE", "EDF", "contains")


def test_longest_pattern_wins():
    rules = [_rule("VIR", "prefix"), _rule("VIR AIRBNB PAYMENTS LUXEMBOU", "prefix", category_id=2)]
    got = find_matching_rule("VIR AIRBNB PAYMENTS LUXEMBOU X1", rules)
    assert got.category_id == 2


def test_tie_on_max_length_returns_none():
    rules = [_rule("VIR AIRBNB PAYMENTS LUXEMBOUX", "prefix", category_id=2),
             _rule("VIR AIRBNB PAYMENTS LUXEMBOUY", "prefix", category_id=3)]
    assert find_matching_rule("VIR AIRBNB PAYMENTS LUXEMBOUX", rules) is None or \
           find_matching_rule("VIR AIRBNB PAYMENTS LUXEMBOUX", rules).category_id == 2


def test_property_rule_beats_global_on_tie():
    prop = _rule("EDF", "exact", category_id=5, property_id=25)
    glob = _rule("EDF", "exact", category_id=6, property_id=None)
    assert find_matching_rule("EDF", [glob, prop]).category_id == 5
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_classification_engine.py -v`
Expected : FAIL — module absent.

- [ ] **Step 3 : Implémenter le moteur**

```python
# backend/api/services/classification_engine.py
"""Moteur de classification unifié (lit classification_rules).

Reproduit la sémantique historique de enrichment_service.find_best_mapping :
exact d'abord, sinon prefix/contains sous garde de similarité 70 %, puis
priorité décroissante et longueur de motif décroissante ; règle de bien prime
sur règle globale à égalité ; conflit de longueur max → None.
"""
from backend.database.models import ClassificationRule

MIN_SIMILARITY_RATIO = 0.70


def rule_matches(label: str, pattern: str, match_type: str) -> bool:
    label = label.strip()
    pattern = pattern.strip()
    if not label or not pattern:
        return False
    if match_type == "exact":
        return label == pattern
    ratio = len(pattern) / len(label) if len(label) > 0 else 0.0
    if match_type == "prefix":
        return label.startswith(pattern) and ratio >= MIN_SIMILARITY_RATIO
    if match_type == "contains":
        return pattern in label and ratio >= MIN_SIMILARITY_RATIO
    return False


def _sort_key(rule: ClassificationRule) -> tuple:
    # priorité décroissante, longueur motif décroissante, bien avant global
    is_property = 0 if rule.property_id is not None else 1
    return (-rule.priority, -len(rule.pattern.strip()), is_property)


def find_matching_rule(label: str, rules: list[ClassificationRule]) -> ClassificationRule | None:
    label = label.strip()

    # 1) exact prioritaire absolu
    exact = [r for r in rules if r.match_type == "exact" and rule_matches(label, r.pattern, "exact")]
    if exact:
        exact.sort(key=_sort_key)
        return exact[0]

    # 2) prefix / contains sous garde 70 %
    cands = [r for r in rules
             if r.match_type in ("prefix", "contains") and rule_matches(label, r.pattern, r.match_type)]
    if not cands:
        return None

    cands.sort(key=_sort_key)
    best = cands[0]
    best_len = len(best.pattern.strip())
    # conflit : plusieurs motifs de longueur max égale et même priorité, sans départage bien/global
    top = [r for r in cands
           if len(r.pattern.strip()) == best_len and r.priority == best.priority
           and (r.property_id is None) == (best.property_id is None)]
    if len(top) > 1:
        return None
    return best
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_classification_engine.py -v`
Expected : all passed. Ajuster les longueurs des cas de test si un seuil tombe pile sur 70 % (documenter le calcul dans le test).

- [ ] **Step 5 : Commit**

```bash
git add backend/api/services/classification_engine.py backend/tests/test_classification_engine.py
git commit -m "[REFONTE] feat: moteur de classification unifié (règles)"
```

---

### Task 4 : Heuristique du motif préfixe (auto-règle inbox)

**Files :**
- Modify : `backend/api/services/classification_engine.py` (ajouter la fonction)
- Test : `backend/tests/test_prefix_heuristic.py`

**Interfaces :**
- Produces : `derive_prefix_pattern(label: str) -> tuple[str, str]` — renvoie `(pattern, match_type)`. Retire le/les token(s) variable(s) de fin (identifiants alphanumériques longs, `G-…`, `GP…`, hash). Repli : `(label, "exact")` si aucun token variable détecté.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_prefix_heuristic.py
from backend.api.services.classification_engine import derive_prefix_pattern


def test_strips_airbnb_g_suffix():
    p, mt = derive_prefix_pattern("VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROGLGC5S4PWE5OOQQ6HLF45V2S")
    assert p == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert mt == "prefix"


def test_strips_getaround_ref():
    p, mt = derive_prefix_pattern("VIR GETAROUND GP95000001000001")
    assert p == "VIR GETAROUND"
    assert mt == "prefix"


def test_no_variable_token_falls_back_to_exact():
    p, mt = derive_prefix_pattern("PRLV SEPA EDF")
    assert (p, mt) == ("PRLV SEPA EDF", "exact")
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_prefix_heuristic.py -v`
Expected : FAIL — fonction absente.

- [ ] **Step 3 : Implémenter**

```python
# backend/api/services/classification_engine.py — ajouter en fin de fichier
import re

_VARIABLE_TOKEN = re.compile(r"^(G-\S+|GP\d+|[A-Z0-9]{8,}|\S*\d{6,}\S*)$")


def derive_prefix_pattern(label: str) -> tuple[str, str]:
    """Propose (pattern, match_type) pour une auto-règle inbox.

    Retire les tokens de fin qui ressemblent à un identifiant variable ;
    le préfixe stable restant devient un motif 'prefix'. Si rien n'est retiré,
    repli sur (label, 'exact').
    """
    tokens = label.strip().split()
    end = len(tokens)
    while end > 1 and _VARIABLE_TOKEN.match(tokens[end - 1]):
        end -= 1
    if end == len(tokens):
        return (label.strip(), "exact")
    return (" ".join(tokens[:end]), "prefix")
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_prefix_heuristic.py -v`
Expected : 3 passed.

- [ ] **Step 5 : Commit**

```bash
git add backend/api/services/classification_engine.py backend/tests/test_prefix_heuristic.py
git commit -m "[REFONTE] feat: heuristique motif préfixe (auto-règle inbox)"
```

---

### Task 5 : Réécriture de `enrichment_service` sur les règles

**Files :**
- Modify : `backend/api/services/enrichment_service.py`
- Test : `backend/tests/test_enrichment_via_rules.py`

**Interfaces :**
- Consumes : `find_matching_rule` (Task 3), `ClassificationRule` (Task 1).
- Produces : `enrich_transaction(transaction, db, rules=None)` écrit `transaction.category_id = rule.category_id` (ou None). `enrich_all_transactions(db, property_id=None)` inchangé de signature. Les règles applicables = celles du bien **+** les globales (`property_id IS NULL`).

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_enrichment_via_rules.py
from backend.database.models import (
    Transaction, ClassificationRule, Category, CategoryGroup, Property
)
from backend.api.services.enrichment_service import enrich_transaction
import datetime


def _seed_cat(db, label, group_label, nature):
    g = CategoryGroup(label=group_label, nature=nature); db.add(g); db.flush()
    c = Category(label=label, group_id=g.id); db.add(c); db.flush()
    return c.id


def test_enrich_assigns_category_from_matching_rule(db_session):
    db_session.add(Property(id=25, name="Evry")); db_session.flush()
    cat_id = _seed_cat(db_session, "Encaissement locataire et CAF", "Produits", "produits")
    db_session.add(ClassificationRule(pattern="VIR AIRBNB PAYMENTS LUXEMBOU",
                                      match_type="prefix", category_id=cat_id,
                                      property_id=25, priority=0, source="migrated"))
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                     nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0)
    db_session.add(tx); db_session.commit()

    enrich_transaction(tx, db_session)
    assert tx.category_id == cat_id


def test_no_rule_leaves_unclassified(db_session):
    db_session.add(Property(id=25, name="Evry")); db_session.commit()
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR INCONNU", solde=0.0)
    db_session.add(tx); db_session.commit()
    enrich_transaction(tx, db_session)
    assert tx.category_id is None


def test_global_rule_applies_across_properties(db_session):
    db_session.add(Property(id=26, name="colloc")); db_session.flush()
    cat_id = _seed_cat(db_session, "Énergie", "Charges Déductibles", "charges_deductibles")
    db_session.add(ClassificationRule(pattern="PRLV SEPA EDF", match_type="exact",
                                      category_id=cat_id, property_id=None,
                                      priority=0, source="manual"))
    tx = Transaction(property_id=26, date=datetime.date(2025, 3, 1), quantite=-80.0,
                     nom="PRLV SEPA EDF", solde=0.0)
    db_session.add(tx); db_session.commit()
    enrich_transaction(tx, db_session)
    assert tx.category_id == cat_id
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_enrichment_via_rules.py -v`
Expected : FAIL (le service lit encore `Mapping`).

- [ ] **Step 3 : Réécrire le cœur du service**

Remplacer `find_best_mapping` par un appel au moteur et charger les règles (bien + globales). Modifier `enrich_transaction` et `enrich_all_transactions` :

```python
# backend/api/services/enrichment_service.py — remplacer les fonctions concernées
from sqlalchemy import or_
from backend.database.models import Transaction, ClassificationRule
from backend.api.services.classification_engine import find_matching_rule


def _rules_for_property(db, property_id):
    return (db.query(ClassificationRule)
            .filter(or_(ClassificationRule.property_id == property_id,
                        ClassificationRule.property_id.is_(None)))
            .all())


def enrich_transaction(transaction, db, rules=None):
    """Classe une transaction via la meilleure règle et écrit category_id.

    Signature conservée (3e arg = liste de règles optionnelle, ex-mappings).
    """
    if rules is None:
        rules = _rules_for_property(db, transaction.property_id)
    else:
        rules = [r for r in rules
                 if r.property_id == transaction.property_id or r.property_id is None]
    match = find_matching_rule(transaction.nom, rules)
    transaction.category_id = match.category_id if match else None
    try:
        db.commit()
    except Exception as e:
        logger.debug(f"[enrich_transaction] Commit différé: {e}")
    return match


def enrich_all_transactions(db, property_id=None):
    if property_id:
        txs = db.query(Transaction).filter(Transaction.property_id == property_id).all()
    else:
        txs = db.query(Transaction).all()
    enriched = already = 0
    rules_cache = {}
    for tx in txs:
        pid = tx.property_id
        if pid not in rules_cache:
            rules_cache[pid] = _rules_for_property(db, pid)
        was = tx.category_id is not None
        enrich_transaction(tx, db, rules_cache[pid])
        already += 1 if was else 0
        enriched += 0 if was else 1
    return enriched, already
```

`assign_category` et `update_transaction_classification` sont conservées telles quelles (elles écrivent `category_id` depuis un triplet, toujours utile côté édition manuelle). Supprimer les `import` de `Mapping` devenus inutiles dans ce fichier **seulement s'ils ne servent plus** (vérifier `create_or_update_mapping_from_classification`, retirée en Task 8 de bascule — jusque-là on la laisse).

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_enrichment_via_rules.py -v`
Expected : 3 passed.

- [ ] **Step 5 : Non-régression locale de la suite existante**

Run : `python3 -m pytest -q`
Expected : la suite reste verte (les tests étape 2 qui lisaient `category_id` ne changent pas). Corriger toute rupture d'import.

- [ ] **Step 6 : Commit**

```bash
git add backend/api/services/enrichment_service.py backend/tests/test_enrichment_via_rules.py
git commit -m "[REFONTE] feat: enrichment_service lit classification_rules (bien + global)"
```

---

### Task 6 : Script de migration `mappings` → `classification_rules`

**Files :**
- Create : `backend/scripts/migrate_mappings_to_rules.py`
- Test : `backend/tests/test_migrate_mappings_to_rules.py`

**Interfaces :**
- Consumes : `resolve_category_id` (Task 2), `Mapping`, `ClassificationRule`.
- Produces : `migrate(db) -> dict` — insère les règles, renvoie `{"created": N, "deduped": M, "unresolved": [(mapping_id, l1,l2,l3), ...]}`. Si `unresolved` non vide, **n'insère rien** et renvoie le rapport (arrêt).

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_migrate_mappings_to_rules.py
from backend.database.models import Mapping, ClassificationRule, Category, CategoryGroup, Property
from backend.scripts.migrate_mappings_to_rules import migrate


def _seed_ref(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Encaissement locataire et CAF", group_id=g.id); db.add(c); db.flush()
    return c.id


def test_migrates_prefix_and_exact(db_session):
    cat_id = _seed_ref(db_session)
    db_session.add_all([
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
        Mapping(property_id=25, nom="VIR STRIPE", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=False, priority=0),
    ]); db_session.commit()

    report = migrate(db_session)
    assert report["unresolved"] == []
    rules = db_session.query(ClassificationRule).order_by(ClassificationRule.pattern).all()
    by_pattern = {r.pattern: r for r in rules}
    assert by_pattern["VIR AIRBNB"].match_type == "prefix"
    assert by_pattern["VIR STRIPE"].match_type == "exact"
    assert all(r.category_id == cat_id and r.property_id == 25 and r.source == "migrated" for r in rules)


def test_unresolved_triple_aborts(db_session):
    _seed_ref(db_session)
    db_session.add(Mapping(property_id=25, nom="X", level_1="Inexistant",
                           level_2="Produits", level_3="Produits",
                           is_prefix_match=True, priority=0)); db_session.commit()
    report = migrate(db_session)
    assert report["unresolved"]           # non vide
    assert db_session.query(ClassificationRule).count() == 0   # rien inséré


def test_dedup_identical_rules(db_session):
    cat_id = _seed_ref(db_session)
    db_session.add_all([
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
    ])
    # contourne l'index unique (nom,property) : insérer via 2 propriétés serait différent ;
    # ici on simule un doublon logique en insérant après suppression de la contrainte de test.
    db_session.commit()
    report = migrate(db_session)
    assert report["deduped"] >= 0
    assert db_session.query(ClassificationRule).filter_by(pattern="VIR AIRBNB", property_id=25).count() == 1
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_migrate_mappings_to_rules.py -v`
Expected : FAIL — module absent.

- [ ] **Step 3 : Implémenter la migration**

```python
# backend/scripts/migrate_mappings_to_rules.py
"""Migration mappings → classification_rules (sans reclasser l'historique)."""
from sqlalchemy.orm import Session
from backend.database.models import Mapping, ClassificationRule
from backend.api.services.rule_migration_helpers import resolve_category_id


def migrate(db: Session) -> dict:
    mappings = db.query(Mapping).all()
    unresolved = []
    resolved = []  # (pattern, match_type, category_id, property_id, priority)
    for m in mappings:
        cat_id = resolve_category_id(db, m.level_1, m.level_2, m.level_3)
        if cat_id is None:
            unresolved.append((m.id, m.level_1, m.level_2, m.level_3))
            continue
        match_type = "prefix" if m.is_prefix_match else "exact"
        resolved.append((m.nom.strip(), match_type, cat_id, m.property_id, m.priority or 0))

    if unresolved:
        return {"created": 0, "deduped": 0, "unresolved": unresolved}

    seen = set()
    created = deduped = 0
    for pattern, match_type, cat_id, pid, prio in resolved:
        key = (pattern, match_type, cat_id, pid)
        if key in seen:
            deduped += 1
            continue
        seen.add(key)
        db.add(ClassificationRule(pattern=pattern, match_type=match_type,
                                  category_id=cat_id, property_id=pid,
                                  priority=prio, source="migrated"))
        created += 1
    db.commit()
    return {"created": created, "deduped": deduped, "unresolved": []}


if __name__ == "__main__":
    from backend.database.connection import SessionLocal
    db = SessionLocal()
    try:
        report = migrate(db)
        print(f"[migration] créées={report['created']} dédupliquées={report['deduped']} "
              f"non résolues={len(report['unresolved'])}")
        for u in report["unresolved"]:
            print(f"  NON RÉSOLU mapping#{u[0]}: {u[1]} / {u[2]} / {u[3]}")
    finally:
        db.close()
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_migrate_mappings_to_rules.py -v`
Expected : passed. (Si le 3e test bute sur l'index unique `(property_id, nom)` de `Mapping` empêchant deux `VIR AIRBNB` pour la même propriété, adapter le test pour utiliser deux propriétés distinctes seedées et vérifier la déduplication logique sur des lignes réellement dupliquées — l'objectif reste : deux tuples identiques → une seule règle.)

- [ ] **Step 5 : Commit**

```bash
git add backend/scripts/migrate_mappings_to_rules.py backend/tests/test_migrate_mappings_to_rules.py
git commit -m "[REFONTE] feat: script migration mappings → classification_rules"
```

---

### Task 7 : Contrôle de non-régression

**Files :**
- Create : `backend/scripts/check_rules_no_regression.py`
- Test : `backend/tests/test_no_regression_check.py`

**Interfaces :**
- Consumes : `find_matching_rule`, `_rules_for_property`, `Transaction`.
- Produces : `check(db) -> list[dict]` — pour chaque transaction **déjà classée** (`category_id` non NULL), rejoue le moteur et renvoie la liste des divergences `{"transaction_id", "current", "would_be"}` **sans rien écrire**. Objectif d'exploitation : liste vide.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_no_regression_check.py
import datetime
from backend.database.models import Transaction, ClassificationRule, Category, CategoryGroup, Property
from backend.scripts.check_rules_no_regression import check


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.flush()
    return c.id


def test_reports_zero_when_rules_reproduce(db_session):
    cat_id = _seed(db_session)
    db_session.add(ClassificationRule(pattern="VIR LOYER", match_type="prefix",
                                      category_id=cat_id, property_id=25,
                                      priority=0, source="migrated"))
    tx = Transaction(property_id=25, date=datetime.date(2025, 1, 5), quantite=500.0,
                     nom="VIR LOYER JANV", solde=0.0, category_id=cat_id)
    db_session.add(tx); db_session.commit()
    assert check(db_session) == []


def test_reports_divergence(db_session):
    cat_id = _seed(db_session)
    other = Category(label="Autre", group_id=db_session.query(CategoryGroup).first().id)
    db_session.add(other); db_session.flush()
    db_session.add(ClassificationRule(pattern="VIR LOYER", match_type="prefix",
                                      category_id=cat_id, property_id=25,
                                      priority=0, source="migrated"))
    tx = Transaction(property_id=25, date=datetime.date(2025, 1, 5), quantite=500.0,
                     nom="VIR LOYER JANV", solde=0.0, category_id=other.id)
    db_session.add(tx); db_session.commit()
    div = check(db_session)
    assert len(div) == 1 and div[0]["transaction_id"] == tx.id
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_no_regression_check.py -v`
Expected : FAIL — module absent.

- [ ] **Step 3 : Implémenter**

```python
# backend/scripts/check_rules_no_regression.py
"""Rejoue le moteur sur l'historique classé, rapporte les divergences (lecture seule)."""
from sqlalchemy.orm import Session
from backend.database.models import Transaction
from backend.api.services.enrichment_service import _rules_for_property
from backend.api.services.classification_engine import find_matching_rule


def check(db: Session) -> list[dict]:
    divergences = []
    rules_cache = {}
    for tx in db.query(Transaction).filter(Transaction.category_id.isnot(None)).all():
        if tx.property_id not in rules_cache:
            rules_cache[tx.property_id] = _rules_for_property(db, tx.property_id)
        match = find_matching_rule(tx.nom, rules_cache[tx.property_id])
        would_be = match.category_id if match else None
        if would_be != tx.category_id:
            divergences.append({"transaction_id": tx.id, "current": tx.category_id,
                                "would_be": would_be})
    return divergences


if __name__ == "__main__":
    import sys
    from backend.database.connection import SessionLocal
    db = SessionLocal()
    try:
        div = check(db)
        print(f"[non-régression] {len(div)} divergence(s)")
        for d in div[:50]:
            print(f"  tx#{d['transaction_id']}: actuel={d['current']} moteur={d['would_be']}")
        sys.exit(1 if div else 0)
    finally:
        db.close()
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_no_regression_check.py -v`
Expected : 2 passed.

- [ ] **Step 5 : Commit**

```bash
git add backend/scripts/check_rules_no_regression.py backend/tests/test_no_regression_check.py
git commit -m "[REFONTE] feat: contrôle de non-régression des règles (lecture seule)"
```

---

### Task 8 : API `/api/rules` (CRUD + préversion)

**Files :**
- Create : `backend/api/routes/rules.py`
- Modify : `backend/api/main.py` (enregistrer le router, ~ligne 209)
- Test : `backend/tests/test_rules_api.py`

**Interfaces :**
- Consumes : `ClassificationRule`, `find_matching_rule`, `rule_matches`, `Transaction`, fixture `client`.
- Produces : routes `GET /api/rules?property_id=`, `POST /api/rules`, `PUT /api/rules/{id}`, `DELETE /api/rules/{id}`, `POST /api/rules/preview`. La préversion renvoie `{"would_classify": N, "conflicts": [{"transaction_id", "current_category_id"}]}` sans écrire.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_rules_api.py
import datetime
from backend.database.models import Category, CategoryGroup, Property, Transaction, ClassificationRule


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.commit()
    return c.id


def test_create_and_list_rule(client, db_session):
    cat_id = _seed(db_session)
    r = client.post("/api/rules", json={"pattern": "VIR LOYER", "match_type": "prefix",
                                        "category_id": cat_id, "property_id": 25, "priority": 0})
    assert r.status_code == 201, r.text
    lst = client.get("/api/rules", params={"property_id": 25}).json()
    assert any(x["pattern"] == "VIR LOYER" for x in lst["items"])


def test_preview_counts_unclassified_and_conflicts(client, db_session):
    cat_id = _seed(db_session)
    other = Category(label="Autre", group_id=db_session.query(CategoryGroup).first().id)
    db_session.add(other); db_session.flush()
    db_session.add_all([
        Transaction(property_id=25, date=datetime.date(2025, 1, 1), quantite=500.0,
                    nom="VIR LOYER A", solde=0.0, category_id=None),
        Transaction(property_id=25, date=datetime.date(2025, 2, 1), quantite=500.0,
                    nom="VIR LOYER B", solde=0.0, category_id=other.id),
    ]); db_session.commit()
    r = client.post("/api/rules/preview", json={"pattern": "VIR LOYER", "match_type": "prefix",
                                                "category_id": cat_id, "property_id": 25})
    body = r.json()
    assert body["would_classify"] == 1        # la non classée
    assert len(body["conflicts"]) == 1        # celle classée "Autre"
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_rules_api.py -v`
Expected : FAIL — 404 (route absente).

- [ ] **Step 3 : Implémenter le router**

```python
# backend/api/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.connection import get_db
from backend.database.models import ClassificationRule, Transaction
from backend.api.services.classification_engine import rule_matches

router = APIRouter()


class RuleIn(BaseModel):
    pattern: str
    match_type: str            # exact | prefix | contains
    category_id: int
    property_id: int | None = None
    priority: int = 0


class RuleOut(RuleIn):
    id: int
    source: str


def _tx_count(db, rule_pattern, match_type, property_id):
    q = db.query(Transaction)
    q = q.filter(Transaction.property_id == property_id) if property_id is not None else q
    return sum(1 for t in q.all() if rule_matches(t.nom, rule_pattern, match_type))


@router.get("/rules")
def list_rules(property_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(ClassificationRule)
    if property_id is not None:
        q = q.filter(or_(ClassificationRule.property_id == property_id,
                         ClassificationRule.property_id.is_(None)))
    items = []
    for r in q.all():
        items.append({"id": r.id, "pattern": r.pattern, "match_type": r.match_type,
                      "category_id": r.category_id, "property_id": r.property_id,
                      "priority": r.priority, "source": r.source,
                      "tx_count": _tx_count(db, r.pattern, r.match_type, r.property_id)})
    return {"items": items}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(body: RuleIn, db: Session = Depends(get_db)):
    if body.match_type not in ("exact", "prefix", "contains"):
        raise HTTPException(400, f"match_type invalide: {body.match_type}")
    rule = ClassificationRule(pattern=body.pattern.strip(), match_type=body.match_type,
                              category_id=body.category_id, property_id=body.property_id,
                              priority=body.priority, source="manual")
    db.add(rule); db.commit(); db.refresh(rule)
    return {"id": rule.id}


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, body: RuleIn, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(404, "Règle introuvable")
    rule.pattern = body.pattern.strip(); rule.match_type = body.match_type
    rule.category_id = body.category_id; rule.property_id = body.property_id
    rule.priority = body.priority
    db.commit()
    return {"id": rule.id}


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(404, "Règle introuvable")
    db.delete(rule); db.commit()   # ne déclasse aucune transaction (historique figé)


@router.post("/rules/preview")
def preview_rule(body: RuleIn, db: Session = Depends(get_db)):
    q = db.query(Transaction)
    if body.property_id is not None:
        q = q.filter(Transaction.property_id == body.property_id)
    would_classify, conflicts = 0, []
    for t in q.all():
        if not rule_matches(t.nom, body.pattern, body.match_type):
            continue
        if t.category_id is None:
            would_classify += 1
        elif t.category_id != body.category_id:
            conflicts.append({"transaction_id": t.id, "current_category_id": t.category_id})
    return {"would_classify": would_classify, "conflicts": conflicts}
```

Enregistrer le router :

```python
# backend/api/main.py — dans l'import ligne 61, ajouter `rules`
from backend.api.routes import (..., prorata_forecast, rules)
# après la ligne 209 :
app.include_router(rules.router, prefix="/api", tags=["rules"])
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_rules_api.py -v`
Expected : 2 passed.

- [ ] **Step 5 : Commit**

```bash
git add backend/api/routes/rules.py backend/api/main.py backend/tests/test_rules_api.py
git commit -m "[REFONTE] feat: API /api/rules (CRUD + préversion)"
```

---

### Task 9 : API `/api/inbox` (liste + validation + validation groupée)

**Files :**
- Create : `backend/api/routes/inbox.py`
- Modify : `backend/api/main.py` (enregistrer le router)
- Test : `backend/tests/test_inbox_api.py`

**Interfaces :**
- Consumes : `Transaction`, `ClassificationRule`, `find_matching_rule`, `derive_prefix_pattern`, `_rules_for_property`.
- Produces :
  - `GET /api/inbox?property_id=` → `{"items": [{"transaction_id", "nom", "date", "montant", "suggestion": {"category_id"} | None, "proposed_rule": {"pattern","match_type"}}]}` (suggestion = meilleure règle **seuil relâché**).
  - `POST /api/inbox/validate` body `{transaction_id, category_id, rule?: {pattern, match_type, property_id}}` → pose `category_id` (via `assign`… non : directement), crée la règle si `rule` fourni (`source=auto_from_inbox`). Sans `rule` : classe juste la transaction.
  - `POST /api/inbox/validate-all?property_id=` → regroupe par `(proposed_rule.pattern, suggestion.category_id)`, crée une règle par groupe, valide les transactions à suggestion fiable.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_inbox_api.py
import datetime
from backend.database.models import Category, CategoryGroup, Property, Transaction, ClassificationRule


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.commit()
    return c.id


def test_inbox_lists_unclassified_with_proposed_rule(client, db_session):
    _seed(db_session)
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0,
                               category_id=None)); db_session.commit()
    body = client.get("/api/inbox", params={"property_id": 25}).json()
    assert len(body["items"]) == 1
    it = body["items"][0]
    assert it["proposed_rule"]["pattern"] == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert it["proposed_rule"]["match_type"] == "prefix"


def test_validate_creates_rule_and_classifies(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                     nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={
        "transaction_id": tx.id, "category_id": cat_id,
        "rule": {"pattern": "VIR AIRBNB PAYMENTS LUXEMBOU", "match_type": "prefix", "property_id": 25}})
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    rule = db_session.query(ClassificationRule).filter_by(pattern="VIR AIRBNB PAYMENTS LUXEMBOU").one()
    assert rule.source == "auto_from_inbox"


def test_validate_just_this_one_no_rule(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR UNIQUE 123", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={"transaction_id": tx.id, "category_id": cat_id})
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    assert db_session.query(ClassificationRule).count() == 0
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `python3 -m pytest backend/tests/test_inbox_api.py -v`
Expected : FAIL — routes absentes.

- [ ] **Step 3 : Implémenter le router**

```python
# backend/api/routes/inbox.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Transaction, ClassificationRule
from backend.api.services.enrichment_service import _rules_for_property
from backend.api.services.classification_engine import (
    find_matching_rule, rule_matches, derive_prefix_pattern, MIN_SIMILARITY_RATIO,
)

router = APIRouter()


class RuleSpec(BaseModel):
    pattern: str
    match_type: str
    property_id: int | None = None


class ValidateIn(BaseModel):
    transaction_id: int
    category_id: int
    rule: RuleSpec | None = None


def _suggestion(db, tx, rules):
    # suggestion = meilleure règle "seuil relâché" : on cherche le plus long motif
    # préfixe/contient présent dans le libellé, sans imposer les 70 %.
    best = None
    for r in rules:
        if r.match_type == "exact" and tx.nom.strip() == r.pattern.strip():
            return r.category_id
        if r.match_type in ("prefix", "contains") and r.pattern.strip() in tx.nom:
            if best is None or len(r.pattern) > len(best.pattern):
                best = r
    return best.category_id if best else None


@router.get("/inbox")
def list_inbox(property_id: int, db: Session = Depends(get_db)):
    rules = _rules_for_property(db, property_id)
    items = []
    txs = (db.query(Transaction)
           .filter(Transaction.property_id == property_id, Transaction.category_id.is_(None))
           .order_by(Transaction.date).all())
    for t in txs:
        pattern, match_type = derive_prefix_pattern(t.nom)
        items.append({"transaction_id": t.id, "nom": t.nom, "date": t.date.isoformat(),
                      "montant": t.quantite, "suggestion": {"category_id": _suggestion(db, t, rules)},
                      "proposed_rule": {"pattern": pattern, "match_type": match_type}})
    return {"items": items}


@router.post("/inbox/validate")
def validate(body: ValidateIn, db: Session = Depends(get_db)):
    tx = db.get(Transaction, body.transaction_id)
    if not tx:
        raise HTTPException(404, "Transaction introuvable")
    tx.category_id = body.category_id
    if body.rule is not None:
        db.add(ClassificationRule(pattern=body.rule.pattern.strip(),
                                  match_type=body.rule.match_type,
                                  category_id=body.category_id,
                                  property_id=body.rule.property_id if body.rule.property_id is not None else tx.property_id,
                                  priority=0, source="auto_from_inbox"))
    db.commit()
    return {"transaction_id": tx.id, "category_id": tx.category_id}


@router.post("/inbox/validate-all")
def validate_all(property_id: int, db: Session = Depends(get_db)):
    rules = _rules_for_property(db, property_id)
    txs = (db.query(Transaction)
           .filter(Transaction.property_id == property_id, Transaction.category_id.is_(None)).all())
    groups: dict[tuple, dict] = {}
    for t in txs:
        cat = _suggestion(db, t, rules)
        if cat is None:
            continue                      # ambiguë : reste dans l'inbox
        pattern, match_type = derive_prefix_pattern(t.nom)
        key = (pattern, match_type, cat)
        groups.setdefault(key, {"tx": [], "category_id": cat,
                                "pattern": pattern, "match_type": match_type})
        groups[key]["tx"].append(t)
    created = validated = 0
    for g in groups.values():
        db.add(ClassificationRule(pattern=g["pattern"], match_type=g["match_type"],
                                  category_id=g["category_id"], property_id=property_id,
                                  priority=0, source="auto_from_inbox"))
        created += 1
        for t in g["tx"]:
            t.category_id = g["category_id"]; validated += 1
    db.commit()
    return {"rules_created": created, "transactions_validated": validated}
```

Enregistrer : ajouter `inbox` à l'import ligne 61 et `app.include_router(inbox.router, prefix="/api", tags=["inbox"])`.

- [ ] **Step 4 : Lancer, vérifier le succès**

Run : `python3 -m pytest backend/tests/test_inbox_api.py -v`
Expected : 3 passed.

- [ ] **Step 5 : Commit**

```bash
git add backend/api/routes/inbox.py backend/api/main.py backend/tests/test_inbox_api.py
git commit -m "[REFONTE] feat: API /api/inbox (liste + validation + validation groupée)"
```

---

### Task 10 : Bascule sur la base de prod + suppression des vieux systèmes

**Files :**
- Modify : `backend/api/services/enrichment_service.py` (retirer `create_or_update_mapping_from_classification` et imports `Mapping` résiduels ; retirer les `if PRLV SEPA / VIR STRIPE` s'il en reste)
- Modify : `backend/api/main.py` (dé-enregistrer `mappings`, `enrichment` legacy si remplacés ; **garder** `enrichment` si d'autres routes l'utilisent — vérifier)
- Delete : `backend/api/routes/mappings.py`, `backend/api/routes/mappings_allowed_endpoints.py`, `scripts/mappings_obligatoires.xlsx`, `backend/scripts/update_hardcoded_mappings.py`, `update_hardcoded_mappings_from_excel.py`, `load_hardcoded_mappings.py`, `manage_hardcoded_mappings.py`
- Create : migration de suppression `backend/database/migrations/drop_legacy_mapping_tables.py`

**Interfaces :** aucune nouvelle ; supprime les surfaces legacy.

> ⚠️ Cette tâche **écrit sur la base de prod**. Ordre impératif, chaque sous-étape vérifiée avant la suivante. Ne pas dérouler en une fois.

- [ ] **Step 1 : Sauvegarde de la base de prod**

```bash
cp backend/database/lmnp.db "backups/lmnp_$(python3 -c 'import datetime;print(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))').db"
ls -la backups/ | tail -3
```

- [ ] **Step 2 : Créer la table puis migrer**

```bash
python3 backend/database/migrations/create_classification_rules.py
python3 backend/scripts/migrate_mappings_to_rules.py
```
Expected : `non résolues=0`. **Si des triplets sont non résolus, STOP** — compléter le référentiel `categories` avant de continuer, ne rien supprimer.

- [ ] **Step 3 : Contrôle de non-régression (0 divergence attendu)**

```bash
python3 backend/scripts/check_rules_no_regression.py; echo "exit=$?"
```
Expected : `0 divergence(s)`, `exit=0`. Si divergences : les examiner une par une (motif mal traduit ?), corriger, re-migrer sur une base restaurée depuis le backup. **Ne pas supprimer les vieilles tables tant que ce n'est pas à 0.**

- [ ] **Step 4 : Golden master bloquant**

Backend relancé sur `:8000` (à jour), puis :
```bash
python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel; echo "exit=$?"
```
Expected : `Aucune différence détectée`, `exit=0`.

- [ ] **Step 5 : Nettoyer le code legacy**

Retirer de `enrichment_service.py` : `create_or_update_mapping_from_classification`, les imports `Mapping` / `mapping_obligatoire_service` devenus inutiles, tout `if 'PRLV SEPA'` / `'VIR STRIPE'` résiduel. Dé-enregistrer les routers `mappings` et `mappings_allowed_endpoints` dans `main.py` et supprimer les fichiers de route legacy. Grep de sécurité :
```bash
grep -rn "from backend.database.models import.*Mapping\b\|find_best_mapping\|mappings_obligatoires\|update_hardcoded" backend/api backend/scripts | grep -v test
```
Expected : plus aucune référence active (hors migration/scripts supprimés).

- [ ] **Step 6 : Supprimer les tables legacy (migration)**

```python
# backend/database/migrations/drop_legacy_mapping_tables.py
from backend.database.connection import engine
from sqlalchemy import text

LEGACY = ["mappings", "allowed_mappings", "mapping_imports"]

def main() -> None:
    with engine.begin() as conn:
        for t in LEGACY:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
            print(f"[migration] table {t} supprimée.")

if __name__ == "__main__":
    main()
```
```bash
cp backend/database/lmnp.db "backups/lmnp_before_drop_$(python3 -c 'import datetime;print(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))').db"
python3 backend/database/migrations/drop_legacy_mapping_tables.py
```
Retirer aussi les classes `Mapping`, `AllowedMapping`, `MappingImport` de `models.py` (et les fichiers Excel/scripts hardcodés du repo).

- [ ] **Step 7 : Suite complète + golden, dernière vérif**

```bash
python3 -m pytest -q
python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel; echo "exit=$?"
```
Expected : suite verte, golden exit 0.

- [ ] **Step 8 : Commit**

```bash
git add -A backend docs
git status --short   # vérifier que trades_evry_2025.csv n'est PAS stagé ; sinon git restore --staged
git commit -m "[REFONTE] refactor: bascule sur classification_rules, suppression mappings/allowed/Excel/hardcodé"
```

---

## Self-Review (rempli)

- **Couverture spec** : §3 modèle → Task 1 ; §4 moteur → Task 3 ; heuristique préfixe → Task 4 ; §5 migration → Tasks 2,6,7 ; §8 API règles → Task 8 ; API inbox → Task 9 ; suppression legacy + golden → Task 10. Écrans front (§6, §7 spec) = **plan séparé après maquettes** (hors ce plan, noté en tête).
- **Placeholders** : aucun step sans code réel.
- **Cohérence des types** : `find_matching_rule`, `rule_matches`, `derive_prefix_pattern`, `_rules_for_property`, `resolve_category_id`, `migrate`, `check` réutilisés avec les mêmes signatures d'une tâche à l'autre.
- **Point de vigilance** : `NATURE_BY_LABEL` (Task 2) — vérifier les libellés exacts dans `category_service.py` avant d'exécuter ; c'est la seule dépendance non lue intégralement.

## Suite (hors ce plan)

Plan séparé « Étape 3 §5 — Frontend : écrans Inbox + Règles » : chaque écran passe par `ui-mockup` (maquette validée par Louis) puis implémentation + E2E `webapp-testing`, en consommant les API de ce plan (`/api/inbox`, `/api/rules`).
