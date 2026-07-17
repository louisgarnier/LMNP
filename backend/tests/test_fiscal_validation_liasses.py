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
