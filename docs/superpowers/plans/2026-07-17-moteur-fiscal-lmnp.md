# Moteur fiscal LMNP — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Doter l'application d'un moteur fiscal qui calcule, pour chaque exercice, la réintégration des amortissements, le déficit reportable, les amortissements reportés et leurs cumuls inter-annuels — au niveau de l'entité (SIREN), reproduisant les liasses déposées.

**Architecture:** Cœur = une **fonction pure** `compute_fiscal_timeline` qui prend la suite chronologique des résultats comptables par année et déroule l'algorithme de report (testable sans base). Autour : une couche d'agrégation qui somme le compte de résultat de tous les biens présents chaque année, une table de réglages globaux (durées de report), et une route API. Aucune donnée en dur : les biens et les années sont énumérés dynamiquement depuis les transactions.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy, SQLite, pytest.

## Global Constraints

- **Calcul au niveau ENTITÉ**, jamais bien par bien (prouvé par la liasse 2024 : Evry bénéficiaire hors-amortissement mais tous les amortissements reportés). Les stocks de report sont globaux.
- **Aucune donnée en dur** : aucun ID de bien, aucun nom, aucune année codés. Ajouter un appartement ne doit rien casser — il entre automatiquement dans l'agrégation.
- **Chronologie obligatoire** : le calcul d'une année dépend des stocks de toutes les précédentes ; toujours dérouler depuis la première année de transactions.
- **Montants en euros** dans le moteur (le service `calculate_compte_resultat` renvoie déjà des floats en euros). La base stocke en centimes mais le service de CR a déjà fait la conversion.
- **Ordre d'imputation** : amortissement de l'année d'abord (plafonné au bénéfice avant amortissement), puis déficits antérieurs (plus anciens en premier), puis amortissements reportés antérieurs.
- **Durées de report** : déficit configurable (défaut 10 ans), amortissements configurables (défaut illimité = pas de purge).

---

## Fichiers

- Créer : `backend/api/services/fiscal_service.py` — moteur (fonction pure + agrégation entité + lecture réglages).
- Modifier : `backend/database/models.py` — ajout du modèle `FiscalSettings` (table de réglages globaux, une seule ligne).
- Créer : `backend/database/migrations/add_fiscal_settings.py` — création de la table + ligne par défaut.
- Modifier : `backend/api/models.py` — schémas Pydantic de réponse fiscale + réglages.
- Créer : `backend/api/routes/fiscal.py` — routes `GET /api/fiscal/calculate`, `GET/PUT /api/fiscal/settings`.
- Modifier : `backend/api/main.py` — enregistrement du router.
- Créer : `backend/tests/test_fiscal_timeline.py` — tests unitaires de la fonction pure (dont cas construits que les liasses ne couvrent pas).
- Créer : `backend/tests/test_fiscal_validation_liasses.py` — validation contre la vraie suite 2021→2025.
- Créer : `backend/tests/test_fiscal_routes.py` — tests API.
- Modifier : `backend/scripts/golden_master.py` — ajout du bloc fiscal à l'extraction (garde-fou de non-régression).

---

## Task 1 : Fonction pure `compute_fiscal_timeline` + tests unitaires

Le cœur risqué, isolé et testable sans base. Chaque année : résultat comptable et amortissements en entrée ; réintégration, déficit, imputations, imposable et stocks en sortie.

**Files:**
- Create: `backend/api/services/fiscal_service.py`
- Test: `backend/tests/test_fiscal_timeline.py`

