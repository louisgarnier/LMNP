"""
Golden dotations Evry — validation des amortissements recalculés contre le
tableau d'immobilisations documentaire.

Source de vérité : docs/files/appartements/Evry/Immobilisations_Evry.pdf
(page 1). Ce test lit la base de PRODUCTION en LECTURE SEULE (mode=ro), via
un engine dédié — PAS le harnais mémoire (conftest) : il valide l'état RÉEL
de la base après passage de backend/scripts/fix_amortization_evry.py.

⚠️ Pourquoi un engine dédié et NON le sessionmaker de production :
- La quarantaine conftest (pytest_collection_modifyitems) saute tout module
  de test dont la source référence le sessionmaker de prod ou consomme
  manuellement le générateur get_db, pour éviter les écritures accidentelles
  sur la prod (c'est pourquoi ce docstring évite d'écrire ces motifs
  littéralement). On veut que CE module s'exécute — on ouvre donc la prod via
  un engine SQLite `mode=ro` (write physiquement impossible, cf.
  test_prod_db_is_read_only) et on nomme le sessionmaker `ReadOnlySession`.
- Résolution du chemin via Path(__file__) -> résiliente au cwd (repo root
  ou backend/).

Contrainte de tolérance (plan Bloc A) : chiffres 2023-2025 = référence au
centime ; écart 2021/2022 vs comptable toléré (les proratas de première
année dépendent de dates de transactions qui diffèrent des lignes
documentaires — hors périmètre du centime).
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_DB_PATH = REPO_ROOT / "backend" / "database" / "lmnp.db"

TOLERANCE = 0.01
EVRY_PROPERTY_ID = 25
MARSEILLE_PROPERTY_ID = 15

# ---------------------------------------------------------------------------
# Vérité documentaire — Immobilisations_Evry.pdf, page 1
# ---------------------------------------------------------------------------
# Annuité pleine par regroupement comptable :
EVRY_CONSTRUCTION_ANNUITE = 115_500.00 / 30          # compte 21300000 -> 3 850,00
EVRY_INSTALLATIONS_ANNUITE = 72_691.48 / 10          # compte 21810000 -> 7 269,148
EVRY_TOTAL_ANNUITE = EVRY_CONSTRUCTION_ANNUITE + EVRY_INSTALLATIONS_ANNUITE  # 11 119,148
EVRY_AMORTIZABLE_BASE = 188_191.48                   # 237 691,48 - 49 500 (terrain)

# Années « pleines » (aucun prorata) => référence au centime.
EVRY_FULL_YEARS = (2023, 2024, 2025)

# Marseille (property 15) — Tablea_Immo_Mars_abnb.xlsx : annuités par catégorie.
MARSEILLE_ANNUITES = {
    "Immobilisation structure/GO": 807.50,       # 40 375 / 50
    "Immobilisation mobilier": 750.62,           # 3 753,09 / 5
    "Immobilisation IGT": 1076.67,               # 16 150 / 15
    "Immobilisation agencements": 1615.00,       # 8 075 / 5
    "Immobilisation Facade/Toiture": 807.50,     # 16 150 / 20
    "Immobilisation travaux": 1100.00,           # 22 000 / 20
}
MARSEILLE_FULL_YEAR = 2025


@pytest.fixture(scope="module")
def ro_session():
    """Session SQLAlchemy en LECTURE SEULE sur la base de prod."""
    if not PROD_DB_PATH.exists():
        pytest.skip(f"Base de prod introuvable: {PROD_DB_PATH}")
    url = f"sqlite:///file:{PROD_DB_PATH}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"uri": True})
    ReadOnlySession = sessionmaker(bind=engine)
    session = ReadOnlySession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_prod_db_is_read_only(ro_session):
    """Garde-fou : l'engine ne DOIT PAS pouvoir écrire dans la prod."""
    with pytest.raises(OperationalError):
        ro_session.execute(
            text("DELETE FROM amortization_results WHERE id = -1")
        )
        ro_session.commit()


def _dotation_by_year(session, property_id):
    """{année: somme des dotations} pour une propriété (via jointure transaction)."""
    rows = session.execute(
        text(
            """
            SELECT ar.year, SUM(ar.amount)
            FROM amortization_results ar
            JOIN transactions t ON t.id = ar.transaction_id
            WHERE t.property_id = :pid
            GROUP BY ar.year
            """
        ),
        {"pid": property_id},
    ).all()
    return {int(y): float(s) for y, s in rows}


def _dotation_by_category_year(session, property_id, year):
    """{catégorie: dotation} pour une propriété et une année données."""
    rows = session.execute(
        text(
            """
            SELECT ar.category, SUM(ar.amount)
            FROM amortization_results ar
            JOIN transactions t ON t.id = ar.transaction_id
            WHERE t.property_id = :pid AND ar.year = :year
            GROUP BY ar.category
            """
        ),
        {"pid": property_id, "year": year},
    ).all()
    return {c: float(s) for c, s in rows}


