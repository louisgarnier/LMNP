"""Bilan au niveau ENTITÉ, dans la forme du CERFA 2033-A.

Le bilan de l'application est calculé par appartement. La liasse, elle, est
déposée pour l'entité entière. Pour vérifier la liasse ligne à ligne, il faut
donc agréger les biens et présenter le résultat dans la même forme que le
formulaire officiel.

Invariant non négociable : l'agrégation doit rester équilibrée. Si chaque bien
équilibre, la somme équilibre — ce test le verrouille, parce qu'une erreur de
signe dans le mapping le casserait silencieusement.
"""
import pytest

from backend.api.services.bilan_entite_service import agreger_bilans, MAPPING_CERFA


def _bilan(actif, passif, categories):
    """Fabrique une réponse /api/bilan/calculate minimale."""
    return {
        "actif_total": actif,
        "passif_total": passif,
        "types": [
            {"type": "ACTIF", "total": actif, "sub_categories": [
                {"sub_category": "Actif immobilisé", "total": actif, "categories": [
                    {"category_name": n, "amount": m} for n, m in categories.get("ACTIF", [])
                ]},
            ]},
            {"type": "PASSIF", "total": passif, "sub_categories": [
                {"sub_category": "Capitaux propres", "total": passif, "categories": [
                    {"category_name": n, "amount": m} for n, m in categories.get("PASSIF", [])
                ]},
            ]},
        ],
    }


BIEN_A = _bilan(1000.0, 1000.0, {
    "ACTIF": [("Immobilisations", 1200.0), ("Amortissements cumulés", -300.0), ("Compte bancaire", 100.0)],
    "PASSIF": [("Compte courant d'associé", 400.0), ("Emprunt bancaire (capital restant dû)", 600.0)],
})
BIEN_B = _bilan(500.0, 500.0, {
    "ACTIF": [("Immobilisations", 800.0), ("Amortissements cumulés", -400.0), ("Compte bancaire", 100.0)],
    "PASSIF": [("Compte courant d'associé", 200.0), ("Emprunt bancaire (capital restant dû)", 300.0)],
})


class TestAgregation:
    def test_additionne_les_categories_de_meme_nom(self):
        r = agreger_bilans([BIEN_A, BIEN_B])
        assert r["categories"]["Immobilisations"] == pytest.approx(2000.0, abs=0.01)
        assert r["categories"]["Amortissements cumulés"] == pytest.approx(-700.0, abs=0.01)
        assert r["categories"]["Compte courant d'associé"] == pytest.approx(600.0, abs=0.01)

    def test_additionne_les_totaux(self):
        r = agreger_bilans([BIEN_A, BIEN_B])
        assert r["actif_total"] == pytest.approx(1500.0, abs=0.01)
        assert r["passif_total"] == pytest.approx(1500.0, abs=0.01)

    def test_l_agregation_reste_equilibree(self):
        """L'invariant du bilan : si chaque bien équilibre, la somme équilibre."""
        r = agreger_bilans([BIEN_A, BIEN_B])
        assert abs(r["actif_total"] - r["passif_total"]) < 0.01

    def test_un_bien_absent_de_l_exercice_ne_perturbe_rien(self):
        vide = _bilan(0.0, 0.0, {})
        r = agreger_bilans([BIEN_A, vide])
        assert r["actif_total"] == pytest.approx(1000.0, abs=0.01)

    def test_aucun_bilan_ne_fait_pas_planter(self):
        r = agreger_bilans([])
        assert r["actif_total"] == 0.0
        assert r["categories"] == {}


class TestFormeCerfa:
    def test_chaque_ligne_cerfa_porte_sa_case(self):
        for ligne in MAPPING_CERFA:
            assert ligne["case"], f"ligne sans case : {ligne['libelle']}"
            assert ligne["bloc"] in ("ACTIF", "PASSIF")

    def test_les_lignes_attendues_de_la_liasse_sont_couvertes(self):
        libelles = {l["cle_liasse"] for l in MAPPING_CERFA if l["cle_liasse"]}
        attendus = {
            "immobilisations_brut", "amortissements_cumules", "actif_total",
            "capital_individuel", "emprunt_capital_restant_du", "passif_total",
        }
        assert attendus <= libelles, attendus - libelles

    def test_le_compte_courant_a_sa_ligne_meme_si_la_liasse_ne_la_porte_pas(self):
        """Louis a injecté des fonds personnels : la ligne doit exister côté app,
        même quand la case 173 de la liasse est vide."""
        cca = [l for l in MAPPING_CERFA if l["case"] == "173"]
        assert len(cca) == 1
        assert cca[0]["cle_liasse"] is None  # rien à comparer tant que la liasse est vide


class TestLesDeuxFormesDeBilan:
    """`calculate_bilan()` renvoie un dict plat, la route renvoie un arbre.
    Les deux circulent dans le code : l'agrégation doit lire les deux, sinon
    les totaux sont justes mais toutes les lignes tombent à zéro."""

    PLAT = {
        "actif_total": 1000.0, "passif_total": 1000.0,
        "categories": {"Immobilisations": 1200.0, "Amortissements cumulés": -300.0,
                       "Compte bancaire": 100.0, "Compte courant d'associé": 400.0,
                       "Emprunt bancaire (capital restant dû)": 600.0},
    }

    def test_lit_la_forme_plate_du_service(self):
        r = agreger_bilans([self.PLAT])
        assert r["categories"]["Immobilisations"] == pytest.approx(1200.0, abs=0.01)
        assert r["categories"]["Compte courant d'associé"] == pytest.approx(400.0, abs=0.01)

    def test_les_deux_formes_donnent_le_meme_resultat(self):
        plat = agreger_bilans([self.PLAT])
        arbre = agreger_bilans([BIEN_A])
        assert plat["categories"] == pytest.approx(arbre["categories"])
        assert plat["actif_total"] == pytest.approx(arbre["actif_total"], abs=0.01)

    def test_melanger_les_deux_formes_fonctionne(self):
        r = agreger_bilans([self.PLAT, BIEN_B])
        assert r["categories"]["Immobilisations"] == pytest.approx(2000.0, abs=0.01)
        assert r["actif_total"] == pytest.approx(1500.0, abs=0.01)