**Interfaces:**
- Produces: `compute_fiscal_timeline(years_data: list[dict], deficit_report_years: int, amort_report_years: int | None) -> dict[int, dict]`
  - `years_data` : liste **ordonnée par année croissante** de `{"year": int, "resultat_comptable": float, "amortissements": float}` (amortissements ≥ 0, valeur absolue de la charge d'amortissement).
  - `amort_report_years = None` signifie report illimité (pas de purge).
  - Retour : `{year: {...}}` avec les clés listées à l'étape 3.

- [ ] **Step 1: Écrire les tests unitaires (ils doivent échouer)**

```python
# backend/tests/test_fiscal_timeline.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.api.services.fiscal_service import compute_fiscal_timeline

C = 0.02  # tolérance centimes


def test_annee_deficitaire_reporte_tout():
    # Un seul exercice, déficit avant amortissement -> aucun amortissement déduit,
    # déficit reportable = |R_ha|, imposable 0.
    out = compute_fiscal_timeline(
        [{"year": 2021, "resultat_comptable": -24729.17, "amortissements": 632.49}],
        deficit_report_years=10, amort_report_years=None,
    )[2021]
    assert out["r_ha"] == pytest.approx(-24096.68, abs=C)
    assert out["amort_deductible"] == pytest.approx(0.0, abs=C)
    assert out["amort_differe_annee"] == pytest.approx(632.49, abs=C)
    assert out["deficit_annee"] == pytest.approx(24096.68, abs=C)
    assert out["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)
    assert out["stock_deficit_fin"] == pytest.approx(24096.68, abs=C)
    assert out["stock_amort_fin"] == pytest.approx(632.49, abs=C)


def test_benefice_absorbe_par_amortissement_de_l_annee():
    # R_ha positif mais < amortissements de l'année : tout le bénéfice absorbe
    # l'amortissement courant, l'excédent est reporté, aucun déficit antérieur imputé.
    out = compute_fiscal_timeline([
        {"year": 2021, "resultat_comptable": -24729.17, "amortissements": 632.49},
        {"year": 2022, "resultat_comptable": -4410.58, "amortissements": 10350.94},
    ], deficit_report_years=10, amort_report_years=None)[2022]
    assert out["r_ha"] == pytest.approx(5940.36, abs=C)
    assert out["amort_deductible"] == pytest.approx(5940.36, abs=C)
    assert out["amort_differe_annee"] == pytest.approx(4410.58, abs=C)
    assert out["imputation_deficits"] == pytest.approx(0.0, abs=C)
    assert out["deficit_annee"] == pytest.approx(0.0, abs=C)
    assert out["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)
    # stock déficit inchangé (24096.68), stock amort cumulé 632.49 + 4410.58
    assert out["stock_deficit_fin"] == pytest.approx(24096.68, abs=C)
    assert out["stock_amort_fin"] == pytest.approx(5043.07, abs=C)


def test_benefice_impute_deficit_anterieur():
    # R_ha > amortissements de l'année : le résidu impute le déficit 2021 (FIFO).
    out = compute_fiscal_timeline([
        {"year": 2021, "resultat_comptable": -24729.17, "amortissements": 632.49},
        {"year": 2022, "resultat_comptable": -4410.58, "amortissements": 10350.94},
        {"year": 2023, "resultat_comptable": 4061.59, "amortissements": 11119.15},
    ], deficit_report_years=10, amort_report_years=None)[2023]
    assert out["r_ha"] == pytest.approx(15180.74, abs=C)
    assert out["amort_deductible"] == pytest.approx(11119.15, abs=C)
    assert out["amort_differe_annee"] == pytest.approx(0.0, abs=C)
    # résidu 4061.59 impute le déficit 2021
    assert out["imputation_deficits"] == pytest.approx(4061.59, abs=C)
    assert out["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)
    # stock déficit : 24096.68 - 4061.59 = 20035.09 ; stock amort inchangé 5043.07
    assert out["stock_deficit_fin"] == pytest.approx(20035.09, abs=C)
    assert out["stock_amort_fin"] == pytest.approx(5043.07, abs=C)


def test_gros_benefice_impute_deficit_puis_amortissements_puis_impose():
    # Cas CONSTRUIT (aucune liasse ne le couvre) : bénéfice qui épuise le déficit
    # ET une partie des amortissements reportés, puis dégage un imposable.
    out = compute_fiscal_timeline([
        {"year": 2021, "resultat_comptable": -1000.0, "amortissements": 3000.0},
        # 2021 : R_ha -1000-... attention resultat_comptable inclut amort.
        # R_ha = resultat_comptable + amort = -1000 + 3000 = 2000 (bénéfice).
        # deductible = min(3000, 2000) = 2000 ; amort différé 1000 ; result_after 0.
        {"year": 2022, "resultat_comptable": 50000.0, "amortissements": 2000.0},
        # R_ha = 52000 ; deductible amort année = 2000 ; result_after 50000.
        # déficit antérieur : 0 (2021 n'a pas fait de déficit, result_after 0).
        # amort reporté antérieur : 1000 -> imputé. imposable = 50000 - 1000 = 49000.
    ], deficit_report_years=10, amort_report_years=None)
    a21 = out[2021]
    assert a21["amort_differe_annee"] == pytest.approx(1000.0, abs=C)
    assert a21["deficit_annee"] == pytest.approx(0.0, abs=C)
    a22 = out[2022]
    assert a22["imputation_deficits"] == pytest.approx(0.0, abs=C)
    assert a22["imputation_amorts"] == pytest.approx(1000.0, abs=C)
    assert a22["resultat_fiscal_imposable"] == pytest.approx(49000.0, abs=C)
    assert a22["stock_amort_fin"] == pytest.approx(0.0, abs=C)


def test_deficit_expire_apres_duree_configurable():
    # Un déficit non imputé expire après `deficit_report_years`.
    data = [{"year": 2021, "resultat_comptable": -5000.0, "amortissements": 0.0}]
    # années intermédiaires neutres (R_ha 0)
    for y in range(2022, 2025):
        data.append({"year": y, "resultat_comptable": 0.0, "amortissements": 0.0})
    # 2025 : gros bénéfice, mais déficit 2021 doit avoir expiré (durée 3 ans -> expire dès 2025 : 2025-2021=4 > 3)
    data.append({"year": 2025, "resultat_comptable": 5000.0, "amortissements": 0.0})
    out = compute_fiscal_timeline(data, deficit_report_years=3, amort_report_years=None)[2025]
    # déficit 2021 expiré -> non imputé -> imposable = 5000
    assert out["imputation_deficits"] == pytest.approx(0.0, abs=C)
    assert out["resultat_fiscal_imposable"] == pytest.approx(5000.0, abs=C)
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_timeline.py -q`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'compute_fiscal_timeline'`.

- [ ] **Step 3: Écrire la fonction pure**

```python
# backend/api/services/fiscal_service.py
"""Moteur fiscal LMNP.

Calcule, au niveau de l'ENTITÉ (tous les biens agrégés), la réintégration des
amortissements, le déficit reportable, les amortissements reportés et leurs
cumuls d'une année sur l'autre. Reproduit la mécanique des liasses déposées.

Règle (art. 39 C CGI, LMNP) : un amortissement n'est déductible que dans la
limite du résultat AVANT amortissement (R_ha) ; l'excédent est reporté sans
limite de durée. Un déficit hors-amortissement est reportable N ans (10 par
défaut). Imputation d'un bénéfice : amortissement de l'année d'abord, puis
déficits antérieurs (plus anciens en premier), puis amortissements reportés.
"""
import logging

logger = logging.getLogger(__name__)

_EPS = 0.005  # seuil de purge des lignes de stock résiduelles (< 0,5 centime)


def compute_fiscal_timeline(years_data, deficit_report_years, amort_report_years):
    """Déroule l'algorithme fiscal sur une suite chronologique d'exercices.

    Args:
        years_data: liste ORDONNÉE par année croissante de dicts
            {"year": int, "resultat_comptable": float, "amortissements": float}.
            `amortissements` ≥ 0 (valeur absolue de la charge d'amortissement).
        deficit_report_years: durée de report du déficit (années). Un déficit
            millésimé Y est imputable jusqu'à Y + deficit_report_years inclus.
        amort_report_years: durée de report des amortissements, ou None = illimité.

    Returns:
        dict {year: résultat de l'exercice} — voir clés ci-dessous.
    """
    deficits = []  # [ [year, remaining], ... ] millésimés, FIFO
    amorts = []    # [ [year, remaining], ... ] millésimés, FIFO
    results = {}

    for row in years_data:
        year = row["year"]
        amort_annee = abs(row["amortissements"])
        r_ha = row["resultat_comptable"] + amort_annee  # résultat avant amortissement

        # Purge des stocks expirés (au titre de l'exercice courant).
        deficits = [d for d in deficits if (year - d[0]) <= deficit_report_years]
        if amort_report_years is not None:
            amorts = [a for a in amorts if (year - a[0]) <= amort_report_years]

        # Amortissement de l'année : déductible dans la limite de R_ha positif.
        deductible = min(amort_annee, max(0.0, r_ha))
        amort_differe_annee = amort_annee - deductible
        result_after = r_ha - deductible  # >= 0 si R_ha > 0, sinon = R_ha (< 0)

        imputation_deficits = 0.0
        imputation_amorts = 0.0
        deficit_annee = 0.0

        if result_after > _EPS:
            profit = result_after
            # 1) imputer les déficits antérieurs, plus anciens d'abord
            for d in sorted(deficits, key=lambda x: x[0]):
                if profit <= _EPS:
                    break
                take = min(d[1], profit)
                d[1] -= take
                profit -= take
                imputation_deficits += take
            # 2) imputer les amortissements reportés antérieurs, plus anciens d'abord
            for a in sorted(amorts, key=lambda x: x[0]):
                if profit <= _EPS:
                    break
                take = min(a[1], profit)
                a[1] -= take
                profit -= take
                imputation_amorts += take
            resultat_fiscal_imposable = max(0.0, profit)
        else:
            # Déficit de l'exercice (hors amortissement de l'année déjà écarté).
            deficit_annee = -result_after if result_after < 0 else 0.0
            if deficit_annee > _EPS:
                deficits.append([year, deficit_annee])
            resultat_fiscal_imposable = 0.0

        # Amortissement différé de l'année rejoint le stock.
        if amort_differe_annee > _EPS:
            amorts.append([year, amort_differe_annee])

        # Purge des lignes soldées.
        deficits = [d for d in deficits if d[1] > _EPS]
        amorts = [a for a in amorts if a[1] > _EPS]

        results[year] = {
            "year": year,
            "resultat_comptable": row["resultat_comptable"],
            "amortissements": amort_annee,
            "r_ha": r_ha,
            "amort_deductible": deductible,
            "amort_differe_annee": amort_differe_annee,
            "deficit_annee": deficit_annee,
            "imputation_deficits": imputation_deficits,
            "imputation_amorts": imputation_amorts,
            "resultat_fiscal_imposable": resultat_fiscal_imposable,
            "stock_deficit_fin": sum(d[1] for d in deficits),
            "stock_amort_fin": sum(a[1] for a in amorts),
        }

    return results
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_timeline.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/api/services/fiscal_service.py backend/tests/test_fiscal_timeline.py
git commit -m "[REFONTE] feat: moteur fiscal LMNP — fonction pure de report (déficit + amortissements)"
```

---

## Task 2 : Validation contre les liasses réelles (2021→2025)

Vérifie que la suite réelle des résultats comptables produit les chiffres des liasses déposées. Vérité-terrain : les PDF (`docs/files/*`). C'est le test qui garantit qu'on reproduit le comptable.

**Files:**
- Test: `backend/tests/test_fiscal_validation_liasses.py`

**Interfaces:**
- Consumes: `compute_fiscal_timeline` (Task 1).

- [ ] **Step 1: Écrire le test de validation**

```python
# backend/tests/test_fiscal_validation_liasses.py
"""Valide le moteur fiscal contre les liasses fiscales déposées.

Les résultats comptables par année (niveau entité) sont ceux calculés par
l'application au 2026-07-17 (relevés bancaires réels + amortissements + crédits).
Les valeurs attendues sont celles des liasses PDF ; là où l'appli diverge, c'est
une erreur documentée du cabinet (cf. docs/project/analysis/ECARTS_LIASSES_FISCALES.md).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.api.services.fiscal_service import compute_fiscal_timeline

C = 0.05

# Suite réelle entité (résultat comptable, amortissements) — source : application.
REEL = [
    {"year": 2021, "resultat_comptable": -24729.17, "amortissements": 632.49},
    {"year": 2022, "resultat_comptable": -4410.58, "amortissements": 10350.94},
    {"year": 2023, "resultat_comptable": 4061.59, "amortissements": 11119.15},
    {"year": 2024, "resultat_comptable": -20031.64, "amortissements": 14552.52},
    {"year": 2025, "resultat_comptable": -31338.22, "amortissements": 20337.59},
]


@pytest.fixture
def timeline():
    return compute_fiscal_timeline(REEL, deficit_report_years=10, amort_report_years=None)


def test_2024_deficit_reportable_conforme_liasse(timeline):
    # Liasse 2024 : déficit hors-amortissement 5 479 €.
    assert timeline[2024]["deficit_annee"] == pytest.approx(5479.12, abs=C)
    assert timeline[2024]["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)


def test_2025_deficit_reportable_diverge_de_64e_erreur_cabinet(timeline):
    # Liasse 2025 : 10 937 € ; appli : 11 000.63 € — écart de 63,68 € = erreur
    # du cabinet sur les intérêts de la colloc (l'appli a raison).
    assert timeline[2025]["deficit_annee"] == pytest.approx(11000.63, abs=C)
    assert timeline[2025]["deficit_annee"] - 10937 == pytest.approx(63.63, abs=1.0)


def test_2023_impute_le_deficit_2021(timeline):
    # 2023 bénéficiaire hors-amortissement : le résidu impute le déficit 2021,
    # imposable reste 0 (à confronter au BILAN 2023 lors de l'implémentation).
    assert timeline[2023]["imputation_deficits"] == pytest.approx(4061.59, abs=C)
    assert timeline[2023]["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)


def test_aucun_impot_sur_toutes_les_annees_passees(timeline):
    # Louis n'a jamais été imposable (stocks de report jamais épuisés).
    for y in (2021, 2022, 2023, 2024, 2025):
        assert timeline[y]["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)


def test_stocks_cumules_croissent_correctement(timeline):
    # Fin 2025 : stock déficit et stock amortissements reportés (cumuls).
    assert timeline[2025]["stock_deficit_fin"] == pytest.approx(36514.84, abs=C)
    assert timeline[2025]["stock_amort_fin"] == pytest.approx(39933.18, abs=C)
```

- [ ] **Step 2: Lancer, vérifier PASS**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_validation_liasses.py -q`
Expected: PASS (5 tests). Si un test échoue, l'algorithme diverge de la vérité-terrain — **ne pas ajuster le test à l'algorithme, comprendre l'écart d'abord**.

- [ ] **Step 3: Confronter au BILAN 2023 (contrôle manuel documenté)**

Lire `docs/files/BILAN 2023 LOUIS GARNIER.PDF` (Read tool, pages). Vérifier que le résultat fiscal imposable 2023 est bien 0 et qu'un déficit reportable y figure. Consigner le constat en une ligne dans `docs/project/analysis/ECARTS_LIASSES_FISCALES.md` (section « Reste à vérifier » → déplacer 2023 en « vérifié » ou noter l'écart).

- [ ] **Step 4: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/tests/test_fiscal_validation_liasses.py docs/project/analysis/ECARTS_LIASSES_FISCALES.md
git commit -m "[REFONTE] test: moteur fiscal validé contre les liasses 2021-2025"
```

---

## Task 3 : Table de réglages `FiscalSettings` + migration

Deux durées de report configurables, globales à l'entité (une seule ligne).

**Files:**
- Modify: `backend/database/models.py` (ajouter la classe en fin de fichier, avant tout `# ===` final)
- Create: `backend/database/migrations/add_fiscal_settings.py`
- Test: `backend/tests/test_fiscal_settings_model.py`

**Interfaces:**
- Produces: modèle `FiscalSettings(id, deficit_report_years: int = 10, amort_report_years: int | None = None, created_at, updated_at)`. `amort_report_years = NULL` ⇒ report illimité.

- [ ] **Step 1: Écrire le test du modèle (doit échouer)**

```python
# backend/tests/test_fiscal_settings_model.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.models import FiscalSettings


def test_fiscal_settings_defauts():
    s = FiscalSettings()
    # défauts métier : déficit 10 ans, amortissements illimités (NULL)
    assert FiscalSettings.__tablename__ == "fiscal_settings"
    cols = {c.name for c in FiscalSettings.__table__.columns}
    assert {"id", "deficit_report_years", "amort_report_years",
            "created_at", "updated_at"} <= cols
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_settings_model.py -q`
Expected: FAIL — `ImportError: cannot import name 'FiscalSettings'`.

- [ ] **Step 3: Ajouter le modèle**

Dans `backend/database/models.py`, ajouter (en suivant le style des autres modèles, ex. `ProRataSettings` ligne 516) :

```python
class FiscalSettings(Base):
    """Réglages fiscaux globaux à l'entité (une seule ligne).

    Durées de report configurables. amort_report_years NULL = report illimité
    (défaut légal LMNP pour les amortissements réputés différés).
    """
    __tablename__ = "fiscal_settings"

    id = Column(Integer, primary_key=True, index=True)
    deficit_report_years = Column(Integer, default=10, nullable=False)
    amort_report_years = Column(Integer, nullable=True)  # NULL = illimité
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4: Écrire la migration**

```python
# backend/database/migrations/add_fiscal_settings.py
"""Crée la table fiscal_settings et insère la ligne de réglages par défaut
(déficit reportable 10 ans, amortissements illimités).

Idempotent (marqueur schema_migrations). Backup automatique avant écriture.

Usage:
    python3 backend/database/migrations/add_fiscal_settings.py --yes
"""
import os
import shutil
import sys
from datetime import datetime

from sqlalchemy import text

from backend.database.connection import engine

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))
MIGRATION_NAME = "add_fiscal_settings"


def backup_database():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-fiscal-settings.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def already_applied(conn):
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"))
    return conn.execute(text(
        "SELECT 1 FROM schema_migrations WHERE name = :n"), {"n": MIGRATION_NAME}).fetchone() is not None


def main():
    with engine.begin() as conn:
        if already_applied(conn):
            print("✅ Déjà appliquée.")
            return 0
    if '--yes' not in sys.argv:
        print("⚠️ Crée fiscal_settings + ligne par défaut. Relancer avec --yes.")
        return 1
    dest = backup_database()
    print(f"💾 Backup : {dest}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS fiscal_settings ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "deficit_report_years INTEGER NOT NULL DEFAULT 10, "
            "amort_report_years INTEGER, "
            "created_at DATETIME, updated_at DATETIME)"))
        exists = conn.execute(text("SELECT COUNT(*) FROM fiscal_settings")).scalar()
        if exists == 0:
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(text(
                "INSERT INTO fiscal_settings (deficit_report_years, amort_report_years, created_at, updated_at) "
                "VALUES (10, NULL, :t, :t)"), {"t": now})
            print("➕ Ligne par défaut insérée (déficit 10 ans, amort illimité).")
        conn.execute(text(
            "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"),
            {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})
    print("✅ Migration terminée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Appliquer la migration + relancer le test**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m backend.database.migrations.add_fiscal_settings --yes && python3 -m pytest backend/tests/test_fiscal_settings_model.py -q`
Expected: migration « ✅ Migration terminée. » puis test PASS.

- [ ] **Step 6: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/database/models.py backend/database/migrations/add_fiscal_settings.py backend/tests/test_fiscal_settings_model.py
git commit -m "[REFONTE] feat: table fiscal_settings (durées de report configurables)"
```

---

## Task 4 : Agrégation entité + `get_fiscal` (lecture des vraies données)

Somme le compte de résultat de tous les biens présents chaque année, déroule le moteur depuis la première année de transactions, lit les durées dans `FiscalSettings`.

**Files:**
- Modify: `backend/api/services/fiscal_service.py`
- Test: `backend/tests/test_fiscal_service_integration.py`

**Interfaces:**
- Consumes: `compute_fiscal_timeline` (Task 1) ; `calculate_compte_resultat(db, year, property_id)` → dict avec `resultat_net: float`, `amortissements: float` ; modèle `FiscalSettings` (Task 3) ; `Property`, `Transaction`.
- Produces:
  - `entity_year_range(db) -> list[int]` — années de la 1re transaction à la dernière, incluses.
  - `entity_year_inputs(db, year) -> dict` — `{"year", "resultat_comptable", "amortissements"}` agrégé entité.
  - `get_fiscal_timeline(db) -> dict[int, dict]` — moteur déroulé sur toute la plage, réglages lus en base.
  - `get_fiscal(db, year) -> dict` — l'exercice `year` (lève `KeyError` → 404 côté route si hors plage).

- [ ] **Step 1: Écrire le test d'intégration (doit échouer)**

```python
# backend/tests/test_fiscal_service_integration.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.database import SessionLocal
from backend.api.services.fiscal_service import (
    entity_year_range, entity_year_inputs, get_fiscal_timeline, get_fiscal,
)

C = 0.1


def test_plage_annees_couvre_2021_a_lannee_courante():
    db = SessionLocal()
    try:
        years = entity_year_range(db)
        assert years[0] == 2021
        assert 2025 in years
    finally:
        db.close()


def test_inputs_entite_2024_somme_les_biens():
    db = SessionLocal()
    try:
        row = entity_year_inputs(db, 2024)
        # entité 2024 = Evry + Marseille abnb (après reclassement des 600€)
        assert row["resultat_comptable"] == pytest.approx(-20031.64, abs=1.0)
        assert row["amortissements"] == pytest.approx(14552.52, abs=1.0)
    finally:
        db.close()


def test_get_fiscal_2024_reproduit_la_liasse():
    db = SessionLocal()
    try:
        out = get_fiscal(db, 2024)
        assert out["deficit_annee"] == pytest.approx(5479.12, abs=1.0)
        assert out["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)
    finally:
        db.close()
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_service_integration.py -q`
Expected: FAIL — `ImportError: cannot import name 'entity_year_range'`.

- [ ] **Step 3: Ajouter l'agrégation à `fiscal_service.py`**

```python
# ── à ajouter dans backend/api/services/fiscal_service.py ──
from datetime import date

from sqlalchemy import func

from backend.database.models import Transaction, Property, FiscalSettings
from backend.api.services.compte_resultat_service import calculate_compte_resultat


def entity_year_range(db):
    """Années de la première à la dernière transaction (entité), incluses."""
    dmin = db.query(func.min(Transaction.date)).scalar()
    dmax = db.query(func.max(Transaction.date)).scalar()
    if dmin is None or dmax is None:
        return []
    y0 = dmin.year if hasattr(dmin, "year") else int(str(dmin)[:4])
    y1 = dmax.year if hasattr(dmax, "year") else int(str(dmax)[:4])
    return list(range(y0, y1 + 1))


def entity_year_inputs(db, year):
    """Somme resultat_net et amortissements de TOUS les biens pour l'année.

    Aucun bien codé en dur : on parcourt la table properties. Un bien sans
    activité l'année donnée contribue 0 (calculate_compte_resultat renvoie 0).
    """
    resultat_comptable = 0.0
    amortissements = 0.0
    for prop in db.query(Property).all():
        cr = calculate_compte_resultat(db, year, property_id=prop.id)
        resultat_comptable += cr.get("resultat_net", 0.0)
        amortissements += abs(cr.get("amortissements", 0.0))
    return {"year": year, "resultat_comptable": resultat_comptable,
            "amortissements": amortissements}


def _read_settings(db):
    s = db.query(FiscalSettings).first()
    if s is None:
        return 10, None
    return s.deficit_report_years, s.amort_report_years


def get_fiscal_timeline(db):
    """Déroule le moteur sur toute la plage d'années, réglages lus en base."""
    deficit_years, amort_years = _read_settings(db)
    years_data = [entity_year_inputs(db, y) for y in entity_year_range(db)]
    return compute_fiscal_timeline(years_data, deficit_years, amort_years)


def get_fiscal(db, year):
    """Résultat fiscal d'un exercice. Lève KeyError si hors plage."""
    return get_fiscal_timeline(db)[year]
```

- [ ] **Step 4: Lancer, vérifier PASS**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_service_integration.py -q`
Expected: PASS (3 tests). (Le backend sur le port 8000 n'a pas besoin d'être relancé : les tests importent le code directement.)

- [ ] **Step 5: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/api/services/fiscal_service.py backend/tests/test_fiscal_service_integration.py
git commit -m "[REFONTE] feat: agrégation entité + get_fiscal (moteur sur données réelles)"
```

---

## Task 5 : Schémas Pydantic + routes API

Expose le moteur : calcul d'un exercice, lecture et mise à jour des réglages.

**Files:**
- Modify: `backend/api/models.py` (fin de fichier)
- Create: `backend/api/routes/fiscal.py`
- Modify: `backend/api/main.py` (import + include_router)
- Test: `backend/tests/test_fiscal_routes.py`

**Interfaces:**
- Consumes: `get_fiscal`, `get_fiscal_timeline`, `_read_settings`, `entity_year_range` (Task 4) ; `FiscalSettings` (Task 3).
- Produces: routes `GET /api/fiscal/calculate?year=YYYY`, `GET /api/fiscal/timeline`, `GET /api/fiscal/settings`, `PUT /api/fiscal/settings`.

- [ ] **Step 1: Écrire les tests de routes (doivent échouer)**

```python
# backend/tests/test_fiscal_routes.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_get_calculate_2024():
    r = client.get("/api/fiscal/calculate", params={"year": 2024})
    assert r.status_code == 200
    body = r.json()
    assert abs(body["deficit_annee"] - 5479.12) < 1.0
    assert abs(body["resultat_fiscal_imposable"]) < 0.1


def test_get_calculate_annee_hors_plage_404():
    r = client.get("/api/fiscal/calculate", params={"year": 1999})
    assert r.status_code == 404


def test_get_settings_defaut():
    r = client.get("/api/fiscal/settings")
    assert r.status_code == 200
    assert r.json()["deficit_report_years"] == 10


def test_put_settings_modifie_la_duree():
    r = client.put("/api/fiscal/settings", json={"deficit_report_years": 8})
    assert r.status_code == 200
    assert r.json()["deficit_report_years"] == 8
    # remettre le défaut pour ne pas polluer la base
    client.put("/api/fiscal/settings", json={"deficit_report_years": 10})
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_routes.py -q`
Expected: FAIL — 404 sur toutes les routes (`/api/fiscal/...` non montées).

- [ ] **Step 3: Ajouter les schémas Pydantic**

Dans `backend/api/models.py`, en fin de fichier :

```python
# ── Fiscal ──
class FiscalYearResponse(BaseModel):
    year: int
    resultat_comptable: float
    amortissements: float
    r_ha: float
    amort_deductible: float
    amort_differe_annee: float
    deficit_annee: float
    imputation_deficits: float
    imputation_amorts: float
    resultat_fiscal_imposable: float
    stock_deficit_fin: float
    stock_amort_fin: float


class FiscalSettingsResponse(BaseModel):
    deficit_report_years: int
    amort_report_years: Optional[int] = None  # None = illimité

    class Config:
        from_attributes = True


class FiscalSettingsUpdate(BaseModel):
    deficit_report_years: Optional[int] = Field(None, ge=1, le=50)
    amort_report_years: Optional[int] = Field(None, ge=1, le=99)
    amort_illimite: Optional[bool] = None  # True => amort_report_years = NULL
```

- [ ] **Step 4: Écrire la route**

```python
# backend/api/routes/fiscal.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import FiscalSettings
from backend.api.models import (
    FiscalYearResponse, FiscalSettingsResponse, FiscalSettingsUpdate,
)
from backend.api.services.fiscal_service import (
    get_fiscal, get_fiscal_timeline, entity_year_range,
)

router = APIRouter()


@router.get("/fiscal/calculate", response_model=FiscalYearResponse)
def calculate_fiscal(year: int = Query(...), db: Session = Depends(get_db)):
    try:
        return get_fiscal(db, year)
    except KeyError:
        raise HTTPException(404, f"Aucune donnée fiscale pour l'exercice {year}")


@router.get("/fiscal/timeline")
def fiscal_timeline(db: Session = Depends(get_db)):
    tl = get_fiscal_timeline(db)
    return {"years": entity_year_range(db), "results": tl}


@router.get("/fiscal/settings", response_model=FiscalSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    s = db.query(FiscalSettings).first()
    if s is None:
        s = FiscalSettings(deficit_report_years=10, amort_report_years=None)
        db.add(s); db.commit(); db.refresh(s)
    return s


@router.put("/fiscal/settings", response_model=FiscalSettingsResponse)
def put_settings(body: FiscalSettingsUpdate, db: Session = Depends(get_db)):
    s = db.query(FiscalSettings).first()
    if s is None:
        s = FiscalSettings(); db.add(s)
    if body.deficit_report_years is not None:
        s.deficit_report_years = body.deficit_report_years
    if body.amort_illimite is True:
        s.amort_report_years = None
    elif body.amort_report_years is not None:
        s.amort_report_years = body.amort_report_years
    db.commit(); db.refresh(s)
    return s
```

- [ ] **Step 5: Enregistrer le router dans `main.py`**

Ajouter l'import à côté des autres routes et l'`include_router` près des lignes 196-211 :

```python
from backend.api.routes import fiscal  # avec les autres imports de routes
# ...
app.include_router(fiscal.router, prefix="/api", tags=["fiscal"])
```

- [ ] **Step 6: Lancer, vérifier PASS**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_fiscal_routes.py -q`
Expected: PASS (4 tests).

- [ ] **Step 7: Relancer le backend du port 8000 (code neuf) + smoke**

Le backend tourne depuis un process ancien ; il faut le relancer pour servir les nouvelles routes. Demander à Louis, ou (s'il a autorisé) :
```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN -t | xargs kill
cd backend && nohup python3 -m uvicorn api.main:app --port 8000 > /tmp/uvicorn_fiscal.log 2>&1 &
sleep 4 && curl -s "http://localhost:8000/api/fiscal/calculate?year=2024"
```
Expected: JSON avec `"deficit_annee": 5479.12...`, `"resultat_fiscal_imposable": 0.0`.

- [ ] **Step 8: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/api/models.py backend/api/routes/fiscal.py backend/api/main.py backend/tests/test_fiscal_routes.py
git commit -m "[REFONTE] feat: routes API fiscal (calculate, timeline, settings)"
```

---

## Task 6 : Garde-fou de non-régression (golden master)

Fige les sorties fiscales pour que toute évolution future qui les changerait soit détectée.

**Files:**
- Modify: `backend/scripts/golden_master.py`

**Interfaces:**
- Consumes: route `GET /api/fiscal/timeline` (Task 5).

- [ ] **Step 1: Localiser l'extraction golden**

Lire `backend/scripts/golden_master.py` et repérer où il interroge l'API par propriété/année (fonction d'extraction). Le fiscal est **au niveau entité**, donc à extraire une seule fois (pas par bien).

- [ ] **Step 2: Ajouter le bloc fiscal à l'extraction**

Dans la fonction d'extraction, après la collecte par propriété, ajouter un appel unique à `/api/fiscal/timeline` et ranger son `results` sous une clé `"fiscal"` du dict golden (arrondi au centime comme le reste, clés triées). Respecter le format existant (voir comment les autres blocs sont normalisés/arrondis dans le fichier).

- [ ] **Step 3: Régénérer et comparer**

Run:
```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
python3 backend/scripts/golden_master.py --extract --tag v9-avec-fiscal
python3 backend/scripts/golden_master.py --compare --tag v8-avant-nettoyage
```
Expected: la comparaison à v8 montre l'**ajout** du bloc fiscal (nouvelles clés) et **aucune modification** des chiffres existants (produits/charges/bilan des 3 biens inchangés).

- [ ] **Step 4: Lancer la suite complète**

Run: `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/ -q -p no:cacheprovider`
Expected: tous verts (hors le rouge assumé `test_solde_marseille_golden` du garde-fou solde Marseille, sans rapport).

- [ ] **Step 5: Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/scripts/golden_master.py docs/project/reference/golden/golden-v9-avec-fiscal.json
git commit -m "[REFONTE] test: golden master étendu au bloc fiscal (non-régression)"
```

---

## Résultat livré par ce plan

Un moteur fiscal complet, validé contre les liasses réelles, exposé en API, non-régressé par le golden master. Il calcule pour chaque exercice : réintégration, déficit reportable, amortissements reportés, imputations, résultat fiscal imposable, et les stocks cumulés — au niveau entité, sans aucune donnée en dur, avec durées de report configurables.

**Non couvert (sous-projets suivants, plans séparés)** : le fichier de référence liasse (sous-projet 2) et l'affichage — page d'accueil + carte de réconciliation avec commentaires d'écart (sous-projet 3). Le forecast fiscal et la génération du CERFA restent hors périmètre global.
