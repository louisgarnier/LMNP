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
