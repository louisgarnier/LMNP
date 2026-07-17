"""Tests du service de réconciliation appli vs liasses déposées.

Lecture seule sur la base réelle via un engine `?mode=ro` (motif sanctionné,
cf. test_fiscal_service_integration.py) : le service et les liasses de référence
sont validés contre les vraies données. La garde de quarantaine prod n'est pas
touchée (engine distinct de backend.database.connection.engine).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.services.reconciliation_service import reconcile, load_liasses

PROD_DB = (Path(__file__).parent.parent / "database" / "lmnp.db").resolve()
_ro_engine = create_engine(f"sqlite:///file:{PROD_DB}?mode=ro&uri=true",
                           connect_args={"uri": True})
_ROSession = sessionmaker(bind=_ro_engine)


@pytest.fixture
def rec():
    db = _ROSession()
    try:
        yield reconcile(db)
    finally:
        db.close()


def test_les_5_liasses_sont_chargees():
    liasses = load_liasses()
    assert set(liasses) == {2021, 2022, 2023, 2024, 2025}
    assert liasses[2024]["biens_inclus"] == [25, 15]


def test_2024_reconcilie_sans_ecart():
    # 2024 colle au comptable (aux arrondis euros entiers près) : 0 écart.
    db = _ROSession()
    try:
        r = reconcile(db)[2024]
    finally:
        db.close()
    assert r["nb_ecarts"] == 0
    # Aucune ligne en écart (ok=False). Certaines lignes ne sont pas comparées
    # (ok=None, ex. déficit reportable cumulé que la liasse 2024 n'imprime pas) :
    # c'est admis, seul False signale un vrai écart.
    for ligne in r["lignes"]:
        assert ligne["ok"] is not False, f"{ligne['poste']} en écart: {ligne['ecart']}"


def test_2025_pointe_l_erreur_interets_du_cabinet(rec):
    # Le déficit de l'exercice diverge de ~64 € (intérêts colloc sous-évalués).
    r = rec[2025]
    deficit = next(l for l in r["lignes"] if l["poste"] == "Déficit de l'exercice")
    assert not deficit["ok"]
    assert deficit["ecart"] == pytest.approx(63.63, abs=0.5)


def test_2021_composition_signale_les_travaux_dates_2021(rec):
    # L'appli immobilise ~36 116 € de travaux en 2021 que la liasse a placés en
    # 2022 : la composition doit le signaler (immo appli > immo liasse).
    r = rec[2021]
    comp = r["composition"]
    assert not comp["ok"]
    assert comp["ecart"] == pytest.approx(36115.83, abs=1.0)


def test_toutes_les_annees_ont_un_imposable_conforme(rec):
    # Résultat fiscal imposable = 0 partout, appli ET liasse.
    for year in (2021, 2022, 2023, 2024, 2025):
        imposable = next(l for l in rec[year]["lignes"]
                         if l["poste"] == "Résultat fiscal imposable")
        assert imposable["ok"]
        assert imposable["app"] == pytest.approx(0.0, abs=0.01)


def test_detail_par_bien_2025_somme_egale_total(rec):
    # Les lignes comptables sont ventilées par bien ; la somme = total appli.
    produits = next(l for l in rec[2025]["lignes"] if l["poste"] == "Produits")
    assert produits["par_bien"] is not None
    assert set(produits["par_bien"]) == {25, 15, 26}
    assert round(sum(produits["par_bien"].values()), 2) == produits["app"]
    # Ligne fiscale = entité, pas de ventilation.
    deficit = next(l for l in rec[2025]["lignes"] if l["poste"] == "Déficit de l'exercice")
    assert deficit["par_bien"] is None


def test_2026_est_un_brouillon_sans_liasse(rec):
    # L'exercice en cours (2026) apparaît en brouillon : chiffres appli, pas de
    # liasse ni d'écart.
    assert 2026 in rec
    r = rec[2026]
    assert r["brouillon"] is True
    assert r["nb_ecarts"] == 0
    for ligne in r["lignes"]:
        assert ligne["liasse"] is None
        assert ligne["ecart"] is None
