"""Route de réconciliation appli vs liasses déposées."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.api.services.reconciliation_service import reconcile

router = APIRouter()


@router.get("/reconciliation")
def get_reconciliation(db: Session = Depends(get_db)):
    """Réconciliation par exercice : appli (calculé) vs liasse (déposé) vs écart.

    Retourne `{"annees": [...], "results": {annee: {...}}}`. Chaque exercice
    porte `composition` (contrôle immobilisations), `lignes` (produits, charges
    externes, impôts et taxes, amortissements, intérêts d'emprunt, résultat
    comptable, déficit de l'exercice, déficit reportable, amortissements
    reportés, résultat fiscal imposable), `cr_par_bien` (CR groupé par
    appartement), `stock_deficit_appli` et `nb_ecarts`.
    """
    results = reconcile(db)
    return {"annees": sorted(results.keys()), "results": results}
