"""Réconciliation appli vs liasses déposées.

Pour chaque exercice qui a une liasse de référence
(`docs/project/reference/liasses/liasse-YYYY.json`), compare ce que
l'application CALCULE (source de vérité) à ce que le cabinet a DÉPOSÉ, et
pointe les écarts. Ce n'est pas l'appli qui lit ses chiffres du PDF : la liasse
n'est qu'une pièce de contrôle. Un écart ≠ 0 signale une divergence (erreur du
cabinet, ou différence de données à investiguer) — cf.
`docs/project/analysis/ECARTS_LIASSES_FISCALES.md`.

Tolérance : les liasses sont en euros entiers, donc un écart de ligne ≤ 1 € est
considéré conforme (arrondi). Au-delà, c'est un vrai écart.
"""
import json
from pathlib import Path

from sqlalchemy import func

from backend.database.models import Transaction, Property, Category, CategoryGroup
from backend.api.services.compte_resultat_service import calculate_compte_resultat
from backend.api.services.fiscal_service import get_fiscal_timeline, entity_year_inputs

LIASSES_DIR = (Path(__file__).resolve().parents[3]
               / "docs" / "project" / "reference" / "liasses")

_TOLERANCE = 1.0  # euros entiers -> un écart <= 1 € est de l'arrondi


def load_liasses(directory=None):
    """Charge tous les fichiers de référence liasse-*.json, indexés par année."""
    d = Path(directory) if directory else LIASSES_DIR
    out = {}
    if not d.exists():
        return out
    for f in sorted(d.glob("liasse-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        out[int(data["annee"])] = data
    return out


def _entity_produits(db, year):
    """Somme des produits d'exploitation de tous les biens (niveau entité)."""
    total = 0.0
    for prop in db.query(Property).all():
        cr = calculate_compte_resultat(db, year, property_id=prop.id)
        total += cr.get("total_produits", 0.0)
    return total


def _immo_brut_fin(db, year):
    """Immobilisations brutes acquises jusqu'au 31/12/année (nature 'actif').

    Sert au contrôle de composition : quels biens sont réellement dans le
    périmètre à cette date (les travaux/mobilier immobilisés plus tard n'y
    figurent pas avant leur année d'entrée).
    """
    end = f"{year}-12-31"
    # func.sum sur une colonne EuroCents renvoie déjà des EUROS via le
    # décorateur de type (centimes en base, euros à l'ORM) — ne pas re-diviser.
    total = (db.query(func.coalesce(func.sum(Transaction.quantite), 0))
             .join(Category, Category.id == Transaction.category_id)
             .join(CategoryGroup, CategoryGroup.id == Category.group_id)
             .filter(CategoryGroup.nature == "actif",
                     Transaction.date <= end)
             .scalar()) or 0
    return abs(total)


def _line(poste, app, liasse):
    ecart = round(app - liasse, 2)
    return {
        "poste": poste,
        "app": round(app, 2),
        "liasse": liasse,
        "ecart": ecart,
        "ok": abs(ecart) <= _TOLERANCE,
    }


def reconcile(db, directory=None):
    """Réconciliation appli vs liasse pour chaque exercice de référence.

    Retour : {année: {biens_inclus, composition, lignes, stock_deficit_appli,
    nb_ecarts}}. `composition` et chaque ligne portent app / liasse / ecart / ok.
    """
    liasses = load_liasses(directory)
    timeline = get_fiscal_timeline(db)
    out = {}
    for year, liasse in liasses.items():
        cr = liasse["compte_resultat"]
        bil = liasse["bilan"]
        fis = liasse["fiscal"]
        inputs = entity_year_inputs(db, year)   # resultat_comptable, amortissements
        fisc = timeline.get(year, {})

        lignes = [
            _line("Produits", _entity_produits(db, year), cr["produits"]),
            _line("Résultat comptable", inputs["resultat_comptable"],
                  cr["resultat_comptable"]),
            _line("Amortissements", inputs["amortissements"],
                  cr["dotations_amortissements"]),
            _line("Déficit de l'exercice", fisc.get("deficit_annee", 0.0),
                  fis.get("deficit_reportable_de_lannee", 0)),
            _line("Résultat fiscal imposable",
                  fisc.get("resultat_fiscal_imposable", 0.0),
                  fis["resultat_fiscal_imposable"]),
        ]
        composition = _line("Immobilisations brutes",
                            _immo_brut_fin(db, year), bil["immobilisations_brut"])

        out[year] = {
            "annee": year,
            "biens_inclus": liasse["biens_inclus"],
            "composition": composition,
            "lignes": lignes,
            # Le stock cumulé de déficit n'est pas comparé (la liasse ne
            # l'imprime pas de façon fiable) mais exposé pour information.
            "stock_deficit_appli": round(fisc.get("stock_deficit_fin", 0.0), 2),
            "nb_ecarts": sum(1 for l in lignes if not l["ok"])
                         + (0 if composition["ok"] else 1),
        }
    return out
