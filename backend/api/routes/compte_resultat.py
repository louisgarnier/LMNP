"""
API routes for compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Phase 11 : Tous les endpoints acceptent property_id pour l'isolation multi-propriétés.
Tâche 7 : les états sont calculés EN TEMPS RÉEL. Il n'existe plus de table de
cache (compte_resultat_data) ni d'endpoint /generate ni d'invalidation : le GET
principal réutilise directement calculate_compte_resultat.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.database.models import (
    CompteResultatMapping,
    CompteResultatConfig,
    CompteResultatOverride,
    Transaction,
)
from backend.api.models import (
    CompteResultatMappingCreate,
    CompteResultatMappingUpdate,
    CompteResultatMappingResponse,
    CompteResultatMappingListResponse,
    CompteResultatDataResponse,
    CompteResultatDataListResponse,
    CompteResultatConfigResponse,
    CompteResultatConfigUpdate,
    CompteResultatOverrideCreate,
    CompteResultatOverrideUpdate,
    CompteResultatOverrideResponse
)
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_compte_resultat,
    sync_mapping_categories,
    labels_from_mapping_categories,
)
from backend.api.utils.validation import validate_property_id

# Logger configuration
logger = logging.getLogger(__name__)

router = APIRouter()


def _data_years_for_property(db: Session, property_id: int) -> List[int]:
    """Retourne la liste triée des années où la propriété a des transactions."""
    rows = db.query(Transaction.date).filter(
        Transaction.property_id == property_id
    ).all()
    return sorted({d[0].year for d in rows})


# ========== Mappings Endpoints ==========

@router.get("/compte-resultat/mappings", response_model=CompteResultatMappingListResponse)
async def get_compte_resultat_mappings(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings pour le compte de résultat d'une propriété.
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat/mappings - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    query = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.property_id == property_id
    )
    total = query.count()

    mappings = query.offset(skip).limit(limit).all()

    # level_1_values reconstruit depuis la liaison (source de vérité — Task 5).
    mapping_responses = [
        CompteResultatMappingResponse(
            id=m.id,
            category_name=m.category_name,
            type=m.type,
            level_1_values=labels_from_mapping_categories(m),
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]

    logger.info(f"[CompteResultat] Retourné {total} mappings pour property_id={property_id}")

    return CompteResultatMappingListResponse(
        items=mapping_responses,
        total=total
    )


@router.post("/compte-resultat/mappings", response_model=CompteResultatMappingResponse, status_code=201)
async def create_compte_resultat_mapping(
    mapping: CompteResultatMappingCreate,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau mapping pour le compte de résultat.
    """
    logger.info(f"[CompteResultat] POST /api/compte-resultat/mappings - property_id={mapping.property_id}")

    validate_property_id(db, mapping.property_id, "CompteResultat")

    # Vérifier si un mapping avec le même category_name existe déjà pour cette propriété
    existing = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.category_name == mapping.category_name,
        CompteResultatMapping.property_id == mapping.property_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà pour cette propriété"
        )

    new_mapping = CompteResultatMapping(
        property_id=mapping.property_id,
        category_name=mapping.category_name,
        type=mapping.type,
    )
    db.add(new_mapping)
    db.flush()  # obtenir new_mapping.id avant de poser la liaison

    # Liaison category_id : unique source de lecture du calcul CR (Task 5 ;
    # colonne level_1_values retirée du modèle en Task 8). Résolue depuis les
    # labels envoyés par le frontend (inchangé cette étape).
    sync_mapping_categories(db, new_mapping, mapping.level_1_values)

    db.commit()
    db.refresh(new_mapping)

    logger.info(f"[CompteResultat] Mapping créé: id={new_mapping.id}, property_id={mapping.property_id}")

    return CompteResultatMappingResponse(
        id=new_mapping.id,
        category_name=new_mapping.category_name,
        type=new_mapping.type,
        level_1_values=labels_from_mapping_categories(new_mapping),
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )


