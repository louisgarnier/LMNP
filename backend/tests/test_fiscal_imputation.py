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
    # Stock amort 2022 : r_ha=3000 plafonne le déductible à 3000, donc
    # amort_differe_annee = 8000-3000 = 5000 (>= bénéfice 2023, tout y passe).
    assert r["imputation_amorts"] == 4000.0     # bénéfice 2023 absorbé par le stock amort
    assert r["imputation_deficits"] == 0.0      # rien ne reste pour le déficit
    assert r["imputation_mode"] == "amort"


def test_choix_sur_annee_non_beneficiaire_est_ignore():
    # 2021 est en perte : le mode 'amort' n'a aucun effet, pas d'imputation.
    r = _timeline({2021: "amort"})[2021]
    assert r["imputation_deficits"] == 0.0
    assert r["imputation_amorts"] == 0.0
