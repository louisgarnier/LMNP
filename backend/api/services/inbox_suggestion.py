"""Suggestion de catégorie et proposition de règle ROBUSTE pour l'inbox.

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md

--- LE PROBLÈME QUE CE MODULE RÈGLE ----------------------------------------

Jusqu'au 2026-07-17, l'inbox appelait `derive_prefix_pattern` puis créait une
règle à chaque classement. Cette heuristique ne retire que les identifiants de
FIN de libellé : sur « VIR INST GESTION FEVRIER 26 - LG », le dernier jeton
(« LG ») est stable, donc rien n'est retiré et elle se replie sur
(libellé complet, "exact"). Résultat : une règle qui ne matchera plus jamais
rien — 272 des 370 règles de la base ne couvrent qu'une seule transaction, et
Louis reclassait ses frais de gestion tous les mois.

Deux causes se cumulaient :
- les parties variables (mois, année) sont AU MILIEU du libellé, là où
  `derive_prefix_pattern` ne regarde pas ;
- la garde de similarité 70 % de `classification_engine` (l.22-23) interdit
  mécaniquement tout motif court, sauf `strict_ratio=False`.

--- LE PRINCIPE ------------------------------------------------------------

L'information n'est pas dans le libellé isolé — les libellés de virement sont
saisis à la main et varient chaque mois :

    VIR INST GESTION FEVRIER 26 - LG
    VIR INST VIREMENT JANVIER 26 - LG      (pas de « GESTION »)
    VIR INST VIREMENT GESTION - MARS LG    (mots dans un autre ordre)
    VIR INST AVRIL 2026 - LOUIS G          (ni « GESTION » ni « LG »)

Aucun motif unique ne couvre les quatre. L'information est dans l'HISTORIQUE
de la catégorie. Ce module s'appuie donc toujours sur l'historique classé du
bien, jamais sur le seul libellé courant.

--- ZÉRO RISQUE (décision de Louis, 2026-07-17) ----------------------------

Louis a explicitement refusé le classement automatique par ressemblance (mesuré
à 0,3 % d'erreur silencieuse) : « je refuse le moindre risque ». Ce module
PROPOSE, il ne décide jamais :
- `suggest_category` sert à PRÉ-REMPLIR l'inbox — un humain valide ;
- `propose_rule` ne propose qu'un motif à ZÉRO conflit vérifié contre tout
  l'historique du bien, et rend ses statistiques pour que l'écran les montre
  avant acceptation.

Le classement automatique reste le fait des règles (`classification_engine`),
qui sont exactes par construction.
"""

import re
from collections import Counter

# Jetons qui varient d'un mois à l'autre et ne portent aucune information de
# catégorie : mois, années, montants, références bancaires.
_MOIS = {
    "JANVIER", "FEVRIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET",
    "AOUT", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE", "DÉCEMBRE",
    "JAN", "FEV", "FÉV", "MAR", "AVR", "JUI", "JUIL", "AOU", "SEP", "SEPT",
    "OCT", "NOV", "DEC", "DÉC",
}

# Un jeton est « variable » s'il porte un mois (même collé à une année, ex.
# « AOUT25 »), s'il est purement numérique, s'il ressemble à une référence
# bancaire, ou s'il n'est que ponctuation.
_REFERENCE = re.compile(r"^(G-\S+|GP\d+|M-\S+|(?=\S*\d)[A-Z0-9]{6,}|\S*\d{5,}\S*)$")
_PONCTUATION = re.compile(r"^[-–—.,;:_/\\]+$")

# Longueur minimale d'un jeton retenu : en dessous, aucune valeur discriminante.
_MIN_TOKEN = 2
# Nombre minimal de transactions qu'un motif doit couvrir pour valoir une règle.
# En dessous, c'est une empreinte de plus — exactement ce qu'on cherche à tuer.
MIN_COUVERTURE = 2
# Ressemblance minimale pour oser suggérer une catégorie.
SEUIL_RESSEMBLANCE = 0.5


def _est_variable(token: str) -> bool:
    if _PONCTUATION.match(token):
        return True
    if token in _MOIS:
        return True
    # « AOUT25 », « NOV25 », « DEC24 » : mois collé à l'année.
    for m in _MOIS:
        if token.startswith(m) and token[len(m):].isdigit():
            return True
    if token.isdigit():
        return True
    if _REFERENCE.match(token):
        return True
    return False


