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


def test_2024_annee_conforme_mais_stock_deficit_herite_de_l_anomalie():
    # Les chiffres PROPRES à 2024 collent au cabinet (produits, résultat,
    # amortissements, déficit de l'exercice, imposable) aux arrondis près.
    db = _ROSession()
    try:
        r = reconcile(db)[2024]
    finally:
        db.close()
    for poste in ("Produits", "Résultat comptable", "Amortissements",
                  "Déficit de l'exercice", "Résultat fiscal imposable"):
        ligne = next(l for l in r["lignes"] if l["poste"] == poste)
        assert ligne["ok"] is True, f"{poste} en écart: {ligne['ecart']}"
    # MAIS le déficit reportable cumulé hérite de l'anomalie 2023 (~-3462) :
    # l'appli a imputé le bénéfice 2023, pas le cabinet (source aide_au_report).
    cumul = next(l for l in r["lignes"] if l["poste"] == "Déficit reportable (cumulé)")
    assert cumul["ok"] is False
    assert cumul["ecart"] == pytest.approx(-3461.90, abs=1.0)


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


def test_per_bien_cr_groupe_les_charges():
    from backend.api.services.reconciliation_service import _per_bien_cr
    db = _ROSession()
    try:
        cr = _per_bien_cr(db, 2025)
    finally:
        db.close()
    evry = cr[25]
    # clés attendues
    assert set(evry) == {"produits", "charges_externes", "impots", "amortissements", "interets", "resultat"}
    # 2025 Evry (valeurs réelles connues, signe charges = négatif)
    assert evry["produits"] == pytest.approx(23803.02, abs=1.0)
    assert evry["impots"] == pytest.approx(-2323, abs=1.0)
    assert evry["amortissements"] == pytest.approx(-11119, abs=1.0)
    assert evry["interets"] == pytest.approx(-2489, abs=1.0)
    # charges externes = toutes charges hors impôts/amort/intérêts
    assert evry["charges_externes"] == pytest.approx(-11263, abs=2.0)
    # cohérence : produits + charges_externes + impots + amortissements + interets == resultat
    somme = (evry["produits"] + evry["charges_externes"] + evry["impots"]
             + evry["amortissements"] + evry["interets"])
    assert somme == pytest.approx(evry["resultat"], abs=0.5)


def test_lignes_groupees_2025_signe_et_ecart(rec):
    lignes = {l["poste"]: l for l in rec[2025]["lignes"]}
    assert set(lignes) >= {"Produits", "Charges externes", "Impôts et taxes",
                           "Amortissements", "Intérêts d'emprunt", "Résultat comptable",
                           "Déficit reportable (cumulé)", "Amortissements reportés (cumulé)"}
    # charges externes : app négatif, comparé à −liasse, écart ~0
    ce = lignes["Charges externes"]
    assert ce["app"] == pytest.approx(-40278, abs=2.0)
    assert ce["liasse"] == pytest.approx(-40278, abs=2.0)
    assert ce["ok"] is True
    # intérêts : l'erreur cabinet de 64 €
    it = lignes["Intérêts d'emprunt"]
    assert it["ok"] is False
    assert abs(it["ecart"]) == pytest.approx(64, abs=2.0)
    # somme par bien = total app sur chaque ligne comptable
    for poste in ("Produits", "Charges externes", "Résultat comptable"):
        l = lignes[poste]
        assert round(sum(l["par_bien"].values()), 2) == pytest.approx(l["app"], abs=0.5)


def test_reconcile_expose_cr_par_bien(rec):
    assert "charges_externes" in rec[2025]["cr_par_bien"][25]


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
