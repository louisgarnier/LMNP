"""
API routes for bilan (balance sheet).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.database import get_db
from backend.database.models import (
    BilanMapping,
    BilanData,
    BilanMappingView
)
from backend.api.models import (
    BilanMappingCreate,
    BilanMappingUpdate,
    BilanMappingResponse,
    BilanMappingListResponse,
    BilanDataResponse,
    BilanDataListResponse,
    BilanGenerateRequest,
    BilanResponse,
    BilanTypeItem,
    BilanSubCategoryItem,
    BilanCategoryItem,
    BilanMappingViewResponse,
    BilanMappingViewCreate,
    BilanMappingViewUpdate,
    BilanMappingViewListResponse
)
from backend.api.services.bilan_service import (
    get_mappings,
    calculate_bilan,
    invalidate_all_bilan,
    invalidate_bilan_for_year,
    get_bilan_data
)

router = APIRouter()


@router.get("/bilan/mappings", response_model=BilanMappingListResponse)
async def get_bilan_mappings(
    db: Session = Depends(get_db)
):
    """
    Récupère tous les mappings de bilan.
    
    Returns:
        Liste de tous les mappings
    """
    mappings = db.query(BilanMapping).order_by(
        BilanMapping.type,
        BilanMapping.sub_category,
        BilanMapping.category_name
    ).all()
    
    return BilanMappingListResponse(
        mappings=[BilanMappingResponse.model_validate(m) for m in mappings],
        total=len(mappings)
    )


@router.get("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def get_bilan_mapping(
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
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    return BilanMappingResponse.model_validate(mapping)


@router.post("/bilan/mappings", response_model=BilanMappingResponse, status_code=201)
async def create_bilan_mapping(
    mapping_data: BilanMappingCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau mapping.
    
    Args:
        mapping_data: Données du mapping à créer
        
    Returns:
        Mapping créé
    """
    mapping = BilanMapping(
        category_name=mapping_data.category_name,
        level_1_values=mapping_data.level_1_values,
        type=mapping_data.type,
        sub_category=mapping_data.sub_category,
        is_special=mapping_data.is_special,
        special_source=mapping_data.special_source,
        amortization_view_id=mapping_data.amortization_view_id,
        compte_resultat_view_id=mapping_data.compte_resultat_view_id
    )
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    # Invalider tous les bilans (les mappings ont changé)
    invalidate_all_bilan(db)
    
    return BilanMappingResponse.model_validate(mapping)


