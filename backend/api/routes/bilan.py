"""
API routes for bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from backend.database import get_db
from backend.database.models import (
    BilanMapping,
    BilanConfig,
    Transaction
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
    sync_bilan_mapping_categories,
    labels_from_bilan_mapping_categories,
    special_source_for_mapping,
    LINE_CODE_BY_SPECIAL_SOURCE,
)
from backend.api.utils.validation import validate_property_id

router = APIRouter()
logger = logging.getLogger(__name__)


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
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings pour le bilan d'une propriété.
    
    - **property_id**: ID de la propriété (obligatoire)
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    logger.info(f"[Bilan] GET /api/bilan/mappings - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")
    
    query = db.query(BilanMapping).filter(BilanMapping.property_id == property_id)
    total = query.count()
    
    mappings = query.offset(skip).limit(limit).all()
    
    mapping_responses = [
        BilanMappingResponse(
            id=m.id,
            category_name=m.category_name,
            type=m.type,
            sub_category=m.sub_category,
            level_1_values=labels_from_bilan_mapping_categories(m),  # reconstruit depuis la liaison (Task 6)
            is_special=m.is_special,
            special_source=special_source_for_mapping(m),  # reconstruit depuis line_code (Task 8)
            compte_resultat_view_id=m.compte_resultat_view_id,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]
    
    logger.info(f"[Bilan] Retourné {len(mapping_responses)} mappings pour property_id={property_id}")
    return BilanMappingListResponse(
        items=mapping_responses,
        total=total
    )


@router.get("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def get_bilan_mapping(
    mapping_id: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'un mapping.
    
    - **mapping_id**: ID du mapping
    - **property_id**: ID de la propriété (obligatoire)
    """
    logger.info(f"[Bilan] GET /api/bilan/mappings/{mapping_id} - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")
    
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id,
        BilanMapping.property_id == property_id
    ).first()
    
    if not mapping:
        logger.error(f"[Bilan] Mapping {mapping_id} introuvable pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable pour cette propriété")
    
    return BilanMappingResponse(
        id=mapping.id,
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        level_1_values=labels_from_bilan_mapping_categories(mapping),  # reconstruit depuis la liaison (Task 6)
        is_special=mapping.is_special,
        special_source=special_source_for_mapping(mapping),  # reconstruit depuis line_code (Task 8)
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
    logger.info(f"[Bilan] POST /api/bilan/mappings - property_id={mapping.property_id}")
    validate_property_id(db, mapping.property_id, "Bilan")
    
    # Vérifier si un mapping avec le même category_name existe déjà pour cette propriété
    existing = db.query(BilanMapping).filter(
        BilanMapping.category_name == mapping.category_name,
        BilanMapping.property_id == mapping.property_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà pour cette propriété"
        )
    
    # Étape 2 Task 8 : `special_source` (label métier envoyé par le frontend)
    # est traduit en `line_code` stable côté serveur ; la colonne `special_source`
    # a été retirée du modèle. Pour une ligne normale, line_code reste NULL.
    line_code = (
        LINE_CODE_BY_SPECIAL_SOURCE.get(mapping.special_source)
        if mapping.is_special else None
    )
    new_mapping = BilanMapping(
        property_id=mapping.property_id,
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        is_special=mapping.is_special,
        line_code=line_code,
        compte_resultat_view_id=mapping.compte_resultat_view_id
    )

    db.add(new_mapping)
    db.flush()  # obtenir new_mapping.id avant de poser la liaison

    # Liaison category_id (unique source de lecture — Task 6). Les lignes
    # spéciales n'ont pas de level_1_values (liaison vide).
    if not new_mapping.is_special:
        sync_bilan_mapping_categories(db, new_mapping, mapping.level_1_values)

    db.commit()
    db.refresh(new_mapping)

    logger.info(f"[Bilan] Mapping créé: id={new_mapping.id}, property_id={mapping.property_id}")
    return BilanMappingResponse(
        id=new_mapping.id,
        category_name=new_mapping.category_name,
        type=new_mapping.type,
        sub_category=new_mapping.sub_category,
        level_1_values=labels_from_bilan_mapping_categories(new_mapping),
        is_special=new_mapping.is_special,
        special_source=special_source_for_mapping(new_mapping),  # reconstruit depuis line_code (Task 8)
        compte_resultat_view_id=new_mapping.compte_resultat_view_id,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )


@router.put("/bilan/mappings/{mapping_id}", response_model=BilanMappingResponse)
async def update_bilan_mapping(
    mapping_id: int,
    mapping_update: BilanMappingUpdate,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour un mapping.
    
    - **mapping_id**: ID du mapping à mettre à jour
    - **property_id**: ID de la propriété (obligatoire)
    """
    logger.info(f"[Bilan] PUT /api/bilan/mappings/{mapping_id} - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")
    
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id,
        BilanMapping.property_id == property_id
    ).first()
    
    if not mapping:
        logger.error(f"[Bilan] Mapping {mapping_id} introuvable pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable pour cette propriété")
    
    # Mettre à jour les champs fournis
    if mapping_update.category_name is not None:
        mapping.category_name = mapping_update.category_name
    if mapping_update.type is not None:
        mapping.type = mapping_update.type
    if mapping_update.sub_category is not None:
        mapping.sub_category = mapping_update.sub_category
    if mapping_update.is_special is not None:
        mapping.is_special = mapping_update.is_special
    # Étape 2 Task 8 : `special_source` reçu est traduit en `line_code` stable
    # (colonne `special_source` retirée du modèle).
    if mapping_update.special_source is not None:
        mapping.line_code = LINE_CODE_BY_SPECIAL_SOURCE.get(mapping_update.special_source)
    if mapping_update.compte_resultat_view_id is not None:
        mapping.compte_resultat_view_id = mapping_update.compte_resultat_view_id

    # Reconstruire la liaison category_id (unique source de lecture — Task 6)
    # quand les labels changent, sur les lignes normales uniquement.
    if mapping_update.level_1_values is not None and not mapping.is_special:
        sync_bilan_mapping_categories(db, mapping, mapping_update.level_1_values)

    db.commit()
    db.refresh(mapping)

    logger.info(f"[Bilan] Mapping {mapping_id} mis à jour pour property_id={property_id}")
    return BilanMappingResponse(
        id=mapping.id,
        category_name=mapping.category_name,
        type=mapping.type,
        sub_category=mapping.sub_category,
        level_1_values=labels_from_bilan_mapping_categories(mapping),
        is_special=mapping.is_special,
        special_source=special_source_for_mapping(mapping),  # reconstruit depuis line_code (Task 8)
        compte_resultat_view_id=mapping.compte_resultat_view_id,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )


@router.delete("/bilan/mappings/{mapping_id}", status_code=204)
async def delete_bilan_mapping(
    mapping_id: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping.
    
    - **mapping_id**: ID du mapping à supprimer
    - **property_id**: ID de la propriété (obligatoire)
    """
    logger.info(f"[Bilan] DELETE /api/bilan/mappings/{mapping_id} - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")
    
    mapping = db.query(BilanMapping).filter(
        BilanMapping.id == mapping_id,
        BilanMapping.property_id == property_id
    ).first()
    
    if not mapping:
        logger.error(f"[Bilan] Mapping {mapping_id} introuvable pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Mapping avec l'ID {mapping_id} introuvable pour cette propriété")
    
    db.delete(mapping)
    db.commit()

    logger.info(f"[Bilan] Mapping {mapping_id} supprimé pour property_id={property_id}")
    return None


# ========== Calculate Endpoint ==========

@router.get("/bilan/calculate")
async def calculate_bilan_multiple_years_endpoint(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    years: str = Query(..., description="Années à calculer (séparées par des virgules, ex: '2021,2022,2023')"),
    db: Session = Depends(get_db)
):
    """
    Calculer le bilan pour plusieurs années en une fois (comme compte de résultat).
    
    - **property_id**: ID de la propriété (obligatoire)
    - **years**: Années à calculer (séparées par des virgules, ex: '2021,2022,2023')
    
    Returns:
        Dictionnaire avec les bilans par année
    """
    import time
    start_time = time.time()
    
    logger.info(f"[Bilan] GET /api/bilan/calculate - property_id={property_id}, years={years}")
    validate_property_id(db, property_id, "Bilan")
    
    try:
        year_list = [int(y.strip()) for y in years.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Format d'années invalide. Utilisez des nombres séparés par des virgules.")
    
    # Récupérer les level_3_values depuis la config pour cette propriété
    level_3_values = get_level_3_values(db, property_id)
    
    # Récupérer les mappings une seule fois pour cette propriété
    mappings = get_mappings(db, property_id)
    
    # OPTIMISATION: Pré-calculer tous les résultats de compte de résultat une
    # seule fois par année, et les passer à calculate_bilan (mémoïsation de
    # portée requête). Cela évite que le résultat de l'exercice et le report à
    # nouveau ne recalculent le compte de résultat à chaque année.
    from backend.api.services.compte_resultat_service import calculate_compte_resultat
    compte_resultat_cache = {}
    for year in year_list:
        compte_resultat_cache[year] = calculate_compte_resultat(db, year, property_id=property_id, skip_prorata=True)

    # Calculer le bilan pour chaque année (en réutilisant le cache CR)
    results = {}
    for year in year_list:
        # Calculer le bilan
        result = calculate_bilan(
            db, year, property_id, mappings, level_3_values,
            cr_cache=compte_resultat_cache
        )
        
        # Construire la structure hiérarchique
        bilan_response = build_hierarchical_structure(
            year,
            result["categories"],
            mappings
        )
        results[year] = bilan_response
    
    elapsed = time.time() - start_time
    logger.info(f"[Bilan] Calcul pour {len(year_list)} années terminé en {elapsed:.2f}s - property_id={property_id}")
    
    return {
        "years": year_list,
        "results": results
    }


@router.post("/bilan/calculate", response_model=BilanResponse)
async def calculate_bilan_endpoint(
    request: BilanCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Générer le bilan pour une année avec structure hiérarchique.
    
    - **property_id**: ID de la propriété (obligatoire)
    - **year**: Année à calculer
    - **selected_level_3_values**: Liste des valeurs level_3 à considérer (optionnel)
    """
    logger.info(f"[Bilan] POST /api/bilan/calculate - property_id={request.property_id}, year={request.year}")
    validate_property_id(db, request.property_id, "Bilan")
    
    # Utiliser les level_3_values fournis ou ceux de la config
    level_3_values = request.selected_level_3_values
    if level_3_values is None:
        level_3_values = get_level_3_values(db, request.property_id)
    
    # Calculer le bilan
    result = calculate_bilan(db, request.year, request.property_id, None, level_3_values)
    
    # Récupérer les mappings pour construire la structure hiérarchique
    mappings = get_mappings(db, request.property_id)
    
    # Construire la structure hiérarchique
    bilan_response = build_hierarchical_structure(
        request.year,
        result["categories"],
        mappings
    )
    
    logger.info(f"[Bilan] Calcul terminé pour year={request.year}, property_id={request.property_id}")
    return bilan_response


# ========== Data Endpoints ==========

@router.get("/bilan", response_model=BilanDataListResponse)
async def get_bilan(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début (pour plusieurs années)"),
    end_year: Optional[int] = Query(None, description="Année de fin (pour plusieurs années)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer le bilan d'une propriété, CALCULÉ EN TEMPS RÉEL (une ligne par
    catégorie et par année). Plus aucun cache : le résultat reflète
    immédiatement toute modification des données sources.

    Les filtres year / start_year / end_year sélectionnent les années à
    renvoyer parmi celles où la propriété possède des transactions.
    """
    logger.info(f"[Bilan] GET /api/bilan - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")

    # Déterminer les années à calculer
    if year is not None:
        selected_years = [year]
    else:
        rows = db.query(Transaction.date).filter(
            Transaction.property_id == property_id
        ).all()
        candidate_years = sorted({d[0].year for d in rows})
        selected_years = [
            y for y in candidate_years
            if (start_year is None or y >= start_year)
            and (end_year is None or y <= end_year)
        ]

    mappings = get_mappings(db, property_id)
    level_3_values = get_level_3_values(db, property_id)

    # Mémoïsation du compte de résultat (portée requête) partagée entre années
    from backend.api.services.compte_resultat_service import calculate_compte_resultat
    cr_cache = {y: calculate_compte_resultat(db, y, property_id=property_id, skip_prorata=True) for y in selected_years}

    # Construire les lignes (une par catégorie, comme l'ancienne table de cache)
    data_rows = []
    for y in selected_years:
        result = calculate_bilan(
            db, y, property_id, mappings, level_3_values, cr_cache=cr_cache
        )
        for category_name, amount in result["categories"].items():
            data_rows.append((y, category_name, amount))

    # Tri déterministe par (année, catégorie)
    data_rows.sort(key=lambda r: (r[0], r[1]))

    total = len(data_rows)
    paginated = data_rows[skip:skip + limit]

    data_responses = [
        BilanDataResponse(annee=annee, category_name=category_name, amount=amount)
        for annee, category_name, amount in paginated
    ]

    logger.info(f"[Bilan] Calculé {total} lignes en temps réel pour property_id={property_id}")
    return BilanDataListResponse(
        items=data_responses,
        total=total
    )


# ========== Config Endpoints ==========

@router.get("/bilan/config", response_model=BilanConfigResponse)
async def get_bilan_config(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la configuration du bilan (level_3_values) pour une propriété.
    
    - **property_id**: ID de la propriété (obligatoire)
    """
    logger.info(f"[Bilan] GET /api/bilan/config - property_id={property_id}")
    validate_property_id(db, property_id, "Bilan")
    
    config = db.query(BilanConfig).filter(BilanConfig.property_id == property_id).first()
    
    if not config:
        # Créer une config par défaut si elle n'existe pas pour cette propriété
        config = BilanConfig(property_id=property_id, level_3_values="[]")
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
    
    Le property_id doit être fourni dans le body.
    """
    if not config_update.property_id:
        raise HTTPException(status_code=422, detail="property_id est obligatoire")
    
    logger.info(f"[Bilan] PUT /api/bilan/config - property_id={config_update.property_id}")
    validate_property_id(db, config_update.property_id, "Bilan")
    
    config = db.query(BilanConfig).filter(BilanConfig.property_id == config_update.property_id).first()
    
    if not config:
        # Créer une config si elle n'existe pas
        config = BilanConfig(
            property_id=config_update.property_id,
            level_3_values=config_update.level_3_values or "[]"
        )
        db.add(config)
    else:
        # Mettre à jour
        if config_update.level_3_values is not None:
            config.level_3_values = config_update.level_3_values
    
    db.commit()
    db.refresh(config)

    logger.info(f"[Bilan] Config mise à jour pour property_id={config_update.property_id}")
    return BilanConfigResponse(
        id=config.id,
        level_3_values=config.level_3_values,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