@router.put("/compte-resultat/mappings/{mapping_id}", response_model=CompteResultatMappingResponse)
async def update_compte_resultat_mapping(
    mapping_id: int,
    mapping: CompteResultatMappingUpdate,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour un mapping pour le compte de résultat.
    """
    logger.info(f"[CompteResultat] PUT /api/compte-resultat/mappings/{mapping_id} - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    existing_mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id,
        CompteResultatMapping.property_id == property_id
    ).first()

    if not existing_mapping:
        logger.error(f"[CompteResultat] Mapping {mapping_id} non trouvé pour property_id={property_id}")
        raise HTTPException(status_code=404, detail="Mapping non trouvé pour cette propriété")

    # Vérifier si le nouveau category_name n'est pas déjà utilisé par un autre mapping de la même propriété
    if mapping.category_name and mapping.category_name != existing_mapping.category_name:
        duplicate = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == mapping.category_name,
            CompteResultatMapping.property_id == property_id,
            CompteResultatMapping.id != mapping_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà pour cette propriété"
            )

    # Mettre à jour les champs
    if mapping.category_name is not None:
        existing_mapping.category_name = mapping.category_name
    if mapping.type is not None:
        existing_mapping.type = mapping.type
    if mapping.level_1_values is not None:
        # Reconstruire la liaison category_id (unique source de lecture du calcul
        # CR — Task 5 ; colonne level_1_values retirée du modèle en Task 8).
        sync_mapping_categories(db, existing_mapping, mapping.level_1_values)

    db.commit()
    db.refresh(existing_mapping)

    logger.info(f"[CompteResultat] Mapping {mapping_id} mis à jour pour property_id={property_id}")

    return CompteResultatMappingResponse(
        id=existing_mapping.id,
        category_name=existing_mapping.category_name,
        type=existing_mapping.type,
        level_1_values=labels_from_mapping_categories(existing_mapping),
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )


@router.delete("/compte-resultat/mappings/{mapping_id}", status_code=204)
async def delete_compte_resultat_mapping(
    mapping_id: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping pour le compte de résultat.
    """
    logger.info(f"[CompteResultat] DELETE /api/compte-resultat/mappings/{mapping_id} - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id,
        CompteResultatMapping.property_id == property_id
    ).first()

    if not mapping:
        logger.error(f"[CompteResultat] Mapping {mapping_id} non trouvé pour property_id={property_id}")
        raise HTTPException(status_code=404, detail="Mapping non trouvé pour cette propriété")

    db.delete(mapping)
    db.commit()

    logger.info(f"[CompteResultat] Mapping {mapping_id} supprimé pour property_id={property_id}")

    return None


# ========== Calculate Endpoints ==========

@router.get("/compte-resultat/calculate")
async def calculate_compte_resultat_endpoint(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    years: str = Query(..., description="Années à calculer (séparées par des virgules, ex: '2021,2022,2023')"),
    db: Session = Depends(get_db)
):
    """
    Calculer les montants pour plusieurs années (basé sur les mappings configurés).

    Returns:
        Dictionnaire avec les montants par catégorie et année
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat/calculate - property_id={property_id}, years={years}")

    validate_property_id(db, property_id, "CompteResultat")

    try:
        year_list = [int(y.strip()) for y in years.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Format d'années invalide. Utilisez des nombres séparés par des virgules.")

    results = {}
    mappings = get_mappings(db, property_id)
    level_3_values = get_level_3_values(db, property_id)

    for year in year_list:
        result = calculate_compte_resultat(db, year, property_id, mappings, level_3_values)
        results[year] = result

    logger.info(f"[CompteResultat] Calcul terminé pour {len(year_list)} années, property_id={property_id}")

    return {
        "years": year_list,
        "results": results
    }


# ========== Data Endpoint (calcul temps réel) ==========

@router.get("/compte-resultat", response_model=CompteResultatDataListResponse)
async def get_compte_resultat(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début (pour plusieurs années)"),
    end_year: Optional[int] = Query(None, description="Année de fin (pour plusieurs années)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer le compte de résultat d'une propriété, CALCULÉ EN TEMPS RÉEL
    (produits + charges par catégorie et par année). Plus aucun cache : le
    résultat reflète immédiatement toute modification des données sources.

    Les filtres year / start_year / end_year sélectionnent les années à
    renvoyer parmi celles où la propriété possède des transactions.
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    # Déterminer les années à calculer
    if year is not None:
        selected_years = [year]
    else:
        candidate_years = _data_years_for_property(db, property_id)
        selected_years = [
            y for y in candidate_years
            if (start_year is None or y >= start_year)
            and (end_year is None or y <= end_year)
        ]

    mappings = get_mappings(db, property_id)
    level_3_values = get_level_3_values(db, property_id)

    # Construire les lignes (une par catégorie non nulle, comme l'ancien cache)
    rows = []
    for y in selected_years:
        result = calculate_compte_resultat(db, y, property_id, mappings, level_3_values)
        for category_name, amount in result["produits"].items():
            rows.append((y, category_name, amount))
        for category_name, amount in result["charges"].items():
            rows.append((y, category_name, amount))

    # Tri déterministe par (année, catégorie)
    rows.sort(key=lambda r: (r[0], r[1]))

    total = len(rows)
    paginated = rows[skip:skip + limit]

    data_responses = [
        CompteResultatDataResponse(annee=annee, category_name=category_name, amount=amount)
        for annee, category_name, amount in paginated
    ]

    logger.info(f"[CompteResultat] Calculé {total} lignes en temps réel pour property_id={property_id}")

    return CompteResultatDataListResponse(
        items=data_responses,
        total=total
    )


# ========== Config Endpoints ==========

@router.get("/compte-resultat/config", response_model=CompteResultatConfigResponse)
async def get_compte_resultat_config(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la configuration du compte de résultat (level_3_values) pour une propriété.
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat/config - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    config = db.query(CompteResultatConfig).filter(
        CompteResultatConfig.property_id == property_id
    ).first()

    if not config:
        # Créer une config par défaut si elle n'existe pas pour cette propriété
        config = CompteResultatConfig(
            property_id=property_id,
            level_3_values="[]"
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        logger.info(f"[CompteResultat] Config créée par défaut pour property_id={property_id}")

    return CompteResultatConfigResponse(
        id=config.id,
        level_3_values=config.level_3_values,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/compte-resultat/config", response_model=CompteResultatConfigResponse)
async def update_compte_resultat_config(
    config_update: CompteResultatConfigUpdate,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour la configuration du compte de résultat (level_3_values) pour une propriété.
    """
    logger.info(f"[CompteResultat] PUT /api/compte-resultat/config - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    config = db.query(CompteResultatConfig).filter(
        CompteResultatConfig.property_id == property_id
    ).first()

    if not config:
        # Créer une config si elle n'existe pas pour cette propriété
        config = CompteResultatConfig(
            property_id=property_id,
            level_3_values=config_update.level_3_values or "[]"
        )
        db.add(config)
    else:
        # Mettre à jour la config existante
        if config_update.level_3_values is not None:
            config.level_3_values = config_update.level_3_values

    db.commit()
    db.refresh(config)

    logger.info(f"[CompteResultat] Config mise à jour pour property_id={property_id}")

    return CompteResultatConfigResponse(
        id=config.id,
        level_3_values=config.level_3_values,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


# ========== Override Endpoints ==========

@router.get("/compte-resultat/override", response_model=List[CompteResultatOverrideResponse])
async def get_all_overrides(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer tous les overrides du résultat de l'exercice pour une propriété.
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat/override - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    overrides = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.property_id == property_id
    ).order_by(CompteResultatOverride.year).all()

    logger.info(f"[CompteResultat] Retourné {len(overrides)} overrides pour property_id={property_id}")

    return [
        CompteResultatOverrideResponse(
            id=o.id,
            year=o.year,
            override_value=o.override_value,
            created_at=o.created_at,
            updated_at=o.updated_at
        )
        for o in overrides
    ]


@router.get("/compte-resultat/override/{year}", response_model=CompteResultatOverrideResponse)
async def get_override_by_year(
    year: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'override pour une année spécifique et une propriété.
    """
    logger.info(f"[CompteResultat] GET /api/compte-resultat/override/{year} - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    override = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year == year,
        CompteResultatOverride.property_id == property_id
    ).first()

    if not override:
        logger.error(f"[CompteResultat] Override non trouvé pour year={year}, property_id={property_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Aucun override trouvé pour l'année {year} et cette propriété"
        )

    return CompteResultatOverrideResponse(
        id=override.id,
        year=override.year,
        override_value=override.override_value,
        created_at=override.created_at,
        updated_at=override.updated_at
    )


@router.post("/compte-resultat/override", response_model=CompteResultatOverrideResponse, status_code=201)
async def create_or_update_override(
    override: CompteResultatOverrideCreate,
    db: Session = Depends(get_db)
):
    """
    Créer ou mettre à jour un override pour une année et une propriété (upsert).
    """
    logger.info(f"[CompteResultat] POST /api/compte-resultat/override - property_id={override.property_id}, year={override.year}")

    validate_property_id(db, override.property_id, "CompteResultat")

    # Vérifier si un override existe déjà pour cette année et cette propriété
    existing = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year == override.year,
        CompteResultatOverride.property_id == override.property_id
    ).first()

    if existing:
        # Mettre à jour l'override existant
        existing.override_value = override.override_value
        db.commit()
        db.refresh(existing)

        logger.info(f"[CompteResultat] Override mis à jour pour year={existing.year}, property_id={override.property_id}")

        return CompteResultatOverrideResponse(
            id=existing.id,
            year=existing.year,
            override_value=existing.override_value,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )
    else:
        # Créer un nouvel override
        new_override = CompteResultatOverride(
            property_id=override.property_id,
            year=override.year,
            override_value=override.override_value
        )
        db.add(new_override)
        db.commit()
        db.refresh(new_override)

        logger.info(f"[CompteResultat] Override créé pour year={new_override.year}, property_id={override.property_id}")

        return CompteResultatOverrideResponse(
            id=new_override.id,
            year=new_override.year,
            override_value=new_override.override_value,
            created_at=new_override.created_at,
            updated_at=new_override.updated_at
        )


@router.delete("/compte-resultat/override/{year}", status_code=204)
async def delete_override(
    year: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Supprimer l'override pour une année et une propriété.
    """
    logger.info(f"[CompteResultat] DELETE /api/compte-resultat/override/{year} - property_id={property_id}")

    validate_property_id(db, property_id, "CompteResultat")

    override = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year == year,
        CompteResultatOverride.property_id == property_id
    ).first()

    if not override:
        logger.error(f"[CompteResultat] Override non trouvé pour year={year}, property_id={property_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Aucun override trouvé pour l'année {year} et cette propriété"
        )

    db.delete(override)
    db.commit()

    logger.info(f"[CompteResultat] Override supprimé pour year={year}, property_id={property_id}")

    return None
