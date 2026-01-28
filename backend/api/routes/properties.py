"""
API routes for properties.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

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
    """
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
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    
    # Activer les foreign keys pour SQLite (déjà activé dans connection.py, mais on le fait aussi ici pour être sûr)
    from sqlalchemy import text
    db.execute(text("PRAGMA foreign_keys = ON"))
    
    # Supprimer la propriété (les contraintes FK avec ON DELETE CASCADE supprimeront automatiquement toutes les données associées)
    # Cela inclut : transactions, mappings, crédits, amortissements, comptes de résultat, bilans, etc.
    db.delete(property)
    db.commit()
    
    return None
