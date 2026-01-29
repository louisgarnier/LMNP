"""
API routes for properties.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.database.models import Property
from backend.api.models import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyListResponse
)

router = APIRouter()


@router.get("/properties", response_model=PropertyListResponse)
async def get_properties(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des propriétés.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    query = db.query(Property)
    total = query.count()
    
    properties = query.order_by(Property.name).offset(skip).limit(limit).all()
    
    property_responses = [
        PropertyResponse(
            id=p.id,
            name=p.name,
            address=p.address,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in properties
    ]
    
    return PropertyListResponse(
        items=property_responses,
        total=total
    )


@router.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer une propriété par son ID.
    
    - **property_id**: ID de la propriété
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    
    return PropertyResponse(
        id=property.id,
        name=property.name,
        address=property.address,
        created_at=property.created_at,
        updated_at=property.updated_at
    )


@router.post("/properties", response_model=PropertyResponse, status_code=201)
async def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle propriété.
    
    - **name**: Nom de la propriété (obligatoire, unique)
    - **address**: Adresse de la propriété (optionnel)
    
    Les mappings autorisés (hardcodés) sont automatiquement chargés depuis le fichier Excel.
    """
    from backend.api.utils.logger_config import get_logger
    from backend.api.services.mapping_obligatoire_service import load_allowed_mappings_from_excel
    
    logger = get_logger(__name__)
    
    # Vérifier si une propriété avec le même nom existe déjà
    existing = db.query(Property).filter(Property.name == property_data.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une propriété avec le nom '{property_data.name}' existe déjà"
        )
    
    property = Property(
        name=property_data.name,
        address=property_data.address
    )
    
    db.add(property)
    db.commit()
    db.refresh(property)
    
    logger.info(f"[Properties] POST /api/properties - Propriété créée: {property.name} (ID: {property.id})")
    
    # Charger automatiquement les mappings autorisés depuis le fichier Excel
    try:
        logger.info(f"[Properties] POST /api/properties - Chargement des mappings autorisés pour la propriété {property.id}...")
        loaded_count = load_allowed_mappings_from_excel(db, property_id=property.id)
        logger.info(f"[Properties] POST /api/properties - {loaded_count} mappings autorisés chargés pour la propriété {property.id}")
    except FileNotFoundError as e:
        logger.warning(f"[Properties] POST /api/properties - Fichier Excel des mappings autorisés non trouvé: {e}")
        # Ne pas faire échouer la création de la propriété si le fichier n'existe pas
    except Exception as e:
        logger.error(f"[Properties] POST /api/properties - Erreur lors du chargement des mappings autorisés: {e}", exc_info=True)
        # Ne pas faire échouer la création de la propriété si le chargement échoue
    
    return PropertyResponse(
        id=property.id,
        name=property.name,
        address=property.address,
        created_at=property.created_at,
        updated_at=property.updated_at
    )


