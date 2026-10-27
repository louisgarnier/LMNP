# Toggle d'imputation + page « chaîne fiscale » — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendre l'ordre d'imputation fiscal choisissable par année (déficit-d'abord / amort-d'abord) et l'exposer dans une nouvelle page « chaîne fiscale » (3 tableaux chaînés, colonnes App + Officiel + Écart, toggle fonctionnel sur les années bénéficiaires).

**Architecture :** Le moteur `compute_fiscal_timeline` reçoit un dict de choix par année et inverse l'ordre d'imputation pour les années au choix « amort ». Les choix sont stockés dans une nouvelle table `fiscal_imputation_choices`. Un service `fiscal_chain_service` assemble, par année, les valeurs App (moteur) + Officiel (liasses) + écart pour les 3 étapes. La page front consomme `GET /api/fiscal/chaine` et persiste chaque changement via `PUT /api/fiscal/imputation/{year}` puis re-fetch.

**Tech Stack :** Python 3.10 / FastAPI / SQLAlchemy / SQLite / pytest ; Next.js App Router / React / TypeScript (styles inline).

## Global Constraints

- **Argent en euros au niveau service** : l'ORM (EuroCents) renvoie déjà des euros. NE JAMAIS re-diviser par 100.
- **Stocks fiscaux au niveau ENTITÉ** (tous biens agrégés), jamais par appartement. Cf. `fiscal_service.entity_year_inputs`.
- **Tests sur base réelle = engine `?mode=ro`** (motif sanctionné, cf. `test_fiscal_service_integration.py` / `test_reconciliation_service.py`). JAMAIS `SessionLocal` (garde de quarantaine prod).
- **Choix d'imputation = par année, uniquement pertinent sur année bénéficiaire** (résultat fiscal de l'exercice > 0, c.-à-d. `result_after > _EPS` dans le moteur). Défaut = `'deficit'` (méthode recommandée : le déficit expire à 10 ans, l'amort jamais).
- **Modes valides** : exactement `'deficit'` et `'amort'`. Toute autre valeur = rejet (400 côté API, `ValueError` côté service).
- **Front** : `'use client'`, styles inline, mêmes conventions que `frontend/app/dashboard/liasse-fiscale/detail/page.tsx`. Couleurs exactes de la maquette (cf. Task 5).
- **HORS PÉRIMÈTRE de ce plan** (→ plan « reprise » suivant) : le calcul 2026+ à partir de la position officielle. Ici la bande « Reprise » et la ligne 2026 sont rendues en informatif à partir des valeurs que le moteur calcule déjà depuis 2021 (pas de position d'ouverture injectée).

**Maquette cible validée par Louis** : `docs/project/analysis/maquettes-position-fiscale/maquette3-chaine-fiscale.html` (interactive — le toggle y recalcule en JS ; c'est le comportement de référence).

---

## File Structure

- `backend/api/services/fiscal_service.py` (modifier) — nouveau paramètre `imputation_choices` sur `compute_fiscal_timeline` ; `get_fiscal_timeline` lit les choix en base.
- `backend/database/models.py` (modifier) — modèle `FiscalImputationChoice`.
- `backend/database/migrations/add_fiscal_imputation_choices.py` (créer) — table.
- `backend/api/services/fiscal_chain_service.py` (créer) — assemble la chaîne App+Officiel+écart par année et par étape.
- `backend/api/routes/fiscal.py` (modifier) — `GET /fiscal/chaine`, `PUT /fiscal/imputation/{year}`.
- `backend/api/models.py` (modifier) — schémas Pydantic de sortie/entrée.
- `backend/tests/test_fiscal_imputation.py` (créer) — bascule d'ordre (fonction pure).
- `backend/tests/test_fiscal_chain_service.py` (créer) — assemblage chaîne (mode=ro, données réelles).
- `frontend/app/dashboard/liasse-fiscale/chaine/page.tsx` (créer) — la page.
- `frontend/app/dashboard/liasse-fiscale/page.tsx` (modifier) — lien « Voir la chaîne année par année → ».

---

### Task 1 : Moteur — ordre d'imputation choisissable par année

**Files:**
- Modify: `backend/api/services/fiscal_service.py:25-111` (signature + branche bénéfice)
- Test: `backend/tests/test_fiscal_imputation.py` (créer)

**Interfaces:**
- Consumes: rien (fonction pure existante).
- Produces: `compute_fiscal_timeline(years_data, deficit_report_years, amort_report_years, imputation_choices=None)`. `imputation_choices` = `dict[int, str]` ; valeurs `'deficit'` (défaut) ou `'amort'`. Le dict de résultat par année gagne la clé `"imputation_mode": 'deficit'|'amort'` (le mode effectif appliqué cette année-là).

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_fiscal_imputation.py
"""Le choix d'imputation par année inverse l'ordre déficit/amort sur un bénéfice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.services.fiscal_service import compute_fiscal_timeline


def _timeline(choices=None):
    # 2021 : grosse perte -> stock déficit. 2022 : amort différé -> stock amort.
    # 2023 : bénéfice avant amort, amort de l'année nul -> impute sur les stocks.
    years = [
        {"year": 2021, "resultat_comptable": -20000.0, "amortissements": 0.0},
        {"year": 2022, "resultat_comptable": -5000.0, "amortissements": 8000.0},
        {"year": 2023, "resultat_comptable": 4000.0, "amortissements": 0.0},
    ]
    return compute_fiscal_timeline(years, 10, None, imputation_choices=choices)


def test_defaut_impute_le_deficit_dabord():
    r = _timeline()[2023]
    assert r["imputation_deficits"] == 4000.0   # bénéfice absorbé par le déficit
    assert r["imputation_amorts"] == 0.0
    assert r["imputation_mode"] == "deficit"


def test_choix_amort_impute_lamortissement_dabord():
    r = _timeline({2023: "amort"})[2023]
    assert r["imputation_amorts"] == 3000.0     # stock amort 2022 (8000-5000) absorbé d'abord
    assert r["imputation_deficits"] == 1000.0   # le reste sur le déficit
    assert r["imputation_mode"] == "amort"


def test_choix_sur_annee_non_beneficiaire_est_ignore():
    # 2021 est en perte : le mode 'amort' n'a aucun effet, pas d'imputation.
    r = _timeline({2021: "amort"})[2021]
    assert r["imputation_deficits"] == 0.0
    assert r["imputation_amorts"] == 0.0
```

- [ ] **Step 2 : Lancer le test — échec attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_imputation.py -v`
Expected: FAIL — `compute_fiscal_timeline() got an unexpected keyword argument 'imputation_choices'`.

- [ ] **Step 3 : Implémenter**

Dans `compute_fiscal_timeline`, ajouter le paramètre et brancher l'ordre. Signature (ligne 25) :

```python
def compute_fiscal_timeline(years_data, deficit_report_years, amort_report_years,
                            imputation_choices=None):
```

Docstring : ajouter sous `amort_report_years` :

```
        imputation_choices: dict {year: 'deficit'|'amort'} — ordre d'imputation
            d'un bénéfice pour l'année. 'deficit' (défaut) impute les déficits
            antérieurs d'abord ; 'amort' impute les amortissements reportés
            d'abord. Sans effet sur une année non bénéficiaire.
```

Au début du corps, normaliser :

```python
    imputation_choices = imputation_choices or {}
```

Remplacer la branche bénéfice (lignes 62-80) pour respecter le mode. Extraire deux helpers locaux et appeler dans l'ordre choisi :

```python
        mode = imputation_choices.get(year, "deficit")
        if result_after > _EPS:
            profit = result_after

            def _impute(stock):
                nonlocal profit
                taken = 0.0
                for item in sorted(stock, key=lambda x: x[0]):
                    if profit <= _EPS:
                        break
                    take = min(item[1], profit)
                    item[1] -= take
                    profit -= take
                    taken += take
                return taken

            if mode == "amort":
                imputation_amorts = _impute(amorts)
                imputation_deficits = _impute(deficits)
            else:
                imputation_deficits = _impute(deficits)
                imputation_amorts = _impute(amorts)
            resultat_fiscal_imposable = max(0.0, profit)
        else:
            deficit_annee = -result_after if result_after < 0 else 0.0
            if deficit_annee > _EPS:
                deficits.append([year, deficit_annee])
            resultat_fiscal_imposable = 0.0
```

Ajouter `"imputation_mode": mode,` dans le dict `results[year]` (après `"resultat_fiscal_imposable"`).

- [ ] **Step 4 : Lancer le test — succès attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_imputation.py -v`
Expected: 3 passed.

- [ ] **Step 5 : Non-régression du moteur existant**

Run: `cd backend && python3 -m pytest tests/test_fiscal_service_integration.py tests/test_reconciliation_service.py -q`
Expected: tout passe (le défaut `'deficit'` reproduit le comportement d'avant).

- [ ] **Step 6 : Commit**

```bash
python3 scripts/git_ops.py add backend/api/services/fiscal_service.py backend/tests/test_fiscal_imputation.py
python3 scripts/git_ops.py commit -m "[REFONTE] feat: ordre d'imputation fiscal choisissable par année (moteur)"
```

---

### Task 2 : Persistance — table des choix d'imputation

**Files:**
- Modify: `backend/database/models.py` (nouveau modèle, après `FiscalSettings` ~ligne 570)
- Create: `backend/database/migrations/add_fiscal_imputation_choices.py`
- Test: `backend/tests/test_fiscal_imputation_choices_model.py` (créer)

**Interfaces:**
- Produces: modèle `FiscalImputationChoice(id, year UNIQUE, mode)` ; table `fiscal_imputation_choices`.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_fiscal_imputation_choices_model.py
"""La table des choix d'imputation stocke un mode unique par année."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, FiscalImputationChoice


def test_year_unique_et_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    db = S()
    db.add(FiscalImputationChoice(year=2023, mode="amort"))
    db.commit()
    got = db.query(FiscalImputationChoice).filter_by(year=2023).one()
    assert got.mode == "amort"
    db.close()
```

- [ ] **Step 2 : Lancer — échec attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_imputation_choices_model.py -v`
Expected: FAIL — `ImportError: cannot import name 'FiscalImputationChoice'`.

- [ ] **Step 3 : Ajouter le modèle**

Dans `backend/database/models.py`, après la classe `FiscalSettings` :

```python
class FiscalImputationChoice(Base):
    """Choix d'ordre d'imputation d'un bénéfice, par exercice.

    mode = 'deficit' (déficit antérieur d'abord, défaut recommandé) ou
    'amort' (amortissements reportés d'abord, méthode du comptable). Une seule
    ligne par année ; absence de ligne = 'deficit'.
    """
    __tablename__ = "fiscal_imputation_choices"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, nullable=False, index=True)
    mode = Column(String(10), nullable=False, default="deficit")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4 : Lancer — succès attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_imputation_choices_model.py -v`
Expected: 1 passed.

- [ ] **Step 5 : Écrire la migration**

```python
# backend/database/migrations/add_fiscal_imputation_choices.py
"""Migration: table fiscal_imputation_choices (choix d'imputation par année).

⚠️ Avant de lancer, lire : ../../docs/workflow/BEST_PRACTICES.md
"""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "lmnp.db"


def migrate():
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fiscal_imputation_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL UNIQUE,
                mode VARCHAR(10) NOT NULL DEFAULT 'deficit',
                updated_at DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_fic_year ON fiscal_imputation_choices (year)")
        conn.commit()
        print("✅ Table fiscal_imputation_choices prête")
    except Exception as e:
        conn.rollback()
        print(f"❌ {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
```

- [ ] **Step 6 : Appliquer la migration**

Run: `cd backend && python3 -m database.migrations.add_fiscal_imputation_choices`
Expected: `✅ Table fiscal_imputation_choices prête`.

- [ ] **Step 7 : Commit**

```bash
python3 scripts/git_ops.py add backend/database/models.py backend/database/migrations/add_fiscal_imputation_choices.py backend/tests/test_fiscal_imputation_choices_model.py
python3 scripts/git_ops.py commit -m "[REFONTE] feat: table fiscal_imputation_choices (persistance des choix)"
```

---

### Task 3 : Service — assemblage de la chaîne (App + Officiel + Écart)

**Files:**
- Modify: `backend/api/services/fiscal_service.py` (`get_fiscal_timeline` lit les choix)
- Create: `backend/api/services/fiscal_chain_service.py`
- Test: `backend/tests/test_fiscal_chain_service.py`

**Interfaces:**
- Consumes: `compute_fiscal_timeline(..., imputation_choices)` (Task 1) ; `FiscalImputationChoice` (Task 2) ; `reconciliation_service.load_liasses()` (existant — renvoie `{year: liasse_dict}`) ; `fiscal_service.entity_year_range`, `entity_year_inputs`.
- Produces :
  - `fiscal_service.read_imputation_choices(db) -> dict[int,str]`.
  - `fiscal_chain_service.build_chain(db) -> {"years": [int], "chain": {year: LigneChaine}}`.

  `LigneChaine` (tous montants en euros, signe naturel) :
  ```
  {
    "year": int, "brouillon": bool, "profitable": bool, "mode": "deficit"|"amort",
    # Étape 1 (App) + rappel officiel
    "resultat_comptable": float, "amort_annee": float, "r_ha": float,
    "amort_deductible": float, "amort_mis_de_cote": float,
    "resultat_fiscal_app": float, "resultat_fiscal_officiel": float | None,
    # Étape 2 — tirelire déficit
    "deficit_depart": float, "deficit_mouvement": float,
    "deficit_fin_app": float, "deficit_fin_officiel": float | None, "deficit_ecart": float | None,
    # Étape 3 — tirelire amort
    "amort_depart": float, "amort_impute": float,
    "amort_fin_app": float, "amort_fin_officiel": float | None, "amort_ecart": float | None,
  }
  ```
  Règles : `profitable = (resultat_fiscal_app > 0.005)`. `resultat_fiscal_app = imputation_deficits + imputation_amorts + resultat_fiscal_imposable` si bénéfice, sinon `-deficit_annee`. `deficit_mouvement = deficit_fin_app - deficit_depart`. `amort_impute = amort_mis_de_cote - (amort_fin_app - amort_depart)` (part du bénéfice retirée du stock amort). `*_officiel` : déficit cumulé = `liasse["fiscal"]["stock_deficit_reportable_fin"]` ; amort cumulé = `liasse["fiscal"]["stock_amort_reporte_reconstitue"]` ; résultat fiscal officiel = `-liasse["fiscal"]["deficit_reportable_de_lannee"]` si perte, sinon la valeur de bénéfice si la liasse la porte (sinon `None`). `*_ecart = app - officiel` (None si pas de liasse). `brouillon = (year not in liasses)`.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
# backend/tests/test_fiscal_chain_service.py
"""La chaîne fiscale assemble App (moteur) + Officiel (liasses) par année."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.services.fiscal_chain_service import build_chain

PROD_DB = (Path(__file__).parent.parent / "database" / "lmnp.db").resolve()
_ro = create_engine(f"sqlite:///file:{PROD_DB}?mode=ro&uri=true", connect_args={"uri": True})
_ROSession = sessionmaker(bind=_ro)


@pytest.fixture
def chain():
    db = _ROSession()
    try:
        yield build_chain(db)
    finally:
        db.close()


def test_2023_est_la_seule_annee_beneficiaire(chain):
    prof = [y for y, l in chain["chain"].items() if l["profitable"]]
    assert prof == [2023]


def test_2023_defaut_deficit_dabord(chain):
    l = chain["chain"][2023]
    assert l["mode"] == "deficit"
    # déficit-d'abord : la tirelire déficit baisse (~20035), l'amort ne bouge pas.
    assert l["deficit_fin_app"] == pytest.approx(20035, abs=2.0)
    assert l["deficit_mouvement"] < 0
    assert l["amort_impute"] == pytest.approx(0.0, abs=1.0)


def test_officiel_et_ecart_2025(chain):
    l = chain["chain"][2025]
    assert l["deficit_fin_officiel"] == pytest.approx(39913, abs=1.0)
    assert l["amort_fin_officiel"] == pytest.approx(35364, abs=1.0)
    assert l["deficit_ecart"] == pytest.approx(l["deficit_fin_app"] - 39913, abs=1.0)


def test_2026_brouillon_sans_officiel(chain):
    l = chain["chain"][2026]
    assert l["brouillon"] is True
    assert l["deficit_fin_officiel"] is None
    assert l["deficit_ecart"] is None
```

- [ ] **Step 2 : Lancer — échec attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_chain_service.py -v`
Expected: FAIL — `ModuleNotFoundError: fiscal_chain_service`.

- [ ] **Step 3 : `get_fiscal_timeline` lit les choix**

Dans `fiscal_service.py`, ajouter (près de `_read_settings`) :

```python
def read_imputation_choices(db):
    """{year: mode} depuis la table, pour les modes non-défaut uniquement."""
    from backend.database.models import FiscalImputationChoice
    rows = db.query(FiscalImputationChoice).all()
    return {r.year: r.mode for r in rows}
```

Et modifier `get_fiscal_timeline` :

```python
def get_fiscal_timeline(db):
    deficit_years, amort_years = _read_settings(db)
    years_data = [entity_year_inputs(db, y) for y in entity_year_range(db)]
    choices = read_imputation_choices(db)
    return compute_fiscal_timeline(years_data, deficit_years, amort_years,
                                   imputation_choices=choices)
```

- [ ] **Step 4 : Écrire `fiscal_chain_service.build_chain`**

```python
# backend/api/services/fiscal_chain_service.py
"""Assemble la « chaîne fiscale » année par année : valeurs App (moteur) +
Officiel (liasses déposées) + écart, pour les 3 étapes (résultat fiscal,
tirelire déficit, tirelire amortissements). Niveau entité."""
from backend.api.services.fiscal_service import get_fiscal_timeline, entity_year_range
from backend.api.services.reconciliation_service import load_liasses

_EPS = 0.005


def build_chain(db):
    tl = get_fiscal_timeline(db)
    liasses = load_liasses()
    years = sorted(tl.keys())

    chain = {}
    prev_deficit = 0.0
    prev_amort = 0.0
    for y in years:
        r = tl[y]
        beneficiaire = (r["imputation_deficits"] + r["imputation_amorts"]
                        + r["resultat_fiscal_imposable"]) > _EPS
        if beneficiaire:
            resultat_fiscal_app = (r["imputation_deficits"] + r["imputation_amorts"]
                                   + r["resultat_fiscal_imposable"])
        else:
            resultat_fiscal_app = -r["deficit_annee"]

        deficit_fin = r["stock_deficit_fin"]
        amort_fin = r["stock_amort_fin"]

        li = liasses.get(y)
        fisc = (li or {}).get("fiscal", {})
        deficit_off = fisc.get("stock_deficit_reportable_fin") if li else None
        amort_off = fisc.get("stock_amort_reporte_reconstitue") if li else None
        if li:
            drl = fisc.get("deficit_reportable_de_lannee", 0.0)
            rf_off = -drl if drl else 0.0
        else:
            rf_off = None

        chain[y] = {
            "year": y,
            "brouillon": li is None,
            "profitable": beneficiaire,
            "mode": r.get("imputation_mode", "deficit"),
            "resultat_comptable": round(r["resultat_comptable"], 2),
            "amort_annee": round(r["amortissements"], 2),
            "r_ha": round(r["r_ha"], 2),
            "amort_deductible": round(r["amort_deductible"], 2),
            "amort_mis_de_cote": round(r["amort_differe_annee"], 2),
            "resultat_fiscal_app": round(resultat_fiscal_app, 2),
            "resultat_fiscal_officiel": (round(rf_off, 2) if rf_off is not None else None),
            "deficit_depart": round(prev_deficit, 2),
            "deficit_mouvement": round(deficit_fin - prev_deficit, 2),
            "deficit_fin_app": round(deficit_fin, 2),
            "deficit_fin_officiel": deficit_off,
            "deficit_ecart": (round(deficit_fin - deficit_off, 2) if deficit_off is not None else None),
            "amort_depart": round(prev_amort, 2),
            "amort_impute": round(r["amort_differe_annee"] - (amort_fin - prev_amort), 2),
            "amort_fin_app": round(amort_fin, 2),
            "amort_fin_officiel": amort_off,
            "amort_ecart": (round(amort_fin - amort_off, 2) if amort_off is not None else None),
        }
        prev_deficit = deficit_fin
        prev_amort = amort_fin

    return {"years": years, "chain": chain}
```

- [ ] **Step 5 : Lancer — succès attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_chain_service.py -v`
Expected: 4 passed.

- [ ] **Step 6 : Commit**

```bash
python3 scripts/git_ops.py add backend/api/services/fiscal_service.py backend/api/services/fiscal_chain_service.py backend/tests/test_fiscal_chain_service.py
python3 scripts/git_ops.py commit -m "[REFONTE] feat: service chaine fiscale (App+Officiel+ecart, choix lus en base)"
```

---

### Task 4 : API — `GET /fiscal/chaine` + `PUT /fiscal/imputation/{year}`

**Files:**
- Modify: `backend/api/routes/fiscal.py`
- Modify: `backend/api/models.py` (schéma d'entrée du PUT)
- Test: `backend/tests/test_fiscal_chain_api.py` (créer)

**Interfaces:**
- Consumes: `fiscal_chain_service.build_chain` (Task 3) ; `FiscalImputationChoice` (Task 2).
- Produces:
  - `GET /api/fiscal/chaine` → `{"years": [...], "chain": {...}, "reprise": {"annee": 2025, "deficit": 39913, "amort": 35364}}` (bloc `reprise` statique/informatif dans ce plan).
  - `PUT /api/fiscal/imputation/{year}` body `{"mode": "deficit"|"amort"}` → upsert la ligne, renvoie la chaîne recalculée (même forme que GET). 400 si `mode` invalide.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
# backend/tests/test_fiscal_chain_api.py
"""Contrat des routes chaîne + imputation (validation d'entrée)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_get_chaine_expose_years_et_chain():
    r = client.get("/api/fiscal/chaine")
    assert r.status_code == 200
    body = r.json()
    assert "years" in body and "chain" in body and "reprise" in body


def test_put_imputation_rejette_mode_invalide():
    r = client.put("/api/fiscal/imputation/2023", json={"mode": "n_importe_quoi"})
    assert r.status_code == 400
```

Note implémenteur : `TestClient(app)` s'exécute sur la vraie base via `get_db`. Le test `test_put_imputation_rejette_mode_invalide` NE doit PAS écrire (rejet avant commit). N'ajoute aucun test qui persiste un mode ici (respect de la garde prod) — le recalcul est déjà couvert au niveau service (Task 3).

- [ ] **Step 2 : Lancer — échec attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_chain_api.py -v`
Expected: FAIL (404 sur les deux routes).

- [ ] **Step 3 : Schéma d'entrée**

Dans `backend/api/models.py`, ajouter :

```python
class ImputationChoiceUpdate(BaseModel):
    mode: str  # 'deficit' | 'amort'
```

- [ ] **Step 4 : Routes**

Dans `backend/api/routes/fiscal.py`, ajouter les imports et routes :

```python
from backend.database.models import FiscalImputationChoice
from backend.api.models import ImputationChoiceUpdate
from backend.api.services.fiscal_chain_service import build_chain

_REPRISE = {"annee": 2025, "deficit": 39913, "amort": 35364}
_MODES = {"deficit", "amort"}


@router.get("/fiscal/chaine")
def fiscal_chaine(db: Session = Depends(get_db)):
    out = build_chain(db)
    out["reprise"] = _REPRISE
    return out


@router.put("/fiscal/imputation/{year}")
def put_imputation(year: int, body: ImputationChoiceUpdate, db: Session = Depends(get_db)):
    if body.mode not in _MODES:
        raise HTTPException(400, f"mode invalide: {body.mode}")
    row = db.query(FiscalImputationChoice).filter_by(year=year).first()
    if row is None:
        row = FiscalImputationChoice(year=year, mode=body.mode)
        db.add(row)
    else:
        row.mode = body.mode
    db.commit()
    out = build_chain(db)
    out["reprise"] = _REPRISE
    return out
```

- [ ] **Step 5 : Lancer — succès attendu**

Run: `cd backend && python3 -m pytest tests/test_fiscal_chain_api.py -v`
Expected: 2 passed.

- [ ] **Step 6 : Vérif manuelle route + non-régression**

Run: `cd backend && python3 -m pytest tests/ -q -k "fiscal or reconciliation"`
Expected: tout vert.

- [ ] **Step 7 : Commit**

```bash
python3 scripts/git_ops.py add backend/api/routes/fiscal.py backend/api/models.py backend/tests/test_fiscal_chain_api.py
python3 scripts/git_ops.py commit -m "[REFONTE] feat: routes /fiscal/chaine et /fiscal/imputation/{year}"
```

---

### Task 5 : Front — page « chaîne fiscale » avec toggle fonctionnel

**Files:**
- Create: `frontend/app/dashboard/liasse-fiscale/chaine/page.tsx`
- Modify: `frontend/app/dashboard/liasse-fiscale/page.tsx` (lien vers la chaîne)
- Reference visuelle EXACTE : `docs/project/analysis/maquettes-position-fiscale/maquette3-chaine-fiscale.html`
- Pattern de câblage : `frontend/app/dashboard/liasse-fiscale/detail/page.tsx`

**Interfaces:**
- Consumes: `GET /api/fiscal/chaine`, `PUT /api/fiscal/imputation/{year}` (Task 4).

- [ ] **Step 1 : Écrire le composant complet**

L'implémenteur écrit le JSX complet en reproduisant la maquette `maquette3-chaine-fiscale.html` (3 cartes = 3 tableaux, mêmes en-têtes/couleurs), branché sur `GET /api/fiscal/chaine`. Règles précises :

- Route GLOBALE (pas de propriété active) : le layout exempte déjà `/dashboard/liasse-fiscale` et ses sous-routes (`startsWith`).
- Fetch au montage : `GET ${API_BASE_URL}/api/fiscal/chaine` → state `{years, chain, reprise}`. Réutiliser `API_BASE_URL`, helper `eur`, conventions de `detail/page.tsx`.
- **Tableau A (Étape 1)** — colonnes : Année · Résultat comptable · +Amort année · =Avant amort (`r_ha`) · Amort déduit (`amort_deductible`) · Amort mis de côté (`amort_mis_de_cote`) · =Résultat fiscal App (`resultat_fiscal_app`) · Rappel officiel (`resultat_fiscal_officiel`, `—` si null).
- **Tableau B (Étape 2)** — colonnes : Année · **Imputer en priorité** · Déficit départ (`deficit_depart`) · Résultat fiscal (`resultat_fiscal_app`) · Mouvement (`deficit_mouvement`, `—` si 0) · Déficit fin App (`deficit_fin_app`) · Déficit fin Officiel (`deficit_fin_officiel`) · Écart (`deficit_ecart`). La colonne « Imputer en priorité » : sur les lignes `profitable === true`, un `<select>` avec options `amort` (« Amort. d'abord (comptable) ») et `deficit` (« Déficit d'abord (reco) »), `value={chain[y].mode}` ; sinon texte gris (`perte` si `resultat_fiscal_app < 0`, sinon `neutre`).
- **Tableau C (Étape 3)** — colonnes : Année · Amort départ (`amort_depart`) · +Mis de côté (`amort_mis_de_cote`) · −Imputation (`amort_impute`, `—` si 0) · Amort fin App (`amort_fin_app`) · Amort fin Officiel (`amort_fin_officiel`) · Écart (`amort_ecart`).
- **onChange du select** : `await fetch(PUT /api/fiscal/imputation/${y}, {method:'PUT', headers, body: JSON.stringify({mode})})` → la réponse EST la chaîne recalculée → `setState`. Pendant l'appel, désactiver le select (état `saving`).
- **Écart** : couleur rouge `#bf2600` si `|ecart| >= 1000`, vert `#00875a` sinon ; `—` si null.
- **Reprise** : après la ligne 2025 dans B et C, une ligne bandeau verte (`background:#e3fcef`) « Reprise fin 2025 — on repart de l'officiel : déficit {reprise.deficit} · amort {reprise.amort} ». **Informatif** (pas de calcul live 2026 ici).
- **Brouillon** (`brouillon===true`, ex. 2026) : colonnes Officiel = `— pas de liasse`, écart `—`.
- Bandeaux explicatifs bas de page (reprise + toggle) repris de la maquette.

- [ ] **Step 2 : Lien depuis la vision globale**

Dans `frontend/app/dashboard/liasse-fiscale/page.tsx`, à côté du lien « Voir le détail par appartement → », ajouter :

```tsx
<Link href="/dashboard/liasse-fiscale/chaine" style={{ fontSize: 12, color: '#0052cc', marginLeft: 16 }}>
  Voir la chaîne fiscale année par année →
</Link>
```

- [ ] **Step 3 : Build + typecheck**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "chaine" ; npm run build 2>&1 | grep -E "Compiled successfully|Failed"`
Expected: pas d'erreur TS sur la page ; `Compiled successfully`.

- [ ] **Step 4 : Vérif route + toggle en direct**

Run (backend + frontend déjà lancés) :
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/dashboard/liasse-fiscale/chaine   # 200
curl -s http://localhost:8000/api/fiscal/chaine | python3 -c "import sys,json; d=json.load(sys.stdin); print('2023 profitable =', d['chain']['2023']['profitable'], '| mode =', d['chain']['2023']['mode'])"
```
Expected: `200` ; `2023 profitable = True | mode = deficit`.

- [ ] **Step 5 : Commit**

```bash
python3 scripts/git_ops.py add frontend/app/dashboard/liasse-fiscale/chaine/page.tsx frontend/app/dashboard/liasse-fiscale/page.tsx
python3 scripts/git_ops.py commit -m "[REFONTE] feat(front): page chaine fiscale + toggle d'imputation fonctionnel"
```

---

## Self-Review (rédacteur)

- **Couverture spec** : moteur paramétrable (T1) · persistance (T2) · assemblage App/Officiel (T3) · API + validation (T4) · page + toggle live (T5). Reprise 2026+ explicitement hors périmètre (plan suivant). ✅
- **Placeholders** : aucun — code complet côté backend ; front cadré par la maquette validée + le pattern `detail/page.tsx` (même approche que la Task 4 du plan précédent, acceptée). ✅
- **Cohérence des types** : `imputation_choices` (dict) traverse T1→T3 ; `mode`/`year` cohérents T2→T4 ; clés de `LigneChaine` (T3) = champs consommés en T5. ✅
- **Signe** : montants en euros signe naturel ; écart = app − officiel ; pas de re-division /100. ✅

## Point à trancher avec Louis (avant/à la revue)

Le `PUT /fiscal/imputation/{year}` **écrit en base de prod** (le choix est persistant, c'est voulu). Aucun test ne persiste (garde de quarantaine respectée : on teste le rejet 400 et le recalcul au niveau service). À confirmer : OK d'exposer une écriture non couverte par test d'intégration écrivant, le recalcul étant validé côté service ?
