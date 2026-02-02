"""
API routes for pivot table configurations.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import json
import logging

from backend.database import get_db
from backend.database.models import PivotConfig
from backend.api.models import (
    PivotConfigCreate,
    PivotConfigUpdate,
    PivotConfigResponse,
    PivotConfigListResponse,
)
from backend.api.utils.validation import validate_property_id

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pivot-configs", response_model=PivotConfigListResponse)
def get_pivot_configs(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Liste tous les tableaux croisés sauvegardés pour une propriété.
    """
    logger.info(f"[Pivot] GET /api/pivot-configs - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Filter by property_id
    total = db.query(PivotConfig).filter(PivotConfig.property_id == property_id).count()
    configs = db.query(PivotConfig).filter(
        PivotConfig.property_id == property_id
    ).order_by(desc(PivotConfig.updated_at)).offset(skip).limit(limit).all()
    
    items = []
    for config in configs:
        # Parser le JSON config
        try:
            config_dict = json.loads(config.config) if isinstance(config.config, str) else config.config
        except (json.JSONDecodeError, TypeError):
            config_dict = {}
        
        items.append(PivotConfigResponse(
            id=config.id,
            name=config.name,
            config=config_dict,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))
    
    logger.info(f"[Pivot] Retourné {len(items)} configs pour property_id={property_id}")
    return PivotConfigListResponse(items=items, total=total)


@router.get("/pivot-configs/{config_id}", response_model=PivotConfigResponse)
def get_pivot_config(
    config_id: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Récupère un tableau croisé par ID.
    """
    logger.info(f"[Pivot] GET /api/pivot-configs/{config_id} - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Filter by both id and property_id
    config = db.query(PivotConfig).filter(
        PivotConfig.id == config_id,
        PivotConfig.property_id == property_id
    ).first()
    
    if not config:
        logger.error(f"[Pivot] ERREUR: Pivot config {config_id} non trouvé pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    # Parser le JSON config
    try:
        config_dict = json.loads(config.config) if isinstance(config.config, str) else config.config
    except (json.JSONDecodeError, TypeError):
        config_dict = {}
    
    logger.info(f"[Pivot] Pivot config {config_id} trouvé pour property_id={property_id}")
    return PivotConfigResponse(
        id=config.id,
        name=config.name,
        config=config_dict,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.post("/pivot-configs", response_model=PivotConfigResponse, status_code=201)
def create_pivot_config(
    config_data: PivotConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau tableau croisé.
    """
    logger.info(f"[Pivot] POST /api/pivot-configs - property_id={config_data.property_id}")
    
    # Validate property_id
    validate_property_id(db, config_data.property_id, "Pivot")
    
    # Vérifier si un config avec le même nom existe déjà pour cette propriété
    existing = db.query(PivotConfig).filter(
        PivotConfig.name == config_data.name,
        PivotConfig.property_id == config_data.property_id
    ).first()
    if existing:
        logger.error(f"[Pivot] ERREUR: Un tableau croisé avec le nom '{config_data.name}' existe déjà pour property_id={config_data.property_id}")
        raise HTTPException(status_code=400, detail=f"Un tableau croisé avec le nom '{config_data.name}' existe déjà")
    
    # Convertir config dict en JSON string
    config_json = json.dumps(config_data.config)
    
    db_config = PivotConfig(
        property_id=config_data.property_id,
        name=config_data.name,
        config=config_json,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    logger.info(f"[Pivot] PivotConfig créé: id={db_config.id}, property_id={config_data.property_id}")
    return PivotConfigResponse(
        id=db_config.id,
        name=db_config.name,
        config=config_data.config,
        created_at=db_config.created_at,
        updated_at=db_config.updated_at,
    )


@router.put("/pivot-configs/{config_id}", response_model=PivotConfigResponse)
def update_pivot_config(
    config_id: int,
    config_data: PivotConfigUpdate,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Met à jour un tableau croisé.
    """
    logger.info(f"[Pivot] PUT /api/pivot-configs/{config_id} - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Filter by both id and property_id
    db_config = db.query(PivotConfig).filter(
        PivotConfig.id == config_id,
        PivotConfig.property_id == property_id
    ).first()
    
    if not db_config:
        logger.error(f"[Pivot] ERREUR: Pivot config {config_id} non trouvé pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    # Vérifier si le nouveau nom existe déjà pour cette propriété (si le nom change)
    if config_data.name and config_data.name != db_config.name:
        existing = db.query(PivotConfig).filter(
            PivotConfig.name == config_data.name,
            PivotConfig.property_id == property_id,
            PivotConfig.id != config_id
        ).first()
        if existing:
            logger.error(f"[Pivot] ERREUR: Un tableau croisé avec le nom '{config_data.name}' existe déjà pour property_id={property_id}")
            raise HTTPException(status_code=400, detail=f"Un tableau croisé avec le nom '{config_data.name}' existe déjà")
        db_config.name = config_data.name
    
    # Mettre à jour la config si fournie
    if config_data.config is not None:
        config_json = json.dumps(config_data.config)
        db_config.config = config_json
    
    db.commit()
    db.refresh(db_config)
    
    # Parser le JSON config pour la réponse
    try:
        config_dict = json.loads(db_config.config) if isinstance(db_config.config, str) else db_config.config
    except (json.JSONDecodeError, TypeError):
        config_dict = {}
    
    logger.info(f"[Pivot] PivotConfig {config_id} mis à jour pour property_id={property_id}")
    return PivotConfigResponse(
        id=db_config.id,
        name=db_config.name,
        config=config_dict,
        created_at=db_config.created_at,
        updated_at=db_config.updated_at,
    )


@router.delete("/pivot-configs/{config_id}", status_code=204)
def delete_pivot_config(
    config_id: int,
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Supprime un tableau croisé.
    """
    logger.info(f"[Pivot] DELETE /api/pivot-configs/{config_id} - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Filter by both id and property_id
    db_config = db.query(PivotConfig).filter(
        PivotConfig.id == config_id,
        PivotConfig.property_id == property_id
    ).first()
    
    if not db_config:
        logger.error(f"[Pivot] ERREUR: Pivot config {config_id} non trouvé pour property_id={property_id}")
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    db.delete(db_config)
    db.commit()
    
    logger.info(f"[Pivot] PivotConfig {config_id} supprimé pour property_id={property_id}")
    return None
