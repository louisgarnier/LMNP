"""
API routes for compte de résultat (income statement).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict
from datetime import date, datetime

from backend.database import get_db
from backend.database.models import (
    CompteResultatMapping,
    CompteResultatData,
    CompteResultatMappingView
)
from backend.api.models import (
    CompteResultatMappingCreate,
    CompteResultatMappingUpdate,
    CompteResultatMappingResponse,
    CompteResultatMappingListResponse,
    CompteResultatDataResponse,
    CompteResultatDataListResponse,
    CompteResultatGenerateRequest,
    CompteResultatResponse,
    CompteResultatMappingViewResponse,
    CompteResultatMappingViewCreate,
    CompteResultatMappingViewUpdate,
    CompteResultatMappingViewListResponse
)
from backend.api.services.compte_resultat_service import (
    get_mappings,
    calculate_compte_resultat,
    calculate_amounts_by_category_and_year
)

router = APIRouter()


@router.get("/compte-resultat/mappings", response_model=CompteResultatMappingListResponse)
async def get_compte_resultat_mappings(
    db: Session = Depends(get_db)
):
    """
    Récupère tous les mappings de compte de résultat.
    
    Returns:
        Liste de tous les mappings
    """
    mappings = db.query(CompteResultatMapping).order_by(
        CompteResultatMapping.category_name
    ).all()
    
    return CompteResultatMappingListResponse(
        mappings=[CompteResultatMappingResponse.model_validate(m) for m in mappings],
        total=len(mappings)
    )


@router.get("/compte-resultat/mappings/{mapping_id}", response_model=CompteResultatMappingResponse)
async def get_compte_resultat_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un mapping par ID.
    
    Args:
        mapping_id: ID du mapping
        
    Returns:
        Mapping
        
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    return CompteResultatMappingResponse.model_validate(mapping)


@router.post("/compte-resultat/mappings", response_model=CompteResultatMappingResponse, status_code=201)
async def create_compte_resultat_mapping(
    mapping_data: CompteResultatMappingCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau mapping.
    
    Args:
        mapping_data: Données du mapping à créer
        
    Returns:
        Mapping créé
    """
    mapping = CompteResultatMapping(
        category_name=mapping_data.category_name,
        level_1_values=mapping_data.level_1_values,
        level_2_values=mapping_data.level_2_values,
        level_3_values=mapping_data.level_3_values,
        amortization_view_id=mapping_data.amortization_view_id if hasattr(mapping_data, 'amortization_view_id') else None,
        selected_loan_ids=mapping_data.selected_loan_ids if hasattr(mapping_data, 'selected_loan_ids') else None
    )
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    # Invalider tous les comptes de résultat (les mappings ont changé)
    from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
    invalidate_all_compte_resultat(db)
    
    return CompteResultatMappingResponse.model_validate(mapping)


