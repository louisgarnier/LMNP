"""Chaque écart avec la liasse doit porter son explication.

Un écart non expliqué est inexploitable : on ne sait pas s'il faut corriger
l'application, écrire au cabinet, ou ne rien faire. Les explications sont des
résultats d'enquête — elles ne se déduisent d'aucun calcul — donc elles vivent
dans les fichiers `liasse-YYYY.json`, à côté des montants qu'elles commentent.

Quatre statuts :
  erreur_cabinet          le cabinet s'est trompé, à faire régulariser
  difference_presentation même réalité, rangée autrement — rien à corriger
  difference_date         décalage de date de mise en service, converge seul
  a_investiguer           on ne sait pas encore
"""
import json
import pytest
from pathlib import Path

from backend.api.services.ecarts_service import (
    STATUTS, explication_cr, explication_bilan, charger_explications,
)

LIASSES = Path(__file__).resolve().parents[2] / "docs" / "project" / "reference" / "liasses"


class TestStatuts:
    def test_les_quatre_statuts_existent(self):
        assert set(STATUTS) == {
            "erreur_cabinet", "difference_presentation", "difference_date", "a_investiguer"
        }

    def test_chaque_statut_a_un_libelle_et_une_couleur(self):
        for cle, s in STATUTS.items():
            assert s["libelle"], cle
            assert s["ton"] in ("rouge", "neutre", "info"), cle


class TestLectureDesFichiers:
    def test_une_liasse_sans_explications_ne_plante_pas(self):
        assert charger_explications({}) == {"cr": {}, "bilan": {}}

    def test_les_explications_sont_lues_par_poste(self):
        liasse = {"ecarts_expliques": {
            "cr": {"Intérêts d'emprunt": {"statut": "erreur_cabinet", "cause": "essai"}},
            "bilan": {"156": {"statut": "erreur_cabinet", "cause": "essai"}},
        }}
        e = charger_explications(liasse)
        assert e["cr"]["Intérêts d'emprunt"]["statut"] == "erreur_cabinet"
        assert e["bilan"]["156"]["cause"] == "essai"

    def test_un_statut_inconnu_est_refuse(self):
        liasse = {"ecarts_expliques": {"cr": {"X": {"statut": "n_importe_quoi", "cause": "c"}}}}
        with pytest.raises(ValueError, match="statut inconnu"):
            charger_explications(liasse)


class TestResolution:
    LIASSE = {"ecarts_expliques": {
        "cr": {"Intérêts d'emprunt": {"statut": "erreur_cabinet", "cause": "sous-évalué de 63,68 €"}},
        "bilan": {"156": {"statut": "erreur_cabinet", "cause": "crédits Marseille absents"}},
    }}

    def test_un_poste_explique_renvoie_sa_cause(self):
        e = explication_cr(self.LIASSE, "Intérêts d'emprunt")
        assert e["statut"] == "erreur_cabinet"
        assert "63,68" in e["cause"]
        assert e["ton"] == "rouge"

    def test_un_poste_sans_explication_renvoie_None(self):
        assert explication_cr(self.LIASSE, "Produits") is None

    def test_le_bilan_se_resout_par_numero_de_case(self):
        e = explication_bilan(self.LIASSE, "156")
        assert "Marseille" in e["cause"]

    def test_absence_de_liasse_renvoie_None(self):
        assert explication_cr(None, "Produits") is None
        assert explication_bilan(None, "156") is None


class TestFichiersReels:
    """Les écarts déjà instruits doivent être encodés dans les liasses."""

    def _liasse(self, annee):
        f = LIASSES / f"liasse-{annee}.json"
        return json.loads(f.read_text(encoding="utf-8"))

    def test_les_63_euros_de_charges_financieres_2025_sont_expliques(self):
        e = explication_cr(self._liasse(2025), "Intérêts d'emprunt")
        assert e is not None, "l'écart de 63,68 € doit porter son explication"
        assert e["statut"] == "erreur_cabinet"

    def test_les_emprunts_manquants_2025_sont_expliques(self):
        e = explication_bilan(self._liasse(2025), "156")
        assert e is not None
        assert e["statut"] == "erreur_cabinet"

    def test_le_capital_individuel_est_marque_difference_de_presentation(self):
        e = explication_bilan(self._liasse(2025), "120")
        assert e is not None
        assert e["statut"] == "difference_presentation"

    def test_les_ecarts_2021_sont_expliques_par_la_date_des_travaux(self):
        e = explication_cr(self._liasse(2021), "Résultat comptable")
        assert e is not None
        assert e["statut"] == "difference_date"

    def test_toutes_les_liasses_ont_des_explications_valides(self):
        for annee in (2021, 2022, 2023, 2024, 2025):
            charger_explications(self._liasse(annee))  # ne doit pas lever
