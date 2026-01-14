"""
API routes for amortization calculations and results.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List, Optional
from collections import defaultdict

from backend.database import get_db
from backend.database.models import AmortizationResult, Transaction
from backend.api.models import (
    AmortizationResultsResponse,
    AmortizationAggregatedResponse,
    AmortizationDetailsResponse,
    AmortizationResultDetail,
    AmortizationRecalculateResponse
)
from backend.api.services.amortization_service import recalculate_all_amortizations

router = APIRouter()


@router.get("/amortization/results", response_model=AmortizationResultsResponse)
async def get_amortization_results(
    db: Session = Depends(get_db)
):
    """
    Récupère les résultats d'amortissement agrégés par année et catégorie.
    
    Returns:
        Résultats agrégés avec totaux par année, par catégorie et total général
    """
    # Récupérer tous les résultats
    results = db.query(AmortizationResult).all()
    
    # Agréger par année et catégorie
    results_by_year = defaultdict(lambda: defaultdict(float))
    totals_by_year = defaultdict(float)
    totals_by_category = defaultdict(float)
    
    for result in results:
        year = result.year
        category = result.category
        amount = result.amount
        
        results_by_year[year][category] += amount
        totals_by_year[year] += amount
        totals_by_category[category] += amount
    
    # Convertir en dict normal
    results_dict = {
        year: dict(categories) 
        for year, categories in results_by_year.items()
    }
    
    # Calculer le total général
    grand_total = sum(totals_by_year.values())
    
    return AmortizationResultsResponse(
        results=results_dict,
        totals_by_year=dict(totals_by_year),
        totals_by_category=dict(totals_by_category),
        grand_total=grand_total
    )


@router.get("/amortization/results/aggregated", response_model=AmortizationAggregatedResponse)
async def get_amortization_results_aggregated(
    db: Session = Depends(get_db)
):
    """
    Récupère les résultats d'amortissement sous forme de tableau croisé prêt pour affichage.
    
    Returns:
        Tableau croisé avec catégories en lignes, années en colonnes, et totaux
    """
    # Récupérer tous les résultats
    results = db.query(AmortizationResult).all()
    
    if not results:
        return AmortizationAggregatedResponse(
            categories=[],
            years=[],
            data=[],
            totals_by_category={},
            totals_by_year={},
            grand_total=0.0
        )
    
    # Collecter toutes les catégories et années uniques
    categories_set = set()
    years_set = set()
    
    for result in results:
        categories_set.add(result.category)
        years_set.add(result.year)
    
    categories = sorted(list(categories_set))
    years = sorted(list(years_set))
    
    # Créer un dictionnaire pour accès rapide
    data_dict = defaultdict(lambda: defaultdict(float))
    
    for result in results:
        data_dict[result.category][result.year] += result.amount
    
    # Créer la matrice de données
    data = []
    totals_by_category = {}
    totals_by_year = defaultdict(float)
    
    for category in categories:
        row = []
        category_total = 0.0
        
        for year in years:
            amount = data_dict[category].get(year, 0.0)
            row.append(amount)
            category_total += amount
            totals_by_year[year] += amount
        
        data.append(row)
        totals_by_category[category] = category_total
    
    # Calculer le total général
    grand_total = sum(totals_by_category.values())
    
    return AmortizationAggregatedResponse(
        categories=categories,
        years=years,
        data=data,
        totals_by_category=totals_by_category,
        totals_by_year=dict(totals_by_year),
        grand_total=grand_total
    )


@router.get("/amortization/results/details", response_model=AmortizationDetailsResponse)
async def get_amortization_results_details(
    year: Optional[int] = Query(None, description="Filtrer par année"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(100, ge=1, le=1000, description="Taille de page"),
    db: Session = Depends(get_db)
):
    """
    Récupère les détails des transactions pour un drill-down depuis le tableau croisé.
    
    Args:
        year: Année à filtrer (optionnel)
        category: Catégorie à filtrer (optionnel)
        page: Numéro de page
        page_size: Taille de page
    
    Returns:
        Liste des transactions correspondantes avec pagination
    """
    # Construire la requête avec filtres
    query = db.query(
        AmortizationResult,
        Transaction
    ).join(
        Transaction, AmortizationResult.transaction_id == Transaction.id
    )
    
    if year is not None:
        query = query.filter(AmortizationResult.year == year)
    
    if category is not None:
        query = query.filter(AmortizationResult.category == category)
    
    # Compter le total
    total = query.count()
    
    # Pagination
    skip = (page - 1) * page_size
    results = query.offset(skip).limit(page_size).all()
    
    # Construire la réponse
    items = []
    for result, transaction in results:
        items.append(AmortizationResultDetail(
            transaction_id=transaction.id,
            transaction_date=transaction.date,
            transaction_nom=transaction.nom,
            transaction_quantite=transaction.quantite,
            year=result.year,
            category=result.category,
            amount=result.amount
        ))
    
    return AmortizationDetailsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/amortization/recalculate", response_model=AmortizationRecalculateResponse)
async def recalculate_amortizations(
    db: Session = Depends(get_db)
):
    """
    Force le recalcul complet de tous les amortissements.
    
    Utile pour recalculer après changement de configuration.
    
    Returns:
        Message de confirmation avec nombre de résultats créés
    """
    try:
        results_created = recalculate_all_amortizations(db)
        
        # Invalider tous les comptes de résultat (les amortissements ont changé)
        try:
            from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
            invalidate_all_compte_resultat(db)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"⚠️ [recalculate_amortizations] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
        
        return AmortizationRecalculateResponse(
            message="Recalcul des amortissements terminé avec succès",
            results_created=results_created
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du recalcul : {str(e)}"
        )

