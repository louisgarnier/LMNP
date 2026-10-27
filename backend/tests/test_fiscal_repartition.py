"""Découpage de la tirelire amortissements par appartement.

Les trois chiffres — total amorti, déjà déduit, encore en tirelire — sont
calculés au niveau ENTITÉ par le moteur fiscal. Pour la revente, il faut les
ventiler bien par bien.

Règle d'attribution du DÉDUIT : l'amortissement déduit une année-là est
attribué aux biens qui amortissaient cette année-là.
  - un seul bien actif  -> attribution EXACTE, aucune convention
  - plusieurs biens     -> prorata de leur amortissement de l'année, et on le
                           signale (`exact: False`) car c'est une convention.

Cf. docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md
"""
import pytest

from backend.api.services.fiscal_repartition_service import repartir_par_bien


# amort_par_bien : {property_id: {annee: montant amorti cette annee}}
# deduit_par_an  : {annee: montant reellement deduit au niveau entite}


class TestAttributionExacte:
    """Cas de Louis : les seules deductions sont tombees quand un seul bien existait."""

    AMORT = {
        25: {2021: 632.49, 2022: 10350.94, 2023: 11119.15, 2024: 11119.15, 2025: 11119.15},
        15: {2024: 3433.0, 2025: 6157.28},
        26: {2025: 3061.0},
    }
    DEDUIT = {2021: 0.0, 2022: 5940.36, 2023: 15180.74, 2024: 0.0, 2025: 0.0}

    def test_tout_le_deduit_revient_au_seul_bien_actif(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        assert r["exact"] is True
        assert r["biens"][25]["deduit"] == pytest.approx(5940.36 + 15180.74, abs=0.01)
        assert r["biens"][15]["deduit"] == pytest.approx(0.0, abs=0.01)
        assert r["biens"][26]["deduit"] == pytest.approx(0.0, abs=0.01)

    def test_le_total_amorti_par_bien_est_la_somme_de_ses_annees(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        assert r["biens"][25]["total"] == pytest.approx(sum(self.AMORT[25].values()), abs=0.01)
        assert r["biens"][15]["total"] == pytest.approx(9590.28, abs=0.01)

    def test_la_tirelire_par_bien_est_le_reste(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        for pid, b in r["biens"].items():
            assert b["tirelire"] == pytest.approx(b["total"] - b["deduit"], abs=0.01), pid

    def test_les_sommes_par_bien_retombent_sur_le_total_entite(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        total_attendu = sum(sum(v.values()) for v in self.AMORT.values())
        assert r["total"] == pytest.approx(total_attendu, abs=0.01)
        assert r["deduit"] == pytest.approx(sum(self.DEDUIT.values()), abs=0.01)
        assert sum(b["deduit"] for b in r["biens"].values()) == pytest.approx(r["deduit"], abs=0.01)
        assert sum(b["tirelire"] for b in r["biens"].values()) == pytest.approx(r["tirelire"], abs=0.01)


class TestAttributionAuProrata:
    """Des qu'une deduction tombe sur une annee a plusieurs biens, c'est une convention."""

    AMORT = {25: {2026: 3000.0}, 15: {2026: 1000.0}}
    DEDUIT = {2026: 800.0}

    def test_le_prorata_suit_le_poids_de_chaque_bien(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        assert r["biens"][25]["deduit"] == pytest.approx(600.0, abs=0.01)  # 3/4
        assert r["biens"][15]["deduit"] == pytest.approx(200.0, abs=0.01)  # 1/4

    def test_le_caractere_conventionnel_est_signale(self):
        r = repartir_par_bien(self.AMORT, self.DEDUIT)
        assert r["exact"] is False
        assert 2026 in r["annees_au_prorata"]

    def test_une_annee_sans_deduction_ne_rend_pas_le_calcul_conventionnel(self):
        r = repartir_par_bien(self.AMORT, {2026: 0.0})
        assert r["exact"] is True
        assert r["annees_au_prorata"] == []


class TestBordsEtRobustesse:
    def test_aucun_bien_ne_fait_pas_planter(self):
        r = repartir_par_bien({}, {})
        assert r["biens"] == {}
        assert r["total"] == 0.0

    def test_un_bien_sans_amortissement_reste_a_zero(self):
        r = repartir_par_bien({25: {2025: 100.0}, 15: {}}, {2025: 0.0})
        assert r["biens"][15]["total"] == 0.0
        assert r["biens"][15]["tirelire"] == 0.0

    def test_une_deduction_sur_une_annee_sans_amortissement_est_ignoree(self):
        # ne doit pas lever ni creer de division par zero
        r = repartir_par_bien({25: {2025: 100.0}}, {2024: 500.0})
        assert r["biens"][25]["deduit"] == pytest.approx(0.0, abs=0.01)

    def test_arret_a_une_annee_donnee(self):
        amort = {25: {2021: 100.0, 2022: 200.0, 2023: 400.0}}
        r = repartir_par_bien(amort, {2021: 0.0, 2022: 50.0, 2023: 300.0}, jusqua=2022)
        assert r["total"] == pytest.approx(300.0, abs=0.01)
        assert r["deduit"] == pytest.approx(50.0, abs=0.01)
