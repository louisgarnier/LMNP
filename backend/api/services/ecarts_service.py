"""Explications des écarts entre l'application et la liasse déposée.

Un écart non expliqué est inexploitable : Louis ne sait pas s'il faut corriger
l'application, écrire au cabinet, ou ne rien faire. Or ces explications sont des
RÉSULTATS D'ENQUÊTE — lecture des FEC, des tableaux d'amortissement, du PDF de
la liasse. Elles ne se déduisent d'aucun calcul.

Elles vivent donc dans les fichiers `liasse-YYYY.json`, sous la clé
`ecarts_expliques`, à côté des montants qu'elles commentent : c'est de la donnée
de référence, pas du code. Instruire un nouvel écart = éditer un JSON.

Détail des enquêtes : docs/project/analysis/ECARTS_LIASSES_FISCALES.md

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

STATUTS = {
    "erreur_cabinet": {
        "libelle": "Erreur du cabinet",
        "ton": "rouge",
        "action": "à faire régulariser",
    },
    "difference_presentation": {
        "libelle": "Différence de présentation",
        "ton": "neutre",
        "action": "même réalité rangée autrement — rien à corriger",
    },
    "difference_date": {
        "libelle": "Différence de date",
        "ton": "info",
        "action": "décalage de mise en service — se résorbe seul",
    },
    "a_investiguer": {
        "libelle": "À investiguer",
        "ton": "info",
        "action": "cause non encore établie",
    },
}


def charger_explications(liasse):
    """Extrait et valide le bloc `ecarts_expliques` d'une liasse."""
    brut = (liasse or {}).get("ecarts_expliques") or {}
    out = {"cr": brut.get("cr") or {}, "bilan": brut.get("bilan") or {}}
    for bloc in out.values():
        for cle, e in bloc.items():
            statut = (e or {}).get("statut")
            if statut not in STATUTS:
                raise ValueError(f"statut inconnu « {statut} » pour « {cle} »")
    return out


def _resoudre(liasse, bloc, cle):
    if not liasse:
        return None
    e = charger_explications(liasse)[bloc].get(str(cle))
    if not e:
        return None
    meta = STATUTS[e["statut"]]
    return {
        "statut": e["statut"],
        "libelle": meta["libelle"],
        "ton": meta["ton"],
        "action": meta["action"],
        "cause": e.get("cause", ""),
    }


def explication_cr(liasse, poste):
    """Explication d'un poste du compte de résultat, ou None."""
    return _resoudre(liasse, "cr", poste)


def explication_bilan(liasse, case):
    """Explication d'une case du bilan, ou None."""
    return _resoudre(liasse, "bilan", case)
