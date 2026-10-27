"""Bilan de l'ENTITÉ, présenté dans la forme du CERFA 2033-A.

Le bilan de l'application est calculé appartement par appartement ; la liasse
est déposée pour l'entité entière. Pour vérifier la liasse ligne à ligne, il
faut donc agréger les biens ET parler la même langue que le formulaire — d'où
le mapping ci-dessous, qui associe chaque catégorie de l'application à sa case
CERFA.

L'application reste la référence : la colonne liasse n'est qu'un contrôle.
Cf. ADR « L'application est la source de vérité fiscale » (2026-07-29).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

# Chaque ligne du bilan simplifié 2033-A.
#   case       : numéro de case sur le formulaire, pour que Louis puisse pointer
#   categories : catégories de l'application à additionner (None = calculé)
#   cle_liasse : clé correspondante dans liasse-YYYY.json, None si la liasse ne
#                porte pas cette information (ex. les comptes courants, laissés
#                vides par le cabinet alors que des fonds personnels existent)
MAPPING_CERFA = [
    # ── ACTIF ──
    {"bloc": "ACTIF", "case": "028", "libelle": "Immobilisations corporelles (brut)",
     "categories": ["Immobilisations"], "cle_liasse": "immobilisations_brut"},
    {"bloc": "ACTIF", "case": "030", "libelle": "Amortissements cumulés",
     "categories": ["Amortissements cumulés"], "cle_liasse": "amortissements_cumules",
     "valeur_absolue": True},
    {"bloc": "ACTIF", "case": "084", "libelle": "Disponibilités",
     "categories": ["Compte bancaire"], "cle_liasse": None},
    {"bloc": "ACTIF", "case": "110", "libelle": "TOTAL ACTIF",
     "categories": None, "cle_liasse": "actif_total", "total": "actif"},

    # ── PASSIF ──
    {"bloc": "PASSIF", "case": "120", "libelle": "Capital social ou individuel",
     "categories": ["Souscription de parts sociales"], "cle_liasse": "capital_individuel"},
    {"bloc": "PASSIF", "case": "134", "libelle": "Report à nouveau",
     "categories": ["Report à nouveau / report du déficit"], "cle_liasse": None},
    {"bloc": "PASSIF", "case": "136", "libelle": "Résultat de l'exercice",
     "categories": ["Résultat de l'exercice"], "cle_liasse": "resultat_exercice"},
    {"bloc": "PASSIF", "case": "156", "libelle": "Emprunts et dettes assimilées",
     "categories": ["Emprunt bancaire (capital restant dû)"], "cle_liasse": "emprunt_capital_restant_du"},
    {"bloc": "PASSIF", "case": "173", "libelle": "Comptes courants d'associés",
     "categories": ["Compte courant d'associé"], "cle_liasse": None},
    {"bloc": "PASSIF", "case": "175", "libelle": "Autres dettes",
     "categories": ["Cautions reçues"], "cle_liasse": None},
    {"bloc": "PASSIF", "case": "180", "libelle": "TOTAL PASSIF",
     "categories": None, "cle_liasse": "passif_total", "total": "passif"},
]


def agreger_bilans(bilans):
    """Somme les bilans de plusieurs biens en un bilan d'entité.

    Accepte les DEUX formes que produit l'application :
      - le dict plat de `calculate_bilan()`   -> {"categories": {nom: montant}}
      - l'arbre de la route /api/bilan/calculate -> {"types": [...]}
    Les deux circulent dans le code ; ne supporter que l'une donnait un bilan
    d'entité aux totaux justes mais aux lignes toutes à zéro.

    Returns:
        {"actif_total": float, "passif_total": float, "categories": {nom: montant}}
    """
    categories = {}
    actif = passif = 0.0

    for b in bilans or []:
        if not b:
            continue
        actif += b.get("actif_total", 0.0) or 0.0
        passif += b.get("passif_total", 0.0) or 0.0

        plates = b.get("categories")
        if isinstance(plates, dict):
            for nom, montant in plates.items():
                categories[nom] = categories.get(nom, 0.0) + (montant or 0.0)
            continue

        for t in b.get("types", []):
            for sc in t.get("sub_categories", []):
                for c in sc.get("categories", []):
                    nom = c.get("category_name")
                    if nom is None:
                        continue
                    categories[nom] = categories.get(nom, 0.0) + (c.get("amount", 0.0) or 0.0)

    return {"actif_total": actif, "passif_total": passif, "categories": categories}


_TOLERANCE = 1.0  # la liasse est en euros entiers : écart <= 1 € = arrondi


def bilan_cerfa(db, year, realized=True):
    """Bilan 2033-A de l'entité : valeur APP, valeur liasse, écart, ligne par ligne."""
    from backend.api.services.bilan_service import calculate_bilan
    from backend.api.services.reconciliation_service import load_liasses
    from backend.api.services.ecarts_service import explication_bilan
    from backend.database.models import Property

    bilans = []
    for prop in db.query(Property).all():
        try:
            bilans.append(calculate_bilan(db, year, property_id=prop.id))
        except Exception:  # bien sans activité sur l'exercice
            continue

    agg = agreger_bilans(bilans)
    liasse = load_liasses().get(year)
    bil = (liasse or {}).get("bilan", {})

    lignes = []
    for m in MAPPING_CERFA:
        if m.get("total") == "actif":
            app = agg["actif_total"]
        elif m.get("total") == "passif":
            app = agg["passif_total"]
        else:
            app = sum(agg["categories"].get(c, 0.0) for c in (m["categories"] or []))
        if m.get("valeur_absolue"):
            app = abs(app)

        off = bil.get(m["cle_liasse"]) if (liasse and m["cle_liasse"]) else None
        ecart = round(app - off, 2) if off is not None else None
        lignes.append({
            "bloc": m["bloc"],
            "case": m["case"],
            "libelle": m["libelle"],
            "app": round(app, 2),
            "liasse": off,
            "ecart": ecart,
            "ok": (abs(ecart) <= _TOLERANCE) if ecart is not None else None,
            "total": bool(m.get("total")),
            "explication": explication_bilan(liasse, m["case"]),
        })

    return {
        "annee": year,
        "brouillon": liasse is None,
        "equilibre": round(agg["actif_total"] - agg["passif_total"], 2),
        "nb_ecarts": sum(1 for l in lignes if l["ok"] is False),
        "lignes": lignes,
    }