def normalize_tokens(label: str) -> list[str]:
    """Jetons porteurs de sens d'un libellé : sans mois, année ni référence."""
    bruts = re.split(r"[\s/]+", (label or "").upper().strip())
    return [t for t in bruts if t and len(t) >= _MIN_TOKEN and not _est_variable(t)]


def _ressemblance(a: list[str], b: list[str]) -> float:
    """Jaccard sur les jetons porteurs de sens."""
    A, B = set(a), set(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def suggest_category(label: str, historique: list[tuple[str, int]]) -> int | None:
    """Catégorie du voisin le plus ressemblant de l'historique classé, ou None.

    Sert UNIQUEMENT à pré-remplir l'inbox : un humain valide toujours. Renvoie
    None plutôt qu'un pari quand rien ne ressemble assez, ou quand les meilleurs
    voisins ne sont pas d'accord entre eux (libellé ambigu).

    `historique` : [(libellé, category_id)] des transactions DÉJÀ classées du bien.
    """
    tokens = normalize_tokens(label)
    if not tokens or not historique:
        return None

    notes = []
    for lab, cat in historique:
        s = _ressemblance(tokens, normalize_tokens(lab))
        if s >= SEUIL_RESSEMBLANCE:
            notes.append((s, cat))
    if not notes:
        return None

    notes.sort(key=lambda x: -x[0])
    meilleur = notes[0][0]
    # Départage : à ressemblance maximale égale, exiger l'unanimité — un libellé
    # qui ressemble autant à deux catégories différentes n'est pas suggérable.
    ex_aequo = {cat for s, cat in notes if s >= meilleur - 1e-9}
    if len(ex_aequo) > 1:
        return None
    return ex_aequo.pop()


def _candidats(tokens: list[str]) -> list[str]:
    """Motifs candidats : jetons seuls puis suites de jetons adjacents."""
    out = []
    for taille in range(1, len(tokens) + 1):
        for i in range(len(tokens) - taille + 1):
            out.append(" ".join(tokens[i:i + taille]))
    return list(dict.fromkeys(out))


def propose_rule(
    label: str, category_id: int, historique: list[tuple[str, int]]
) -> dict | None:
    """Motif le plus court couvrant le plus de `category_id`, SANS aucun conflit.

    Renvoie {"pattern", "match_type", "matches", "conflicts"} où :
      - `matches`   : nb de transactions de `category_id` que le motif couvre ;
      - `conflicts` : libellés d'AUTRES catégories que le motif capturerait —
                      toujours vide, sinon le motif est rejeté.

    Renvoie None si aucun motif sûr ne couvre au moins MIN_COUVERTURE
    transactions : mieux vaut pas de règle qu'une empreinte de plus, ou qu'une
    règle qui déclasserait de l'existant.

    Le motif est destiné à une règle `contains` avec `strict_ratio=False` —
    sans quoi la garde des 70 % (classification_engine l.22-23) le rejetterait.
    """
    tokens = normalize_tokens(label)
    if not tokens or not historique:
        return None

    retenus = []
    for pattern in _candidats(tokens):
        touche_cible = 0
        conflits = []
        for lab, cat in historique:
            if pattern in lab.upper():
                if cat == category_id:
                    touche_cible += 1
                else:
                    conflits.append(lab)
        if conflits:
            continue  # ce motif déclasserait de l'existant : écarté d'office
        if touche_cible >= MIN_COUVERTURE:
            retenus.append((touche_cible, pattern))

    if not retenus:
        return None

    # Couverture maximale d'abord ; à couverture égale, le motif le PLUS LONG.
    #
    # ⚠️ Le tri « plus court d'abord » est un piège : sur un historique jeune où
    # une seule catégorie est classée, « VIR » n'entre en conflit avec rien et
    # serait retenu — alors qu'il avalerait tout le reste dès que d'autres
    # catégories apparaîtraient. L'absence de conflit AUJOURD'HUI ne prouve rien
    # sur demain. À couverture égale, le motif le plus spécifique est le seul
    # choix sûr : il couvre autant, et engage moins l'avenir.
    couverture, pattern = max(retenus, key=lambda r: (r[0], len(r[1])))
    return {
        "pattern": pattern,
        "match_type": "contains",
        "matches": couverture,
        "conflicts": [],
    }
