"""Trois données du document de référence des tirelires, jusqu'ici calculées
mais jamais exposées :

  1. les MILLÉSIMES du déficit (quel euro est né quand, quand il meurt) ;
  2. l'amortissement DÉJÀ DÉDUIT en cumul ;
  3. l'échéancier de péremption qui en découle.

Sans elles, l'onglet « Ce qui expire » et le découpage par bien ne peuvent pas
exister. Voir docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md.
"""
import pytest

from backend.api.services.fiscal_service import compute_fiscal_timeline


def _annee(year, resultat_comptable, amortissements):
    return {"year": year, "resultat_comptable": resultat_comptable,
            "amortissements": amortissements}


# Scénario calqué sur la réalité de Louis : deux exercices en perte, puis un
# gros bénéfice qui puise dans une tirelire.
SCENARIO = [
    _annee(2021, -24729.17, 632.49),    # r_ha < 0  -> les deux tirelires se remplissent
    _annee(2022, -4410.58, 10350.94),   # r_ha > 0 mais < amort
    _annee(2023, 4061.59, 11119.15),    # r_ha > amort -> on puise
]


class TestMillesimesDeficit:
    def test_chaque_perte_cree_un_millesime_date(self):
        # mode "amort" : le bénéfice 2023 puise dans l'autre tirelire, le
        # millésime déficit reste donc intact à sa valeur d'origine.
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {2023: "amort"})
        mill = tl[2023]["deficit_millesimes"]
        assert [m["annee"] for m in mill] == [2021]
        assert mill[0]["montant"] == pytest.approx(24096.68, abs=0.01)

    def test_le_millesime_est_entame_si_le_deficit_est_impute(self):
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {2023: "deficit"})
        mill = tl[2023]["deficit_millesimes"]
        # 24 096,68 − 4 061,59 de bénéfice imputé
        assert mill[0]["montant"] == pytest.approx(20035.09, abs=0.01)

    def test_le_millesime_porte_son_annee_de_peremption(self):
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {})
        assert tl[2023]["deficit_millesimes"][0]["expire_fin"] == 2031

    def test_la_duree_de_report_pilote_la_peremption(self):
        tl = compute_fiscal_timeline(SCENARIO, 5, None, {})
        assert tl[2023]["deficit_millesimes"][0]["expire_fin"] == 2026

    def test_un_millesime_consomme_disparait(self):
        # mode "deficit" : le bénéfice 2023 attaque le déficit le plus ancien
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {2023: "deficit"})
        restant = sum(m["montant"] for m in tl[2023]["deficit_millesimes"])
        assert restant == pytest.approx(tl[2023]["stock_deficit_fin"], abs=0.01)
        assert restant < 24096.68  # une partie a servi

    def test_fifo_le_plus_ancien_part_en_premier(self):
        scenario = SCENARIO + [
            _annee(2024, -20032.0, 14553.0),   # nouveau millésime 2024
            _annee(2025, 30000.0, 1000.0),     # gros bénéfice
        ]
        tl = compute_fiscal_timeline(scenario, 10, None, {2025: "deficit"})
        restants = {m["annee"]: m["montant"] for m in tl[2025]["deficit_millesimes"]}
        # 2021 doit avoir été servi avant 2024 : il ne reste que du 2024, ou rien
        assert 2021 not in restants


class TestAmortDejaDeduit:
    def test_cumul_deduit_vaut_zero_tant_quon_est_en_perte(self):
        tl = compute_fiscal_timeline(SCENARIO[:1], 10, None, {})
        assert tl[2021]["amort_deduit_cumul"] == pytest.approx(0.0, abs=0.01)

    def test_cumul_deduit_additionne_deduction_directe_et_puisage(self):
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {2023: "amort"})
        # 2022 : 5 940,36 déduits directement ; 2023 : 11 119,15 directs + 4 061,59 puisés
        attendu = 5940.36 + 11119.15 + 4061.59
        assert tl[2023]["amort_deduit_cumul"] == pytest.approx(attendu, abs=0.02)

    def test_total_amorti_egale_deduit_plus_tirelire(self):
        """L'identité qui fonde tout le raisonnement de la revente."""
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {2023: "amort"})
        total_amorti = sum(a["amortissements"] for a in SCENARIO)
        r = tl[2023]
        assert r["amort_deduit_cumul"] + r["stock_amort_fin"] == pytest.approx(
            total_amorti, abs=0.02)

    def test_identite_verifiee_sur_chaque_exercice(self):
        tl = compute_fiscal_timeline(SCENARIO, 10, None, {})
        cumul_amorti = 0.0
        for a in SCENARIO:
            cumul_amorti += a["amortissements"]
            r = tl[a["year"]]
            assert r["amort_deduit_cumul"] + r["stock_amort_fin"] == pytest.approx(
                cumul_amorti, abs=0.02), f"identité rompue en {a['year']}"


class TestEcheancier:
    def test_echeancier_trie_du_plus_urgent_au_plus_lointain(self):
        scenario = SCENARIO + [_annee(2024, -20032.0, 14553.0),
                               _annee(2025, -31338.22, 20337.59)]
        tl = compute_fiscal_timeline(scenario, 10, None, {2023: "amort"})
        mill = tl[2025]["deficit_millesimes"]
        annees = [m["expire_fin"] for m in mill]
        assert annees == sorted(annees), "le plus urgent doit venir en premier"
        assert annees[0] == 2031
