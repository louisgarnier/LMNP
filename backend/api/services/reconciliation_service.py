"""Réconciliation appli vs liasses déposées.

Pour chaque exercice, compare ce que l'application CALCULE (source de vérité) à
ce que le cabinet a DÉPOSÉ, et pointe les écarts. La liasse n'est qu'une pièce
de contrôle ; l'appli ne lit jamais ses chiffres du PDF. Cf.
`docs/project/analysis/ECARTS_LIASSES_FISCALES.md`.

Détail PAR APPARTEMENT pour les lignes comptables (produits, résultat,
amortissements, immobilisations) — comme le tableur de Louis — afin que la somme
des biens soit vérifiable ligne à ligne. Les lignes FISCALES (déficit, imposable)
restent au niveau ENTITÉ : ce sont des stocks globaux non ventilables (prouvé par
la liasse 2024). Les exercices sans liasse (année en cours) sont marqués
`brouillon` : chiffres de l'appli, sans comparaison.

Tolérance : liasses en euros entiers → écart de ligne ≤ 1 € = conforme (arrondi).
"""
import json
from pathlib import Path

from sqlalchemy import func

from backend.database.models import Transaction, Property, Category, CategoryGroup
from backend.api.services.compte_resultat_service import calculate_compte_resultat
from backend.api.services.fiscal_service import get_fiscal_timeline, entity_year_range
from backend.api.services.ecarts_service import explication_cr

LIASSES_DIR = (Path(__file__).resolve().parents[3]
               / "docs" / "project" / "reference" / "liasses")

_TOLERANCE = 1.0  # euros entiers -> écart <= 1 € = arrondi
_EPS = 0.005      # seuil "activité" d'un bien sur une année


