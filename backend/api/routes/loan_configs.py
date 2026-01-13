"""
API routes for loan configurations.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.database.models import LoanConfig
from backend.api.models import (
    LoanConfigCreate,
    LoanConfigUpdate,
    LoanConfigResponse,
    LoanConfigListResponse
)

router = APIRouter()


@router.get("/loan-configs", response_model=LoanConfigListResponse)
async def get_loan_configs(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    sort_by: Optional[str] = Query("name", description="Colonne de tri (name, credit_amount, interest_rate, duration_years)"),
    sort_direction: Optional[str] = Query("asc", description="Direction du tri (asc, desc)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des configurations de crédit.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    - **sort_by**: Colonne de tri (name, credit_amount, interest_rate, duration_years)
    - **sort_direction**: Direction du tri (asc, desc)
    """
    query = db.query(LoanConfig)
    
    # Compter le total (avant tri)
    total = query.count()
    
    # Tri
    if sort_by:
        sort_dir = sort_direction.lower() if sort_direction else "asc"
        if sort_dir not in ["asc", "desc"]:
            sort_dir = "asc"
        
        if sort_by == "name":
            order_col = LoanConfig.name
        elif sort_by == "credit_amount":
            order_col = LoanConfig.credit_amount
        elif sort_by == "interest_rate":
            order_col = LoanConfig.interest_rate
        elif sort_by == "duration_years":
            order_col = LoanConfig.duration_years
        else:
            order_col = LoanConfig.name
            sort_dir = "asc"
        
        if sort_dir == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(LoanConfig.name))
    
    # Pagination
    configs = query.offset(skip).limit(limit).all()
    
    # Convertir en réponse
    config_responses = [
        LoanConfigResponse(
            id=c.id,
            name=c.name,
            credit_amount=c.credit_amount,
            interest_rate=c.interest_rate,
            duration_years=c.duration_years,
            initial_deferral_months=c.initial_deferral_months,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in configs
    ]
    
    return LoanConfigListResponse(
        items=config_responses,
        total=total
    )


@router.post("/loan-configs", response_model=LoanConfigResponse, status_code=201)
async def create_loan_config(
    config: LoanConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle configuration de crédit.
    """
    # Vérifier si une configuration avec le même nom existe déjà
    existing = db.query(LoanConfig).filter(LoanConfig.name == config.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une configuration avec le nom '{config.name}' existe déjà"
        )
    
    db_config = LoanConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return LoanConfigResponse(
        id=db_config.id,
        name=db_config.name,
        credit_amount=db_config.credit_amount,
        interest_rate=db_config.interest_rate,
        duration_years=db_config.duration_years,
        initial_deferral_months=db_config.initial_deferral_months,
        created_at=db_config.created_at,
        updated_at=db_config.updated_at
    )


@router.get("/loan-configs/{config_id}", response_model=LoanConfigResponse)
async def get_loan_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer une configuration de crédit par son ID.
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration de crédit non trouvée")
    
    return LoanConfigResponse(
        id=config.id,
        name=config.name,
        credit_amount=config.credit_amount,
        interest_rate=config.interest_rate,
        duration_years=config.duration_years,
        initial_deferral_months=config.initial_deferral_months,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/loan-configs/{config_id}", response_model=LoanConfigResponse)
async def update_loan_config(
    config_id: int,
    config_update: LoanConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une configuration de crédit.
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration de crédit non trouvée")
    
    # Vérifier si le nouveau nom (si fourni) n'est pas déjà utilisé par une autre configuration
    update_data = config_update.dict(exclude_unset=True)
    if 'name' in update_data and update_data['name'] != config.name:
        existing = db.query(LoanConfig).filter(
            LoanConfig.name == update_data['name'],
            LoanConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une configuration avec le nom '{update_data['name']}' existe déjà"
            )
    
    # Mettre à jour les champs fournis
    for field, value in update_data.items():
        setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    
    return LoanConfigResponse(
        id=config.id,
        name=config.name,
        credit_amount=config.credit_amount,
        interest_rate=config.interest_rate,
        duration_years=config.duration_years,
        initial_deferral_months=config.initial_deferral_months,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete("/loan-configs/{config_id}", status_code=204)
async def delete_loan_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une configuration de crédit.
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration de crédit non trouvée")
    
    db.delete(config)
    db.commit()
    
    return None
