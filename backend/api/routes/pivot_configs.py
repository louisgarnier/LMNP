"""
API routes for pivot table configurations.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import json

from backend.database import get_db
from backend.database.models import PivotConfig
from backend.api.models import (
    PivotConfigCreate,
    PivotConfigUpdate,
    PivotConfigResponse,
    PivotConfigListResponse,
)

router = APIRouter()


@router.get("/pivot-configs", response_model=PivotConfigListResponse)
def get_pivot_configs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Liste tous les tableaux croisés sauvegardés.
    """
    total = db.query(PivotConfig).count()
    configs = db.query(PivotConfig).order_by(desc(PivotConfig.updated_at)).offset(skip).limit(limit).all()
    
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
    
    return PivotConfigListResponse(items=items, total=total)


@router.get("/pivot-configs/{config_id}", response_model=PivotConfigResponse)
def get_pivot_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un tableau croisé par ID.
    """
    config = db.query(PivotConfig).filter(PivotConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    # Parser le JSON config
    try:
        config_dict = json.loads(config.config) if isinstance(config.config, str) else config.config
    except (json.JSONDecodeError, TypeError):
        config_dict = {}
    
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
    # Vérifier si un config avec le même nom existe déjà
    existing = db.query(PivotConfig).filter(PivotConfig.name == config_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un tableau croisé avec le nom '{config_data.name}' existe déjà")
    
    # Convertir config dict en JSON string
    config_json = json.dumps(config_data.config)
    
    db_config = PivotConfig(
        name=config_data.name,
        config=config_json,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
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
    db: Session = Depends(get_db)
):
    """
    Met à jour un tableau croisé.
    """
    db_config = db.query(PivotConfig).filter(PivotConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    # Vérifier si le nouveau nom existe déjà (si le nom change)
    if config_data.name and config_data.name != db_config.name:
        existing = db.query(PivotConfig).filter(PivotConfig.name == config_data.name).first()
        if existing:
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
    db: Session = Depends(get_db)
):
    """
    Supprime un tableau croisé.
    """
    db_config = db.query(PivotConfig).filter(PivotConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail=f"Pivot config avec ID {config_id} non trouvé")
    
    db.delete(db_config)
    db.commit()
    
    return None