def _grand_total(session, property_id):
    total = session.execute(
        text(
            """
            SELECT SUM(ar.amount)
            FROM amortization_results ar
            JOIN transactions t ON t.id = ar.transaction_id
            WHERE t.property_id = :pid
            """
        ),
        {"pid": property_id},
    ).scalar()
    return float(total or 0.0)


# ---------------------------------------------------------------------------
# Evry — cœur du test (référence au centime)
# ---------------------------------------------------------------------------

def test_evry_types_realignes_sur_le_document(ro_session):
    """Les 4 types Evry doivent mapper les bonnes catégories level_1 et durées
    (aucun type orphelin level_1_values == [])."""
    rows = ro_session.execute(
        text(
            "SELECT name, level_1_values, duration FROM amortization_types "
            "WHERE property_id = :pid"
        ),
        {"pid": EVRY_PROPERTY_ID},
    ).all()
    mapping = {}
    for name, lv1, dur in rows:
        values = json.loads(lv1 or "[]")
        assert values, f"Type orphelin (level_1_values vide): {name!r}"
        assert len(values) == 1, f"Type {name!r} mappe plusieurs level_1: {values}"
        mapping[values[0]] = dur

    assert mapping == {
        "Terrain (non amortissable)": 0.0,
        "Immeuble (hors terrain)": 30.0,
        "Travaux de rénovation, gros œuvre": 10.0,
        "Mobilier & électroménager": 10.0,
    }


def test_evry_terrain_non_amorti(ro_session):
    """La part terrain (Terrain non amortissable) ne produit AUCUN résultat."""
    n = ro_session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM amortization_results ar
            JOIN transactions t ON t.id = ar.transaction_id
            JOIN categories c ON c.id = t.category_id
            WHERE t.property_id = :pid
              AND c.label = 'Terrain (non amortissable)'
            """
        ),
        {"pid": EVRY_PROPERTY_ID},
    ).scalar()
    assert n == 0


def test_evry_dotation_annuelle_pleine_au_centime(ro_session):
    """Années pleines (2023-2025) : dotation totale == 11 119,148 €/an (doc)."""
    by_year = _dotation_by_year(ro_session, EVRY_PROPERTY_ID)
    for year in EVRY_FULL_YEARS:
        assert year in by_year, f"Aucune dotation Evry pour {year}"
        assert abs(abs(by_year[year]) - EVRY_TOTAL_ANNUITE) <= TOLERANCE, (
            f"Evry {year}: dotation {by_year[year]:.4f} != "
            f"annuité document {-EVRY_TOTAL_ANNUITE:.4f}"
        )


def test_evry_dotation_par_regroupement_comptable(ro_session):
    """Année pleine 2025 : construction (compte 21300000) == 3 850,00 et
    installations (compte 21810000, travaux + mobilier) == 7 269,148."""
    by_cat = _dotation_by_category_year(ro_session, EVRY_PROPERTY_ID, 2025)

    construction = by_cat.get("Immeuble (hors terrain)")
    assert construction is not None, f"Catégorie construction absente: {by_cat}"
    assert abs(abs(construction) - EVRY_CONSTRUCTION_ANNUITE) <= TOLERANCE

    installations = sum(
        v for k, v in by_cat.items() if k != "Immeuble (hors terrain)"
    )
    assert abs(abs(installations) - EVRY_INSTALLATIONS_ANNUITE) <= TOLERANCE


def test_evry_base_amortissable_totale(ro_session):
    """Somme de TOUTES les dotations (toutes années) == base amortissable
    documentaire 188 191,48 € (le montant s'amortit intégralement)."""
    total = _grand_total(ro_session, EVRY_PROPERTY_ID)
    assert abs(abs(total) - EVRY_AMORTIZABLE_BASE) <= TOLERANCE


# ---------------------------------------------------------------------------
# Marseille (15) — vérification croisée contre son xlsx (dans le périmètre :
# elle CONCORDE, donc on la verrouille). Colloc (26) : source ambiguë ->
# documentée dans le rapport / ECARTS.md, PAS testée ici (hors périmètre Evry).
# ---------------------------------------------------------------------------

def test_marseille_dotations_conformes_xlsx(ro_session):
    """Marseille (15), année pleine 2025 : chaque catégorie == annuité xlsx."""
    by_cat = _dotation_by_category_year(ro_session, MARSEILLE_PROPERTY_ID, MARSEILLE_FULL_YEAR)
    for category, annuite in MARSEILLE_ANNUITES.items():
        assert category in by_cat, f"Marseille: catégorie absente {category!r}"
        assert abs(abs(by_cat[category]) - annuite) <= TOLERANCE, (
            f"Marseille {category!r}: {by_cat[category]:.2f} != xlsx {-annuite:.2f}"
        )