def load_liasses(directory=None):
    """Charge tous les fichiers liasse-*.json, indexés par année (int)."""
    d = Path(directory) if directory else LIASSES_DIR
    out = {}
    if not d.exists():
        return out
    for f in sorted(d.glob("liasse-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        out[int(data["annee"])] = data
    return out


def _per_bien_cr(db, year, realized=True):
    """{pid: {produits, charges_externes, impots, amortissements, interets, resultat}}
    pour les biens ACTIFS l'année. Charges/impôts/intérêts/amortissements en
    valeur NÉGATIVE (comme des charges). Aucun bien codé en dur : parcourt
    db.query(Property). Un bien sans activité (aucune transaction cette année)
    est omis pour ne pas afficher de colonne à 0.

    `realized=True` (défaut) = Réel (coût financement à ce jour) ; False =
    Prévisionnel (plein an). N'affecte que l'année en cours.
    """
    # catégories de charges NON externes (traitées à part)
    IMPOTS = "Impôts et taxes"
    AMORT = "Charges d'amortissements"
    FIN = "Coût du financement (hors remboursement du capital)"
    out = {}
    for prop in db.query(Property).all():
        cr = calculate_compte_resultat(db, year, property_id=prop.id,
                                       skip_prorata=realized)
        produits = cr.get("total_produits", 0.0)
        resultat = cr.get("resultat_net", 0.0)
        charges = cr.get("charges", {})
        impots = charges.get(IMPOTS, 0.0)
        amort = -abs(cr.get("amortissements", 0.0))
        interets = -abs(cr.get("cout_financement", 0.0))
        charges_externes = sum(v for k, v in charges.items()
                               if k not in (IMPOTS, AMORT, FIN))
        if (abs(produits) > _EPS or abs(resultat) > _EPS or abs(amort) > _EPS):
            out[prop.id] = {
                "produits": round(produits, 2),
                "charges_externes": round(charges_externes, 2),
                "impots": round(impots, 2),
                "amortissements": round(amort, 2),
                "interets": round(interets, 2),
                "resultat": round(resultat, 2),
            }
    return out


def _per_bien_immo(db, year):
    """{pid: immobilisations brutes acquises au 31/12/année} (nature 'actif').

    func.sum sur EuroCents renvoie déjà des euros (ne pas re-diviser).
    """
    end = f"{year}-12-31"
    rows = (db.query(Transaction.property_id,
                     func.coalesce(func.sum(Transaction.quantite), 0))
            .join(Category, Category.id == Transaction.category_id)
            .join(CategoryGroup, CategoryGroup.id == Category.group_id)
            .filter(CategoryGroup.nature == "actif", Transaction.date <= end)
            .group_by(Transaction.property_id)
            .all())
    return {pid: round(abs(v), 2) for pid, v in rows if abs(v) > _EPS}


def _ligne(poste, par_bien, liasse_val):
    """Ligne comptable : détail par bien + total appli, comparé à la liasse.

    `liasse_val` None (exercice brouillon) -> pas de comparaison.
    """
    app = round(sum(par_bien.values()), 2)
    if liasse_val is None:
        return {"poste": poste, "par_bien": par_bien, "app": app,
                "liasse": None, "ecart": None, "ok": None}
    ecart = round(app - liasse_val, 2)
    return {"poste": poste, "par_bien": par_bien, "app": app,
            "liasse": liasse_val, "ecart": ecart, "ok": abs(ecart) <= _TOLERANCE}


def _ligne_entite(poste, app_val, liasse_val):
    """Ligne fiscale (stock d'entité) : total seul, pas de ventilation par bien."""
    app = round(app_val, 2)
    if liasse_val is None:
        return {"poste": poste, "par_bien": None, "app": app,
                "liasse": None, "ecart": None, "ok": None}
    ecart = round(app - liasse_val, 2)
    return {"poste": poste, "par_bien": None, "app": app,
            "liasse": liasse_val, "ecart": ecart, "ok": abs(ecart) <= _TOLERANCE}


def reconcile(db, directory=None, realized=True, imputation_choices=None):
    """Réconciliation par exercice, du plus ancien au plus récent.

    Chaque année : lignes comptables ventilées par bien + total, lignes fiscales
    au total, contrôle de composition, stock de déficit, nb_ecarts. Les exercices
    sans liasse (année en cours) sont marqués `brouillon`.

    `realized=True` (défaut) = Réel (coût financement à ce jour, cohérent avec le
    bilan) ; False = Prévisionnel (plein an). N'affecte que l'année en cours ;
    années closes identiques (conformité aux liasses préservée).
    """
    liasses = load_liasses(directory)
    timeline = get_fiscal_timeline(db, realized=realized,
                                   imputation_choices=imputation_choices)
    annees = entity_year_range(db)
    out = {}

    for year in annees:
        liasse = liasses.get(year)
        brouillon = liasse is None
        fisc = timeline.get(year, {})

        cr_bien = _per_bien_cr(db, year, realized=realized)
        immo_bien = _per_bien_immo(db, year)
        produits_bien = {pid: v["produits"] for pid, v in cr_bien.items()}
        cext_bien = {pid: v["charges_externes"] for pid, v in cr_bien.items()}
        impots_bien = {pid: v["impots"] for pid, v in cr_bien.items()}
        amort_bien_neg = {pid: v["amortissements"] for pid, v in cr_bien.items()}  # négatif
        interets_bien = {pid: v["interets"] for pid, v in cr_bien.items()}
        resultat_bien = {pid: v["resultat"] for pid, v in cr_bien.items()}

        if liasse:
            cr = liasse["compte_resultat"]
            bil = liasse["bilan"]
            fis = liasse["fiscal"]
            biens = liasse["biens_inclus"]
            lignes = [
                _ligne("Produits", produits_bien, cr["produits"]),
                # Périmètre égal : l'app classe en externes ce que le cabinet range parfois
                # en « charges exceptionnelles » (2033-B bloc VI, ex. 60 EUR en 2024).
                _ligne("Charges externes", cext_bien,
                       -(cr["autres_charges_externes"] + cr.get("charges_exceptionnelles", 0))),
                _ligne("Impôts et taxes", impots_bien, -cr["impots_et_taxes"]),
                _ligne("Amortissements", amort_bien_neg, -cr["dotations_amortissements"]),
                _ligne("Intérêts d'emprunt", interets_bien, -cr["charges_financieres"]),
                _ligne("Résultat comptable", resultat_bien, cr["resultat_comptable"]),
                _ligne_entite("Déficit de l'exercice", fisc.get("deficit_annee", 0.0),
                              fis.get("deficit_reportable_de_lannee", 0)),
                _ligne_entite("Déficit reportable (cumulé)",
                              fisc.get("stock_deficit_fin", 0.0),
                              fis.get("stock_deficit_reportable_fin")),
                _ligne_entite("Amortissements reportés (cumulé)",
                              fisc.get("stock_amort_fin", 0.0),
                              fis.get("stock_amort_reporte_reconstitue")),
                _ligne_entite("Résultat fiscal imposable",
                              fisc.get("resultat_fiscal_imposable", 0.0),
                              fis["resultat_fiscal_imposable"]),
            ]
            composition = _ligne("Immobilisations brutes", immo_bien,
                                 bil["immobilisations_brut"])
        else:
            biens = sorted(cr_bien.keys())
            lignes = [
                _ligne("Produits", produits_bien, None),
                _ligne("Charges externes", cext_bien, None),
                _ligne("Impôts et taxes", impots_bien, None),
                _ligne("Amortissements", amort_bien_neg, None),
                _ligne("Intérêts d'emprunt", interets_bien, None),
                _ligne("Résultat comptable", resultat_bien, None),
                _ligne_entite("Déficit de l'exercice", fisc.get("deficit_annee", 0.0), None),
                _ligne_entite("Déficit reportable (cumulé)",
                              fisc.get("stock_deficit_fin", 0.0), None),
                _ligne_entite("Amortissements reportés (cumulé)",
                              fisc.get("stock_amort_fin", 0.0), None),
                _ligne_entite("Résultat fiscal imposable",
                              fisc.get("resultat_fiscal_imposable", 0.0), None),
            ]
            composition = _ligne("Immobilisations brutes", immo_bien, None)

        # Chaque écart porte son explication, quand l'enquête a conclu.
        for l in lignes:
            l["explication"] = explication_cr(liasse, l["poste"])

        nb_ecarts = sum(1 for l in lignes if l["ok"] is False)
        if composition["ok"] is False:
            nb_ecarts += 1

        out[year] = {
            "annee": year,
            "brouillon": brouillon,
            "biens_inclus": biens,
            "cr_par_bien": cr_bien,
            "composition": composition,
            "lignes": lignes,
            "stock_deficit_appli": round(fisc.get("stock_deficit_fin", 0.0), 2),
            "nb_ecarts": nb_ecarts,
        }
    return out
