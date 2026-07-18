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
    # imputation_choices={} => défaut déficit-d'abord, déterministe (indépendant
    # de tout choix d'imputation persisté en base).
    db = _ROSession()
    try:
        yield build_chain(db, imputation_choices={})
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


def test_realized_naffecte_que_lannee_en_cours():
    # Réel vs Prévisionnel : résultat comptable identique sur toutes les années
    # CLOSES, différent uniquement sur l'année en cours (2026).
    db = _ROSession()
    try:
        reel = build_chain(db, realized=True, imputation_choices={})
        prev = build_chain(db, realized=False, imputation_choices={})
    finally:
        db.close()
    for y in (2021, 2022, 2023, 2024, 2025):
        assert reel["chain"][y]["resultat_comptable"] == pytest.approx(
            prev["chain"][y]["resultat_comptable"], abs=0.5), f"{y} devrait être identique Réel/Prévisionnel"
    # 2026 en cours : le Réel plafonne le coût du financement -> résultat distinct.
    assert abs(reel["chain"][2026]["resultat_comptable"]
               - prev["chain"][2026]["resultat_comptable"]) > 1.0


def test_imputation_override_bascule_les_tirelires_2023():
    # L'override d'imputation pilote la chaîne indépendamment de l'état persisté.
    db = _ROSession()
    try:
        deficit = build_chain(db, imputation_choices={})
        amort = build_chain(db, imputation_choices={2023: "amort"})
    finally:
        db.close()
    # déficit-d'abord : le bénéfice 2023 vide la tirelire déficit (~20035).
    assert deficit["chain"][2023]["deficit_fin_app"] == pytest.approx(20035, abs=2.0)
    assert deficit["chain"][2023]["mode"] == "deficit"
    # amort-d'abord : la tirelire déficit reste haute (~24097).
    assert amort["chain"][2023]["deficit_fin_app"] == pytest.approx(24097, abs=2.0)
    assert amort["chain"][2023]["mode"] == "amort"
