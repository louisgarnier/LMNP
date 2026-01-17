"""
API routes for bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from backend.database import get_db
from backend.database.models import (
    BilanMapping,
    BilanData,
    BilanConfig
)
from backend.api.models import (
    BilanMappingCreate,
    BilanMappingUpdate,
    BilanMappingResponse,
    BilanMappingListResponse,
    BilanDataResponse,
    BilanDataListResponse,
    BilanConfigResponse,
    BilanConfigUpdate,
    BilanCalculateRequest,
    BilanResponse,
    BilanCategoryItem,
    BilanSubCategoryItem,
    BilanTypeItem
)
from backend.api.services.bilan_service import (
    get_mappings,
    get_level_3_values,
    calculate_bilan,
    get_bilan_data,
    invalidate_all_bilan,
    invalidate_bilan_for_year
)

router = APIRouter()


def build_hierarchical_structure(
    year: int,
    categories: dict,
    mappings: List[BilanMapping]
) -> BilanResponse:
    """
    Construire la structure hiérarchique du bilan à partir des catégories et mappings.
    
    Args:
        year: Année du bilan
        categories: Dictionnaire {category_name: amount}
        mappings: Liste des mappings
    
    Returns:
        BilanResponse avec structure hiérarchique
    """
    # Créer un dictionnaire pour mapper category_name -> mapping
    mapping_dict = {m.category_name: m for m in mappings}
    
    # Grouper par type (ACTIF/PASSIF)
    types_dict = {}
    
    for category_name, amount in categories.items():
        mapping = mapping_dict.get(category_name)
        if not mapping:
            continue
        
        type_name = mapping.type
        sub_category = mapping.sub_category
        
        # Initialiser le type si nécessaire
        if type_name not in types_dict:
            types_dict[type_name] = {}
        
        # Initialiser la sous-catégorie si nécessaire
        if sub_category not in types_dict[type_name]:
            types_dict[type_name][sub_category] = []
        
        # Ajouter la catégorie
        category_item = BilanCategoryItem(
            category_name=category_name,
            amount=amount,
            is_special=mapping.is_special
        )
        types_dict[type_name][sub_category].append(category_item)
    
    # Construire la structure hiérarchique
    type_items = []
    actif_total = 0.0
    passif_total = 0.0
    
    for type_name in ["ACTIF", "PASSIF"]:
        if type_name not in types_dict:
            continue
        
        sub_category_items = []
        type_total = 0.0
        
        for sub_category, categories_list in types_dict[type_name].items():
            sub_category_total = sum(cat.amount for cat in categories_list)
            type_total += sub_category_total
            
            sub_category_item = BilanSubCategoryItem(
                sub_category=sub_category,
                total=sub_category_total,
                categories=categories_list
            )
            sub_category_items.append(sub_category_item)
        
        if type_name == "ACTIF":
            actif_total = type_total
        else:
            passif_total = type_total
        
        type_item = BilanTypeItem(
            type=type_name,
            total=type_total,
            sub_categories=sub_category_items
        )
        type_items.append(type_item)
    
    # Calculer la différence
    difference = actif_total - passif_total
    if passif_total != 0:
        difference_percent = (difference / passif_total) * 100
    elif actif_total != 0:
        difference_percent = 100.0
    else:
        difference_percent = 0.0
    
    return BilanResponse(
        year=year,
        types=type_items,
        actif_total=actif_total,
        passif_total=passif_total,
        difference=difference,
        difference_percent=difference_percent
    )


# ========== Mappings Endpoints ==========

@router.get("/bilan/mappings", response_model=BilanMappingListResponse)
async def get_bilan_mappings(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings pour le bilan.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    query = db.query(BilanMapping)
    total = query.count()
    
    mappings = query.offset(skip).limit(limit).all()
    
    mapping_responses = [
        BilanMappingResponse(
            id=m.id,
            category_name=m.category_name,
            type=m.type,
            sub_category=m.sub_category,
            level_1_values=m.level_1_values,
            is_special=m.is_special,
            special_source=m.special_source,
            compte_resultat_view_id=m.compte_resultat_view_id,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]
    
    return BilanMappingListResponse(
        items=mapping_responses,
        total=total
    )


@router.get("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def get_bilan_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'un mapping.
    
    - **mapping_id**: ID du mapping
    """
    mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable")
    
    return BilanMappingResponse(
        id=mapping.id,
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        level_1_values=mapping.level_1_values,
        is_special=mapping.is_special,
        special_source=mapping.special_source,
        compte_resultat_view_id=mapping.compte_resultat_view_id,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )


