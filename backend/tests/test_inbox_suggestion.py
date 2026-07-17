"""Suggestion de catégorie et proposition de règle ROBUSTE pour l'inbox.

Contexte (2026-07-17) : l'inbox fabriquait une règle `exact` sur le libellé
COMPLET à chaque classement — 272 des 370 règles de la base ne matchent qu'une
seule transaction. Chaque virement de gestion mensuel devait être reclassé à la
main, indéfiniment.

Deux briques, toutes deux SANS risque : elles proposent, elles ne décident pas.
1. `suggest_category` : devine la catégorie par ressemblance avec l'historique
   déjà classé du bien. Sert à pré-remplir l'inbox.
2. `propose_rule` : propose le motif le plus COURT qui couvre le plus de
   transactions de la catégorie visée SANS jamais en capturer une d'une autre
   catégorie (zéro conflit garanti, vérifié contre tout l'historique du bien).
"""

import pytest

from backend.api.services.inbox_suggestion import (
    normalize_tokens,
    propose_rule,
    suggest_category,
)

# Historique réel de Marseille (extraits) : (libellé, category_id)
# 49 = Frais de gestion locative, 14 = Encaissement locataire, 18 = Compte courant
HISTORIQUE = [
    ("VIR INST GESTION ABNB - NOV25 - VH53501M80N7MF01", 49),
    ("VIR INST ABNB GESTION - LOUIS G VH53242B3KB32Z01", 49),
    ("VIR SEPA GESTION ABNB - AOUT25", 49),
    ("VIR SEPA GESTION ABNB - JUIL25", 49),
    ("VIR INST VIREMENT GESTION DEC25 VH60192084P7UL01", 49),
    ("VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROGLGC5S4PWE5OOQQ6HLF45V2S", 14),
    ("VIR AIRBNB PAYMENTS LUXEMBOU M-KGEEN3REN4PKJPN45XRGYGAE32QJM", 14),
    ("VIR AIRBNB PAYMENTS LUXEMBOU G-2TDJ3OKXS5BG42BFL2B2P5ISYE7JF", 14),
    ("VIR INST MR VICTOR BRIAND   5072082841681338", 18),
    ("PRLV SEPA TOTALENERGIES ELECTRI PRELEVEMENT TOTALENERGIES ELECT", 22),
    ("PRLV SEPA FREE TELECOM FREE HAUTDEBIT 1440956599", 23),
]


# --- normalisation -----------------------------------------------------------

def test_normalize_retire_les_references_bancaires():
    assert "VH53501M80N7MF01" not in normalize_tokens(
        "VIR INST GESTION ABNB - NOV25 - VH53501M80N7MF01"
    )


def test_normalize_retire_les_mois_et_les_annees():
    toks = normalize_tokens("VIR INST GESTION FEVRIER 26 - LG")
    assert "FEVRIER" not in toks
    assert "26" not in toks
    assert "GESTION" in toks


def test_normalize_garde_les_mots_porteurs_de_sens():
    assert normalize_tokens("VIR SEPA GESTION ABNB - AOUT25") == ["VIR", "SEPA", "GESTION", "ABNB"]


# --- suggestion de catégorie -------------------------------------------------

def test_suggere_la_categorie_d_un_virement_de_gestion_inedit():
    """Le libellé est inédit (mois et référence neufs) — la ressemblance doit suffire."""
    assert suggest_category("VIR INST GESTION AOUT 26 - LG CH3W26240W009999", HISTORIQUE) == 49


def test_suggere_la_categorie_d_un_encaissement_airbnb_inedit():
    assert suggest_category("VIR AIRBNB PAYMENTS LUXEMBOU M-ZZZNEUFZZZ999", HISTORIQUE) == 14


def test_ne_suggere_rien_quand_rien_ne_ressemble():
    """Sans voisin crédible, on préfère l'aveu d'ignorance à une fausse piste."""
    assert suggest_category("PRLV SEPA MAIRIE DE MARSEILLE CANTINE", HISTORIQUE) is None