@router.put("/compte-resultat/mappings/{mapping_id}", response_model=CompteResultatMappingResponse)
async def update_compte_resultat_mapping(
    mapping_id: int,
    mapping_data: CompteResultatMappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un mapping.
    
    Args:
        mapping_id: ID du mapping
        mapping_data: Données à mettre à jour
        
    Returns:
        Mapping mis à jour
        
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    # Mettre à jour les champs fournis
    # Utiliser model_dump(exclude_unset=True) pour ne mettre à jour que les champs explicitement fournis
    update_data = mapping_data.model_dump(exclude_unset=True)
    
    if 'category_name' in update_data:
        mapping.category_name = update_data['category_name']
    if 'level_1_values' in update_data:
        # Permettre de mettre à jour même si c'est None (pour vider la liste)
        mapping.level_1_values = update_data['level_1_values']
    if 'level_2_values' in update_data:
        mapping.level_2_values = update_data['level_2_values']
    if 'level_3_values' in update_data:
        mapping.level_3_values = update_data['level_3_values']
    if 'amortization_view_id' in update_data:
        mapping.amortization_view_id = update_data['amortization_view_id']
    if 'selected_loan_ids' in update_data:
        mapping.selected_loan_ids = update_data['selected_loan_ids']
    
    db.commit()
    db.refresh(mapping)
    
    return CompteResultatMappingResponse.model_validate(mapping)


@router.delete("/compte-resultat/mappings/{mapping_id}", status_code=204)
async def delete_compte_resultat_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un mapping.
    
    Args:
        mapping_id: ID du mapping
        
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    db.delete(mapping)
    db.commit()
    
    # Invalider tous les comptes de résultat (les mappings ont changé)
    from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
    invalidate_all_compte_resultat(db)
    
    # Invalider tous les bilans (les mappings ont changé)
    from backend.api.services.bilan_service import invalidate_all_bilan
    invalidate_all_bilan(db)
    
    return None


@router.post("/compte-resultat/generate", response_model=CompteResultatResponse)
async def generate_compte_resultat(
    request: CompteResultatGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Génère un compte de résultat pour une année donnée et le stocke en base de données.
    
    Args:
        request: Requête avec year et amortization_view_id
        
    Returns:
        Compte de résultat calculé
    """
    # Récupérer les mappings
    mappings = get_mappings(db)
    
    # Calculer le compte de résultat
    result = calculate_compte_resultat(
        request.year,
        mappings,
        request.amortization_view_id,
        db
    )
    
    # Supprimer les anciennes données pour cette année
    db.query(CompteResultatData).filter(
        CompteResultatData.annee == request.year
    ).delete()
    
    # Stocker les résultats en base de données
    for category_name, amount in result["categories"].items():
        data = CompteResultatData(
            annee=request.year,
            category_name=category_name,
            amount=amount,
            amortization_view_id=request.amortization_view_id
        )
        db.add(data)
    
    db.commit()
    
    return CompteResultatResponse(
        year=request.year,
        categories=result["categories"],
        total_produits=result["total_produits"],
        total_charges=result["total_charges"],
        resultat_exploitation=result["resultat_exploitation"],
        resultat_net=result["resultat_net"]
    )


@router.get("/compte-resultat")
async def get_compte_resultat(
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début (pour plusieurs années)"),
    end_year: Optional[int] = Query(None, description="Année de fin (pour plusieurs années)"),
    db: Session = Depends(get_db)
):
    """
    Récupère les comptes de résultat.
    
    Args:
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel, pour plusieurs années)
        end_year: Année de fin (optionnel, pour plusieurs années)
        
    Returns:
        Dictionnaire {year: CompteResultatResponse} pour une ou plusieurs années
    """
    # Déterminer les années à récupérer
    if year:
        years = [year]
    elif start_year and end_year:
        years = list(range(start_year, end_year + 1))
    else:
        # Récupérer toutes les années disponibles
        years = db.query(CompteResultatData.annee).distinct().all()
        years = [y[0] for y in years]
    
    if not years:
        return {}
    
    # Récupérer les données pour chaque année
    results = {}
    
    for year_val in years:
        # Récupérer toutes les données pour cette année
        data_list = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year_val
        ).all()
        
        if not data_list:
            continue
        
        # Construire le dictionnaire de catégories
        categories = {data.category_name: data.amount for data in data_list}
        
        # Calculer les totaux
        produits_categories = [
            "Loyers hors charge encaissés",
            "Charges locatives payées par locataires",
            "Autres revenus"
        ]
        
        total_produits = sum(
            amount for category, amount in categories.items()
            if category in produits_categories
        )
        
        total_charges = sum(
            amount for category, amount in categories.items()
            if category not in produits_categories
        )
        
        resultat_exploitation = total_produits - total_charges
        resultat_net = resultat_exploitation
        
        results[str(year_val)] = CompteResultatResponse(
            year=year_val,
            categories=categories,
            total_produits=total_produits,
            total_charges=total_charges,
            resultat_exploitation=resultat_exploitation,
            resultat_net=resultat_net
        ).model_dump()
    
    return results


@router.get("/compte-resultat/calculate")
async def calculate_compte_resultat_amounts(
    years: Optional[str] = Query(None, description="Années séparées par des virgules (ex: 2023,2024)"),
    year: Optional[int] = Query(None, description="Année unique"),
    db: Session = Depends(get_db)
):
    """
    Calcule les montants par catégorie et année en utilisant les mappings configurés.
    
    Cette fonction utilise exclusivement les mappings configurés dans CompteResultatMapping.
    Pour chaque catégorie :
    - Si mapping level_1/level_2 : calcule depuis les transactions
    - Si "Charges d'amortissements" : utilise amortization_view_id du mapping
    - Si "Coût du financement" : utilise selected_loan_ids du mapping
    
    Args:
        years: Années séparées par des virgules (ex: "2023,2024")
        year: Année unique (alternative à years)
        db: Session de base de données
        
    Returns:
        Dictionnaire {year: {category_name: amount}}
    """
    # Déterminer les années à calculer
    if years:
        years_list = [int(y.strip()) for y in years.split(',')]
    elif year:
        years_list = [year]
    else:
        raise HTTPException(status_code=400, detail="Fournir soit 'years' soit 'year'")
    
    # Calculer les montants
    results = calculate_amounts_by_category_and_year(years_list, db)
    
    # Convertir les clés int en str pour la sérialisation JSON
    return {str(k): v for k, v in results.items()}


@router.get("/compte-resultat/data", response_model=CompteResultatDataListResponse)
async def get_compte_resultat_data(
    year: Optional[int] = Query(None, description="Filtrer par année"),
    category_name: Optional[str] = Query(None, description="Filtrer par catégorie"),
    db: Session = Depends(get_db)
):
    """
    Récupère les données brutes du compte de résultat.
    
    Args:
        year: Filtrer par année (optionnel)
        category_name: Filtrer par catégorie (optionnel)
        
    Returns:
        Liste des données
    """
    query = db.query(CompteResultatData)
    
    if year:
        query = query.filter(CompteResultatData.annee == year)
    if category_name:
        query = query.filter(CompteResultatData.category_name == category_name)
    
    data_list = query.order_by(
        CompteResultatData.annee.desc(),
        CompteResultatData.category_name
    ).all()
    
    return CompteResultatDataListResponse(
        data=[CompteResultatDataResponse.model_validate(d) for d in data_list],
        total=len(data_list)
    )


@router.delete("/compte-resultat/data/{data_id}", status_code=204)
async def delete_compte_resultat_data(
    data_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une donnée de compte de résultat.
    
    Args:
        data_id: ID de la donnée
        
    Raises:
        HTTPException: Si la donnée n'existe pas
    """
    data = db.query(CompteResultatData).filter(
        CompteResultatData.id == data_id
    ).first()
    
    if not data:
        raise HTTPException(status_code=404, detail="Donnée non trouvée")
    
    db.delete(data)
    db.commit()
    
    return None


@router.delete("/compte-resultat/year/{year}", status_code=204)
async def delete_compte_resultat_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Supprime toutes les données de compte de résultat pour une année.
    
    Args:
        year: Année à supprimer
    """
    db.query(CompteResultatData).filter(
        CompteResultatData.annee == year
    ).delete()
    
    db.commit()
    
    return None


# Routes pour les vues de mappings (Save/Load/Delete)
@router.get("/compte-resultat/mapping-views", response_model=CompteResultatMappingViewListResponse)
async def get_compte_resultat_mapping_views(
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les vues de mappings de compte de résultat.
    
    Returns:
        Liste de toutes les vues de mappings
    """
    views = db.query(CompteResultatMappingView).order_by(
        CompteResultatMappingView.created_at.desc()
    ).all()
    
    return CompteResultatMappingViewListResponse(
        views=[CompteResultatMappingViewResponse.model_validate(v) for v in views],
        total=len(views)
    )


@router.get("/compte-resultat/mapping-views/{view_id}", response_model=CompteResultatMappingViewResponse)
async def get_compte_resultat_mapping_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une vue de mapping par ID.
    
    Args:
        view_id: ID de la vue
        
    Returns:
        Vue de mapping
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(CompteResultatMappingView).filter(
        CompteResultatMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue de mapping non trouvée")
    
    return CompteResultatMappingViewResponse.model_validate(view)


@router.post("/compte-resultat/mapping-views", response_model=CompteResultatMappingViewResponse, status_code=201)
async def create_compte_resultat_mapping_view(
    view_data: CompteResultatMappingViewCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle vue de mapping.
    
    Args:
        view_data: Données de la vue à créer
        
    Returns:
        Vue créée
        
    Raises:
        HTTPException: Si une vue avec le même nom existe déjà
    """
    # Vérifier si une vue avec le même nom existe déjà
    existing = db.query(CompteResultatMappingView).filter(
        CompteResultatMappingView.name == view_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une vue avec le nom '{view_data.name}' existe déjà"
        )
    
    view = CompteResultatMappingView(
        name=view_data.name,
        view_data=view_data.view_data
    )
    
    db.add(view)
    db.commit()
    db.refresh(view)
    
    return CompteResultatMappingViewResponse.model_validate(view)


@router.put("/compte-resultat/mapping-views/{view_id}", response_model=CompteResultatMappingViewResponse)
async def update_compte_resultat_mapping_view(
    view_id: int,
    view_data: CompteResultatMappingViewUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour une vue de mapping.
    
    Args:
        view_id: ID de la vue
        view_data: Données à mettre à jour
        
    Returns:
        Vue mise à jour
        
    Raises:
        HTTPException: Si la vue n'existe pas ou si le nouveau nom existe déjà
    """
    view = db.query(CompteResultatMappingView).filter(
        CompteResultatMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue de mapping non trouvée")
    
    # Vérifier si le nouveau nom existe déjà (si le nom change)
    if view_data.name and view_data.name != view.name:
        existing = db.query(CompteResultatMappingView).filter(
            and_(
                CompteResultatMappingView.name == view_data.name,
                CompteResultatMappingView.id != view_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une vue avec le nom '{view_data.name}' existe déjà"
            )
    
    # Mettre à jour les champs fournis
    update_data = view_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(view, key, value)
    
    view.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(view)
    
    return CompteResultatMappingViewResponse.model_validate(view)


@router.delete("/compte-resultat/mapping-views/{view_id}", status_code=204)
async def delete_compte_resultat_mapping_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une vue de mapping.
    
    Args:
        view_id: ID de la vue
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(CompteResultatMappingView).filter(
        CompteResultatMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue de mapping non trouvée")
    
    db.delete(view)
    db.commit()
    
    return None