@router.put("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def update_bilan_mapping(
    mapping_id: int,
    mapping_data: BilanMappingUpdate,
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
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    # Mettre à jour les champs fournis
    update_data = mapping_data.model_dump(exclude_unset=True)
    
    if 'category_name' in update_data:
        mapping.category_name = update_data['category_name']
    if 'level_1_values' in update_data:
        mapping.level_1_values = update_data['level_1_values']
    if 'type' in update_data:
        mapping.type = update_data['type']
    if 'sub_category' in update_data:
        mapping.sub_category = update_data['sub_category']
    if 'is_special' in update_data:
        mapping.is_special = update_data['is_special']
    if 'special_source' in update_data:
        mapping.special_source = update_data['special_source']
    if 'amortization_view_id' in update_data:
        mapping.amortization_view_id = update_data['amortization_view_id']
    if 'compte_resultat_view_id' in update_data:
        mapping.compte_resultat_view_id = update_data['compte_resultat_view_id']
    
    db.commit()
    db.refresh(mapping)
    
    # Invalider tous les bilans (les mappings ont changé)
    invalidate_all_bilan(db)
    
    return BilanMappingResponse.model_validate(mapping)


@router.delete("/bilan/mappings/{mapping_id}", status_code=204)
async def delete_bilan_mapping(
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
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    db.delete(mapping)
    db.commit()
    
    # Invalider tous les bilans (les mappings ont changé)
    invalidate_all_bilan(db)
    
    return None


@router.post("/bilan/generate", response_model=BilanResponse)
async def generate_bilan(
    request: BilanGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Génère un bilan pour une année donnée avec structure hiérarchique.
    
    Args:
        request: Requête avec year et selected_level_3_values
        
    Returns:
        Bilan calculé avec structure hiérarchique
    """
    # Récupérer les mappings
    mappings = get_mappings(db)
    
    if not mappings:
        raise HTTPException(status_code=400, detail="Aucun mapping configuré")
    
    # Calculer le bilan
    result = calculate_bilan(
        request.year,
        mappings,
        request.selected_level_3_values,
        db
    )
    
    # Supprimer les anciennes données pour cette année
    db.query(BilanData).filter(
        BilanData.annee == request.year
    ).delete()
    
    # Stocker les résultats en base de données
    for category_name, amount in result["categories"].items():
        data = BilanData(
            annee=request.year,
            category_name=category_name,
            amount=amount
        )
        db.add(data)
    
    db.commit()
    
    # Construire la structure hiérarchique
    types_dict: Dict[str, Dict[str, List[BilanCategoryItem]]] = {}
    
    # Grouper par type puis par sous-catégorie
    for mapping in mappings:
        type_name = mapping.type
        sub_cat = mapping.sub_category
        category_name = mapping.category_name
        amount = result["categories"].get(category_name, 0.0)
        
        if type_name not in types_dict:
            types_dict[type_name] = {}
        
        if sub_cat not in types_dict[type_name]:
            types_dict[type_name][sub_cat] = []
        
        types_dict[type_name][sub_cat].append(
            BilanCategoryItem(
                category_name=category_name,
                amount=amount
            )
        )
    
    # Construire les BilanTypeItem avec sous-catégories
    type_items: List[BilanTypeItem] = []
    
    for type_name in ["ACTIF", "PASSIF"]:  # Ordre fixe
        if type_name not in types_dict:
            continue
        
        sub_category_items: List[BilanSubCategoryItem] = []
        
        for sub_cat, categories in types_dict[type_name].items():
            total = result["sub_category_totals"].get(sub_cat, 0.0)
            sub_category_items.append(
                BilanSubCategoryItem(
                    sub_category=sub_cat,
                    total=total,
                    categories=categories
                )
            )
        
        type_total = result["type_totals"].get(type_name, 0.0)
        type_items.append(
            BilanTypeItem(
                type=type_name,
                total=type_total,
                sub_categories=sub_category_items
            )
        )
    
    return BilanResponse(
        year=request.year,
        types=type_items,
        equilibre=result["equilibre"]
    )


@router.get("/bilan/calculate")
async def calculate_bilan_amounts(
    years: Optional[str] = Query(None, description="Années séparées par des virgules (ex: 2023,2024)"),
    year: Optional[int] = Query(None, description="Année unique"),
    selected_level_3_values: Optional[str] = Query(None, description="Level 3 values séparés par des virgules"),
    db: Session = Depends(get_db)
):
    """
    Calcule les montants du bilan à la volée (comme le compte de résultat).
    
    Cette fonction calcule directement depuis les transactions sans stocker dans BilanData.
    Pour chaque catégorie :
    - Si mapping level_1 : calcule depuis les transactions (cumul jusqu'à fin d'année)
    - Si catégorie spéciale : utilise la source spéciale (amortissements, compte bancaire, etc.)
    
    Args:
        years: Années séparées par des virgules (ex: "2023,2024")
        year: Année unique (alternative à years)
        selected_level_3_values: Level 3 values séparés par des virgules (optionnel)
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
    
    # Parser selected_level_3_values si fourni
    level_3_list = None
    if selected_level_3_values:
        level_3_list = [v.strip() for v in selected_level_3_values.split(',')]
    
    # Récupérer les mappings
    mappings = get_mappings(db)
    
    if not mappings:
        raise HTTPException(status_code=400, detail="Aucun mapping configuré")
    
    # Calculer pour chaque année
    results: Dict[str, Dict[str, float]] = {}
    
    for year_val in years_list:
        # Calculer le bilan pour cette année
        result = calculate_bilan(year_val, mappings, level_3_list, db)
        
        # Extraire les catégories
        results[str(year_val)] = result["categories"]
    
    return results


@router.get("/bilan", response_model=BilanDataListResponse)
async def get_bilan(
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début"),
    end_year: Optional[int] = Query(None, description="Année de fin"),
    db: Session = Depends(get_db)
):
    """
    Récupère les données du bilan (depuis la table BilanData - données pré-calculées).
    
    NOTE: Pour un calcul à la volée, utilisez /api/bilan/calculate à la place.
    
    Args:
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel)
        end_year: Année de fin (optionnel)
        
    Returns:
        Liste des données du bilan
    """
    data_list = get_bilan_data(db, year, start_year, end_year)
    
    return BilanDataListResponse(
        data=[BilanDataResponse.model_validate(d) for d in data_list],
        total=len(data_list)
    )


# Bilan Mapping Views Endpoints

@router.get("/bilan/mapping-views", response_model=BilanMappingViewListResponse)
async def get_bilan_mapping_views(
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les vues de mapping de bilan.
    
    Returns:
        Liste de toutes les vues
    """
    views = db.query(BilanMappingView).order_by(
        BilanMappingView.name
    ).all()
    
    return BilanMappingViewListResponse(
        views=[BilanMappingViewResponse.model_validate(v) for v in views],
        total=len(views)
    )


@router.get("/bilan/mapping-views/{view_id}", response_model=BilanMappingViewResponse)
async def get_bilan_mapping_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une vue par ID.
    
    Args:
        view_id: ID de la vue
        
    Returns:
        Vue
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(BilanMappingView).filter(
        BilanMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue non trouvée")
    
    return BilanMappingViewResponse.model_validate(view)


@router.post("/bilan/mapping-views", response_model=BilanMappingViewResponse, status_code=201)
async def create_bilan_mapping_view(
    view_data: BilanMappingViewCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle vue.
    
    Args:
        view_data: Données de la vue à créer
        
    Returns:
        Vue créée
        
    Raises:
        HTTPException: Si une vue avec le même nom existe déjà
    """
    # Vérifier si une vue avec le même nom existe déjà
    existing = db.query(BilanMappingView).filter(
        BilanMappingView.name == view_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Une vue avec ce nom existe déjà")
    
    view = BilanMappingView(
        name=view_data.name,
        view_data=view_data.view_data
    )
    
    db.add(view)
    db.commit()
    db.refresh(view)
    
    return BilanMappingViewResponse.model_validate(view)


@router.put("/bilan/mapping-views/{view_id}", response_model=BilanMappingViewResponse)
async def update_bilan_mapping_view(
    view_id: int,
    view_data: BilanMappingViewUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour une vue.
    
    Args:
        view_id: ID de la vue
        view_data: Données à mettre à jour
        
    Returns:
        Vue mise à jour
        
    Raises:
        HTTPException: Si la vue n'existe pas ou si le nouveau nom existe déjà
    """
    view = db.query(BilanMappingView).filter(
        BilanMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue non trouvée")
    
    update_data = view_data.model_dump(exclude_unset=True)
    
    if 'name' in update_data:
        # Vérifier si le nouveau nom existe déjà (sauf pour cette vue)
        existing = db.query(BilanMappingView).filter(
            and_(
                BilanMappingView.name == update_data['name'],
                BilanMappingView.id != view_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Une vue avec ce nom existe déjà")
        
        view.name = update_data['name']
    
    if 'view_data' in update_data:
        view.view_data = update_data['view_data']
    
    db.commit()
    db.refresh(view)
    
    return BilanMappingViewResponse.model_validate(view)


@router.delete("/bilan/mapping-views/{view_id}", status_code=204)
async def delete_bilan_mapping_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une vue.
    
    Args:
        view_id: ID de la vue
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(BilanMappingView).filter(
        BilanMappingView.id == view_id
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue non trouvée")
    
    db.delete(view)
    db.commit()
    
    return None

