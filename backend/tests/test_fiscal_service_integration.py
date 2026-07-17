"""
Tests d'intégration du moteur fiscal (Task 4) — agrégation entité + get_fiscal.

⚠️ Ce module lit la base de PRODUCTION en LECTURE SEULE (mode=ro), via un
engine SQLite dédié — PAS `backend.database.SessionLocal` : la quarantaine
étape 2 (ADR-007, voir docs/workflow/ERROR_INVESTIGATION.md, incident
2026-07-12) lève une RuntimeError sur toute connexion via le moteur de
production tant que LMNP_ALLOW_PROD_DB_TESTS != "1", pour empêcher toute
écriture accidentelle. `entity_year_inputs`/`calculate_compte_resultat` ne
font que des lectures (aucun .add/.commit/.delete), donc un engine `mode=ro`
suffit et reproduit le pattern déjà utilisé par les tests golden
(`test_amortization_evry_golden.py`).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.services.fiscal_service import (
    entity_year_range, entity_year_inputs, get_fiscal_timeline, get_fiscal,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_DB_PATH = REPO_ROOT / "backend" / "database" / "lmnp.db"

C = 0.1


@pytest.fixture(scope="module")
def db():
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


def test_plage_annees_couvre_2021_a_lannee_courante(db):
    years = entity_year_range(db)
    assert years[0] == 2021
    assert 2025 in years


def test_inputs_entite_2024_somme_les_biens(db):
    row = entity_year_inputs(db, 2024)
    # entité 2024 = Evry + Marseille abnb (après reclassement des 600€)
    assert row["resultat_comptable"] == pytest.approx(-20031.64, abs=1.0)
    assert row["amortissements"] == pytest.approx(14552.52, abs=1.0)


def test_get_fiscal_2024_reproduit_la_liasse(db):
    out = get_fiscal(db, 2024)
    assert out["deficit_annee"] == pytest.approx(5479.12, abs=1.0)
    assert out["resultat_fiscal_imposable"] == pytest.approx(0.0, abs=C)