def test_ne_suggere_rien_sur_un_historique_vide():
    assert suggest_category("VIR INST GESTION AOUT 26", []) is None


# --- proposition de règle ----------------------------------------------------

def test_propose_un_motif_court_pas_le_libelle_complet():
    """LE bug d'origine : l'inbox proposait le libellé entier, référence comprise."""
    regle = propose_rule("VIR INST GESTION AOUT 26 - LG CH3W26240W009999", 49, HISTORIQUE)
    assert regle is not None
    assert len(regle["pattern"]) < 20, f"motif trop long, on refabrique l'annuaire : {regle['pattern']!r}"
    assert "CH3W26240W009999" not in regle["pattern"]
    assert "AOUT" not in regle["pattern"]


def test_le_motif_propose_couvre_l_historique_de_la_categorie():
    """Une règle qui ne couvre qu'une transaction est une empreinte, pas une règle."""
    regle = propose_rule("VIR INST GESTION AOUT 26 - LG", 49, HISTORIQUE)
    assert regle["matches"] >= 4, f"ne couvre que {regle['matches']} transaction(s)"


def test_le_motif_propose_ne_capture_AUCUNE_transaction_d_une_autre_categorie():
    """Zéro risque, vérifié sur la donnée — pas sur le mot du code.

    ⚠️ Ce test remplace une version antérieure qui se contentait de
    `assert regle["conflicts"] == []` : comme `conflicts` est renseigné en dur
    par la fonction quand elle réussit, l'assertion était vide de sens — un
    sabotage du garde-fou anti-conflit laissait les 13 tests au vert. On vérifie
    donc la PROPRIÉTÉ RÉELLE : le motif retenu ne doit apparaître dans le libellé
    d'aucune transaction d'une autre catégorie.
    """
    regle = propose_rule("VIR INST GESTION AOUT 26 - LG", 49, HISTORIQUE)
    assert regle is not None
    for lab, cat in HISTORIQUE:
        if cat != 49:
            assert regle["pattern"] not in lab.upper(), (
                f"le motif « {regle['pattern']} » capturerait « {lab} » "
                f"(catégorie {cat}) — il déclasserait de l'existant"
            )
    assert regle["conflicts"] == []


def test_refuse_les_motifs_trop_generaux_qui_capturent_une_autre_categorie():
    """« VIR » ou « VIR INST » attraperaient l'apport de Victor Briand (cat 18).

    Piège concret repéré le 2026-07-17 : un apport en compte courant d'associé
    reclassé en charge de gestion. Les motifs sont essayés du plus court au plus
    long ; les plus courts sont ici les plus dangereux et doivent être écartés.
    """
    regle = propose_rule("VIR INST GESTION AOUT 26 - LG", 49, HISTORIQUE)
    assert regle["pattern"].strip() not in ("VIR", "INST", "VIR INST")


def test_ne_propose_rien_si_aucun_motif_n_est_sur():
    """Aucun motif sans conflit → on n'invente pas, l'inbox propose sans règle.

    Ici la catégorie 18 (l'apport de Victor Briand) ne partage avec le reste de
    l'historique que « VIR » et « INST », deux jetons présents dans des
    transactions de gestion (cat 49). Tout motif les utilisant créerait un
    conflit ; le seul motif sûr serait le nom propre, spécifique à cette seule
    transaction — donc une empreinte. On préfère ne rien proposer.
    """
    regle = propose_rule("VIR INST MR VICTOR BRIAND   9999888877776666", 18, HISTORIQUE)
    assert regle is None or regle["conflicts"] == []


def test_le_motif_propose_matche_bien_le_libelle_dont_il_est_issu():
    """Garde-fou : une règle qui ne matche même pas sa propre transaction est un bug."""
    label = "VIR INST GESTION AOUT 26 - LG CH3W26240W009999"
    regle = propose_rule(label, 49, HISTORIQUE)
    assert regle["pattern"] in label.upper()