@router.put("/properties/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db)
):
    """
    Modifier une propriété.
    
    - **property_id**: ID de la propriété
    - **name**: Nouveau nom (optionnel)
    - **address**: Nouvelle adresse (optionnel)
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    
    # Vérifier si le nouveau nom (s'il est fourni) n'est pas déjà utilisé par une autre propriété
    if property_data.name and property_data.name != property.name:
        existing = db.query(Property).filter(
            Property.name == property_data.name,
            Property.id != property_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une propriété avec le nom '{property_data.name}' existe déjà"
            )
        property.name = property_data.name
    
    if property_data.address is not None:
        property.address = property_data.address
    
    db.commit()
    db.refresh(property)
    
    return PropertyResponse(
        id=property.id,
        name=property.name,
        address=property.address,
        created_at=property.created_at,
        updated_at=property.updated_at
    )


@router.delete("/properties/{property_id}", status_code=204)
async def delete_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une propriété.
    
    - **property_id**: ID de la propriété
    
    ⚠️ ATTENTION : La suppression d'une propriété supprimera également TOUTES les données associées
    (transactions, mappings, crédits, amortissements, comptes de résultat, bilans, etc.)
    grâce aux contraintes FOREIGN KEY avec ON DELETE CASCADE.
    
    Aucune donnée orpheline ne sera laissée en base de données.
    """
    from backend.api.utils.logger_config import get_logger
    logger = get_logger(__name__)
    
    logger.info(f"[Properties] DELETE /api/properties/{property_id} - Début de la suppression")
    
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        
        if not property:
            logger.warning(f"[Properties] DELETE /api/properties/{property_id} - Propriété non trouvée")
            raise HTTPException(status_code=404, detail="Propriété non trouvée")
        
        logger.info(f"[Properties] DELETE /api/properties/{property_id} - Propriété trouvée: {property.name}")
        
        # Activer les foreign keys pour SQLite (déjà activé dans connection.py, mais on le fait aussi ici pour être sûr)
        from sqlalchemy import text
        db.execute(text("PRAGMA foreign_keys = ON"))
        
        # IMPORTANT: Supprimer manuellement les AmortizationResult avant de supprimer les transactions
        # car SQLAlchemy essaie de mettre à jour transaction_id à None au lieu de supprimer
        from backend.database.models import Transaction, AmortizationResult
        from sqlalchemy import text
        
        # Récupérer toutes les transactions de cette propriété
        transactions = db.query(Transaction).filter(Transaction.property_id == property_id).all()
        transaction_ids = [t.id for t in transactions]
        
        if transaction_ids:
            logger.info(f"[Properties] DELETE /api/properties/{property_id} - {len(transaction_ids)} transactions trouvées")
            logger.info(f"[Properties] DELETE /api/properties/{property_id} - Suppression des AmortizationResult associés...")
            
            # Utiliser une requête SQL directe pour éviter que SQLAlchemy ne charge les relations
            # et essaie de mettre à jour transaction_id à None
            # SQLAlchemy text() attend un dictionnaire ou une séquence de tuples
            placeholders = ','.join([f':id{i}' for i in range(len(transaction_ids))])
            params = {f'id{i}': tid for i, tid in enumerate(transaction_ids)}
            result = db.execute(
                text(f"DELETE FROM amortization_results WHERE transaction_id IN ({placeholders})"),
                params
            )
            deleted_count = result.rowcount
            logger.info(f"[Properties] DELETE /api/properties/{property_id} - {deleted_count} AmortizationResult supprimés via SQL direct")
            
            # Flush pour s'assurer que les suppressions sont appliquées avant la suppression de la propriété
            db.flush()
        
        # Supprimer la propriété (les contraintes FK avec ON DELETE CASCADE supprimeront automatiquement toutes les données associées)
        # Cela inclut : transactions, mappings, crédits, amortissements, comptes de résultat, bilans, etc.
        logger.info(f"[Properties] DELETE /api/properties/{property_id} - Suppression de la propriété et de toutes ses données associées")
        db.delete(property)
        db.commit()
        
        logger.info(f"[Properties] DELETE /api/properties/{property_id} - Propriété supprimée avec succès")
        return None
    except HTTPException:
        raise
    except Exception as e:
        # Logger dans le logger root (backend) pour qu'il apparaisse dans backend_*.log
        root_logger = logging.getLogger()
        root_logger.error(
            f"❌ ERREUR lors de la suppression de la propriété {property_id}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        
        # Logger aussi dans le logger API
        logger.error(f"[Properties] DELETE /api/properties/{property_id} - Erreur lors de la suppression: {e}", exc_info=True)
        
        # Afficher aussi dans le terminal (via print pour être sûr)
        import traceback
        print(f"\n{'='*80}")
        print(f"❌ ERREUR suppression propriété {property_id}: {type(e).__name__}: {str(e)}")
        print(f"   Traceback:")
        traceback.print_exc()
        print(f"{'='*80}\n")
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de la propriété: {str(e)}")
