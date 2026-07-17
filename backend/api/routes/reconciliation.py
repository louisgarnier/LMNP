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
    porte `composition` (contrôle immobilisations), `lignes` (produits, résultat
    comptable, amortissements, déficit de l'exercice, résultat fiscal imposable),
    `stock_deficit_appli` et `nb_ecarts`.
    """
    results = reconcile(db)
    return {"annees": sorted(results.keys()), "results": results}
