"""
Validation utilities for API endpoints.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.database.models import Property
import logging

logger = logging.getLogger(__name__)


def validate_property_id(db: Session, property_id: int, context: str = "API") -> bool:
    """
    Valide qu'un property_id existe dans la table properties.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété à valider
        context: Contexte pour les logs (ex: "Transactions", "Mappings", etc.)
    
    Returns:
        True si valide
    
    Raises:
        HTTPException(400): Si property_id n'existe pas
    """
    logger.info(f"[{context}] Validation property_id={property_id}")
    
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        error_msg = f"Property ID {property_id} n'existe pas"
        logger.error(f"[{context}] ERREUR: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    logger.debug(f"[{context}] Property validée: {property_obj.name} (ID={property_id})")
    return True
