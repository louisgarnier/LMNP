"""
API routes for loan configurations management.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les configurations de crédit.
    
    Returns:
        Liste de toutes les configurations de crédit
    """
    configs = db.query(LoanConfig).order_by(LoanConfig.created_at).all()
    
    return LoanConfigListResponse(
        configs=[LoanConfigResponse.model_validate(c) for c in configs],
        total=len(configs)
    )


@router.get("/loan-configs/{config_id}", response_model=LoanConfigResponse)
async def get_loan_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une configuration de crédit par ID.
    
    Args:
        config_id: ID de la configuration
    
    Returns:
        Configuration de crédit
    
    Raises:
        HTTPException: Si la configuration n'existe pas
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration de crédit avec ID {config_id} non trouvée")
    
    return LoanConfigResponse.model_validate(config)


@router.post("/loan-configs", response_model=LoanConfigResponse, status_code=201)
async def create_loan_config(
    config_data: LoanConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle configuration de crédit.
    
    Args:
        config_data: Données de la configuration de crédit
    
    Returns:
        Configuration de crédit créée
    """
    config = LoanConfig(
        name=config_data.name,
        credit_amount=config_data.credit_amount,
        interest_rate=config_data.interest_rate,
        duration_years=config_data.duration_years,
        initial_deferral_months=config_data.initial_deferral_months
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return LoanConfigResponse.model_validate(config)


@router.put("/loan-configs/{config_id}", response_model=LoanConfigResponse)
async def update_loan_config(
    config_id: int,
    config_data: LoanConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour une configuration de crédit existante.
    
    Args:
        config_id: ID de la configuration
        config_data: Données à mettre à jour
    
    Returns:
        Configuration de crédit mise à jour
    
    Raises:
        HTTPException: Si la configuration n'existe pas
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration de crédit avec ID {config_id} non trouvée")
    
    # Mettre à jour les champs fournis
    if config_data.name is not None:
        config.name = config_data.name
    if config_data.credit_amount is not None:
        config.credit_amount = config_data.credit_amount
    if config_data.interest_rate is not None:
        config.interest_rate = config_data.interest_rate
    if config_data.duration_years is not None:
        config.duration_years = config_data.duration_years
    if config_data.initial_deferral_months is not None:
        config.initial_deferral_months = config_data.initial_deferral_months
    
    db.commit()
    db.refresh(config)
    
    return LoanConfigResponse.model_validate(config)


@router.delete("/loan-configs/{config_id}")
async def delete_loan_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une configuration de crédit.
    
    Args:
        config_id: ID de la configuration
    
    Raises:
        HTTPException: Si la configuration n'existe pas
    """
    config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration de crédit avec ID {config_id} non trouvée")
    
    db.delete(config)
    db.commit()
    
    return {"message": f"Configuration de crédit {config_id} supprimée avec succès"}

