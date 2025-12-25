"""
API routes for amortization calculations.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.database.models import AmortizationConfig
from backend.api.models import (
    AmortizationConfigResponse,
    AmortizationConfigUpdate
)

router = APIRouter()


@router.get("/amortization/config", response_model=AmortizationConfigResponse)
async def get_amortization_config(
    db: Session = Depends(get_db)
):
    """
    Récupère la configuration des amortissements.
    
    Returns:
        Configuration des amortissements (singleton - une seule config)
    
    Raises:
        HTTPException: Si aucune configuration n'existe
    """
    config = db.query(AmortizationConfig).first()
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Aucune configuration d'amortissement trouvée. Veuillez créer une configuration."
        )
    
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
    # Vérifier que le mapping contient les 4 clés requises
    required_keys = ["meubles", "travaux", "construction", "terrain"]
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
        config.duration_meubles = config_data.duration_meubles
        config.duration_travaux = config_data.duration_travaux
        config.duration_construction = config_data.duration_construction
        config.duration_terrain = config_data.duration_terrain
    else:
        # Créer une nouvelle configuration
        config = AmortizationConfig(
            level_2_value=config_data.level_2_value,
            level_3_mapping=config_data.level_3_mapping,
            duration_meubles=config_data.duration_meubles,
            duration_travaux=config_data.duration_travaux,
            duration_construction=config_data.duration_construction,
            duration_terrain=config_data.duration_terrain
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    
    return AmortizationConfigResponse.model_validate(config)

