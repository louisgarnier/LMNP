"""
API routes for amortization calculations.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, List
from collections import defaultdict

from backend.database import get_db
from backend.database.models import (
    AmortizationConfig, AmortizationResult, Transaction, EnrichedTransaction
)
from backend.api.models import (
    AmortizationConfigResponse,
    AmortizationConfigUpdate,
    AmortizationResultsResponse,
    AmortizationAggregatedResponse,
    AmortizationRecalculateResponse,
    TransactionResponse,
    TransactionListResponse
)
from backend.api.services.amortization_service import recalculate_all_amortizations

router = APIRouter()


@router.get("/amortization/config", response_model=AmortizationConfigResponse)
async def get_amortization_config(
    db: Session = Depends(get_db)
):
    """
    Récupère la configuration des amortissements.
    Crée une configuration par défaut si elle n'existe pas.
    
    Returns:
        Configuration des amortissements (singleton - une seule config)
    """
    config = db.query(AmortizationConfig).first()
    
    if not config:
        # Créer une configuration par défaut
        config = AmortizationConfig(
            level_2_value="ammortissements",
            level_3_mapping={
                "part_terrain": [],
                "structure_go": [],
                "mobilier": [],
                "igt": [],
                "agencements": [],
                "facade_toiture": [],
                "travaux": [],
            },
            duration_part_terrain=0.0,
            duration_structure_go=0.0,
            duration_mobilier=0.0,
            duration_igt=0.0,
            duration_agencements=0.0,
            duration_facade_toiture=0.0,
            duration_travaux=0.0
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return AmortizationConfigResponse.model_validate(config)


@router.put("/amortization/config", response_model=AmortizationConfigResponse)
async def update_amortization_config(
    config_data: AmortizationConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour ou crée la configuration des amortissements.
    
    Si aucune configuration n'existe, en crée une nouvelle.
    Si une configuration existe, la met à jour (singleton).
    
    Args:
        config_data: Données de configuration (level_2_value, level_3_mapping, durées)
        db: Session de base de données
    
    Returns:
        Configuration mise à jour ou créée
    """
    # Vérifier que le mapping contient les 7 clés requises
    required_keys = ["part_terrain", "structure_go", "mobilier", "igt", "agencements", "facade_toiture", "travaux"]
    if not all(key in config_data.level_3_mapping for key in required_keys):
        raise HTTPException(
            status_code=400,
            detail=f"Le mapping level_3 doit contenir les clés suivantes: {', '.join(required_keys)}"
        )
    
    # Récupérer ou créer la configuration (singleton)
    config = db.query(AmortizationConfig).first()
    
    if config:
        # Mettre à jour la configuration existante
        config.level_2_value = config_data.level_2_value
        config.level_3_mapping = config_data.level_3_mapping
        # Utiliser 0.0 si la valeur n'est pas fournie ou est None
        config.duration_part_terrain = config_data.duration_part_terrain if config_data.duration_part_terrain is not None else 0.0
        config.duration_structure_go = config_data.duration_structure_go if config_data.duration_structure_go is not None else 0.0
        config.duration_mobilier = config_data.duration_mobilier if config_data.duration_mobilier is not None else 0.0
        config.duration_igt = config_data.duration_igt if config_data.duration_igt is not None else 0.0
        config.duration_agencements = config_data.duration_agencements if config_data.duration_agencements is not None else 0.0
        config.duration_facade_toiture = config_data.duration_facade_toiture if config_data.duration_facade_toiture is not None else 0.0
        config.duration_travaux = config_data.duration_travaux if config_data.duration_travaux is not None else 0.0
    else:
        # Créer une nouvelle configuration
        config = AmortizationConfig(
            level_2_value=config_data.level_2_value,
            level_3_mapping=config_data.level_3_mapping,
            duration_part_terrain=config_data.duration_part_terrain if config_data.duration_part_terrain is not None else 0.0,
            duration_structure_go=config_data.duration_structure_go if config_data.duration_structure_go is not None else 0.0,
            duration_mobilier=config_data.duration_mobilier if config_data.duration_mobilier is not None else 0.0,
            duration_igt=config_data.duration_igt if config_data.duration_igt is not None else 0.0,
            duration_agencements=config_data.duration_agencements if config_data.duration_agencements is not None else 0.0,
            duration_facade_toiture=config_data.duration_facade_toiture if config_data.duration_facade_toiture is not None else 0.0,
            duration_travaux=config_data.duration_travaux if config_data.duration_travaux is not None else 0.0
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    
    return AmortizationConfigResponse.model_validate(config)


@router.get("/amortization/results", response_model=AmortizationResultsResponse)
async def get_amortization_results(
    db: Session = Depends(get_db)
):
    """
    Récupère les résultats d'amortissements agrégés par année et catégorie.
    
    Returns:
        Résultats agrégés avec totaux par année, par catégorie, et total général
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
    
    # Convertir defaultdict en dict normal
    results_dict = {
        year: dict(categories) 
        for year, categories in results_by_year.items()
    }
    
    grand_total = sum(totals_by_category.values())
    
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
    Récupère les résultats d'amortissements sous forme de tableau croisé prêt pour affichage.
    
    Returns:
        Tableau croisé avec catégories en lignes, années en colonnes, et totaux
    """
    # Récupérer tous les résultats
    results = db.query(AmortizationResult).all()
    
    # Collecter toutes les catégories et années uniques
    categories_set = set()
    years_set = set()
    
    for result in results:
        categories_set.add(result.category)
        years_set.add(result.year)
    
    categories = sorted(list(categories_set))
    years = sorted(list(years_set))
    
    # Créer matrice de données
    data = []
    row_totals = []
    
    for category in categories:
        row = []
        row_total = 0.0
        
        for year in years:
            # Trouver le montant pour cette catégorie et cette année
            amount = sum(
                r.amount for r in results 
                if r.category == category and r.year == year
            )
            row.append(amount)
            row_total += amount
        
        data.append(row)
        row_totals.append(row_total)
    
    # Calculer totaux par colonne (année)
    column_totals = []
    for year in years:
        col_total = sum(
            r.amount for r in results 
            if r.year == year
        )
        column_totals.append(col_total)
    
    # Grand total
    grand_total = sum(row_totals)
    
    return AmortizationAggregatedResponse(
        categories=categories,
        years=years,
        data=data,
        row_totals=row_totals,
        column_totals=column_totals,
        grand_total=grand_total
    )


@router.get("/amortization/results/details", response_model=TransactionListResponse)
async def get_amortization_results_details(
    year: Optional[int] = Query(None, description="Année à filtrer"),
    category: Optional[str] = Query(None, description="Catégorie à filtrer (meubles, travaux, construction, terrain)"),
    skip: int = Query(0, ge=0, description="Nombre de résultats à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """
    Récupère les transactions détaillées correspondant aux critères d'amortissement.
    
    Utilisé pour le drill-down depuis le tableau croisé.
    
    Args:
        year: Année à filtrer (optionnel)
        category: Catégorie à filtrer (optionnel)
        skip: Nombre de résultats à sauter (pagination)
        limit: Nombre maximum de résultats (pagination)
        db: Session de base de données
    
    Returns:
        Liste des transactions avec pagination
    """
    # Construire la requête
    query = db.query(Transaction).join(
        AmortizationResult,
        Transaction.id == AmortizationResult.transaction_id
    ).join(
        EnrichedTransaction,
        Transaction.id == EnrichedTransaction.transaction_id
    )
    
    # Appliquer filtres
    if year is not None:
        query = query.filter(AmortizationResult.year == year)
    
    if category is not None:
        query = query.filter(AmortizationResult.category == category)
    
    # Compter le total
    total = query.count()
    
    # Pagination
    transactions = query.offset(skip).limit(limit).all()
    
    # Construire les réponses
    transaction_responses = []
    for t in transactions:
        enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == t.id
        ).first()
        
        transaction_dict = {
            "id": t.id,
            "date": t.date,
            "quantite": t.quantite,
            "nom": t.nom,
            "solde": t.solde,
            "source_file": t.source_file,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "level_1": enriched.level_1 if enriched else None,
            "level_2": enriched.level_2 if enriched else None,
            "level_3": enriched.level_3 if enriched else None,
        }
        transaction_responses.append(TransactionResponse(**transaction_dict))
    
    return TransactionListResponse(
        transactions=transaction_responses,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/amortization/recalculate", response_model=AmortizationRecalculateResponse)
async def recalculate_amortizations(
    db: Session = Depends(get_db)
):
    """
    Force le recalcul complet de tous les amortissements.
    
    Utile après un changement de configuration ou pour recalculer toutes les transactions.
    
    Returns:
        Message de confirmation avec nombre de transactions traitées
    """
    count = recalculate_all_amortizations(db)
    
    return AmortizationRecalculateResponse(
        message=f"Recalcul effectué avec succès. {count} transaction(s) traitée(s).",
        transactions_processed=count
    )