@router.post("/bilan/mappings", response_model=BilanMappingResponse, status_code=201)
async def create_bilan_mapping(
    mapping: BilanMappingCreate,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau mapping pour le bilan.
    """
    # Vérifier si un mapping avec le même category_name existe déjà
    existing = db.query(BilanMapping).filter(
        BilanMapping.category_name == mapping.category_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà"
        )
    
    new_mapping = BilanMapping(
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        level_1_values=mapping.level_1_values,
        is_special=mapping.is_special,
        special_source=mapping.special_source,
        compte_resultat_view_id=mapping.compte_resultat_view_id
    )
    
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    # Invalider tous les bilans (les mappings ont changé)
    try:
        invalidate_all_bilan(db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_bilan_mapping] Erreur lors de l'invalidation des bilans: {error_details}")
    
    return BilanMappingResponse(
        id=new_mapping.id,
        category_name=new_mapping.category_name,
        type=new_mapping.type,
        sub_category=new_mapping.sub_category,
        level_1_values=new_mapping.level_1_values,
        is_special=new_mapping.is_special,
        special_source=new_mapping.special_source,
        compte_resultat_view_id=new_mapping.compte_resultat_view_id,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )


@router.put("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def update_bilan_mapping(
    mapping_id: int,
    mapping_update: BilanMappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour un mapping.
    
    - **mapping_id**: ID du mapping à mettre à jour
    """
    mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable")
    
    # Mettre à jour les champs fournis
    if mapping_update.category_name is not None:
        mapping.category_name = mapping_update.category_name
    if mapping_update.type is not None:
        mapping.type = mapping_update.type
    if mapping_update.sub_category is not None:
        mapping.sub_category = mapping_update.sub_category
    if mapping_update.level_1_values is not None:
        mapping.level_1_values = mapping_update.level_1_values
    if mapping_update.is_special is not None:
        mapping.is_special = mapping_update.is_special
    if mapping_update.special_source is not None:
        mapping.special_source = mapping_update.special_source
    if mapping_update.compte_resultat_view_id is not None:
        mapping.compte_resultat_view_id = mapping_update.compte_resultat_view_id
    
    db.commit()
    db.refresh(mapping)
    
    # Invalider tous les bilans (les mappings ont changé)
    try:
        invalidate_all_bilan(db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_bilan_mapping] Erreur lors de l'invalidation des bilans: {error_details}")
    
    return BilanMappingResponse(
        id=mapping.id,
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        level_1_values=mapping.level_1_values,
        is_special=mapping.is_special,
        special_source=mapping.special_source,
        compte_resultat_view_id=mapping.compte_resultat_view_id,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )


@router.delete("/bilan/mappings/{mapping_id}", status_code=204)
async def delete_bilan_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping.
    
    - **mapping_id**: ID du mapping à supprimer
    """
    mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable")
    
    db.delete(mapping)
    db.commit()
    
    # Invalider tous les bilans (les mappings ont changé)
    try:
        invalidate_all_bilan(db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [delete_bilan_mapping] Erreur lors de l'invalidation des bilans: {error_details}")
    
    return None


# ========== Calculate Endpoint ==========

@router.post("/bilan/calculate", response_model=BilanResponse)
async def calculate_bilan_endpoint(
    request: BilanCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Générer le bilan pour une année avec structure hiérarchique.
    
    - **year**: Année à calculer
    - **selected_level_3_values**: Liste des valeurs level_3 à considérer (optionnel)
    """
    # Utiliser les level_3_values fournis ou ceux de la config
    level_3_values = request.selected_level_3_values
    if level_3_values is None:
        level_3_values = get_level_3_values(db)
    
    # Calculer le bilan
    result = calculate_bilan(db, request.year, None, level_3_values)
    
    # Récupérer les mappings pour construire la structure hiérarchique
    mappings = get_mappings(db)
    
    # Construire la structure hiérarchique
    bilan_response = build_hierarchical_structure(
        request.year,
        result["categories"],
        mappings
    )
    
    return bilan_response


# ========== Data Endpoints ==========

@router.get("/bilan", response_model=BilanDataListResponse)
async def get_bilan(
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début (pour plusieurs années)"),
    end_year: Optional[int] = Query(None, description="Année de fin (pour plusieurs années)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les données du bilan stockées.
    
    - **year**: Année spécifique (optionnel)
    - **start_year**: Année de début (pour plusieurs années, optionnel)
    - **end_year**: Année de fin (pour plusieurs années, optionnel)
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    # Récupérer les données avec filtres
    data_list = get_bilan_data(db, year, start_year, end_year)
    
    total = len(data_list)
    
    # Pagination
    paginated_data = data_list[skip:skip + limit]
    
    data_responses = [
        BilanDataResponse(
            id=d.id,
            annee=d.annee,
            category_name=d.category_name,
            amount=d.amount,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in paginated_data
    ]
    
    return BilanDataListResponse(
        items=data_responses,
        total=total
    )


# ========== Config Endpoints ==========

@router.get("/bilan/config", response_model=BilanConfigResponse)
async def get_bilan_config(
    db: Session = Depends(get_db)
):
    """
    Récupérer la configuration du bilan (level_3_values).
    """
    config = db.query(BilanConfig).first()
    
    if not config:
        # Créer une config par défaut si elle n'existe pas
        config = BilanConfig(level_3_values="[]")
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return BilanConfigResponse(
        id=config.id,
        level_3_values=config.level_3_values,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/bilan/config", response_model=BilanConfigResponse)
async def update_bilan_config(
    config_update: BilanConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour la configuration du bilan (level_3_values).
    """
    config = db.query(BilanConfig).first()
    
    if not config:
        # Créer une config si elle n'existe pas
        config = BilanConfig(level_3_values=config_update.level_3_values or "[]")
        db.add(config)
    else:
        # Mettre à jour
        if config_update.level_3_values is not None:
            config.level_3_values = config_update.level_3_values
    
    db.commit()
    db.refresh(config)
    
    # Invalider tous les bilans (la config a changé)
    try:
        invalidate_all_bilan(db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_bilan_config] Erreur lors de l'invalidation des bilans: {error_details}")
    
    return BilanConfigResponse(
        id=config.id,
        level_3_values=config.level_3_values,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
