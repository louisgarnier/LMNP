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


def test_2023_resultat_fiscal_app_et_officiel(chain):
    # 2023 est bénéficiaire : rappel officiel du résultat fiscal = +4077
    # (résultat comptable + amort réintégrés), pas 0.
    l = chain["chain"][2023]
    assert l["resultat_fiscal_officiel"] == pytest.approx(4077, abs=1.0)
    assert l["resultat_fiscal_app"] == pytest.approx(4062, abs=3.0)
