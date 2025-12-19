"""
API routes for mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.database.models import Mapping
from backend.api.models import (
    MappingCreate,
    MappingUpdate,
    MappingResponse,
    MappingListResponse
)

router = APIRouter()


@router.get("/mappings", response_model=MappingListResponse)
async def get_mappings(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    search: Optional[str] = Query(None, description="Recherche dans le nom"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings.
    
    Args:
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre d'éléments à retourner
        search: Terme de recherche dans le nom
        db: Session de base de données
    
    Returns:
        Liste des mappings avec pagination
    """
    query = db.query(Mapping)
    
    # Filtre de recherche
    if search:
        query = query.filter(Mapping.nom.contains(search))
    
    # Comptage total
    total = query.count()
    
    # Pagination
    mappings = query.order_by(Mapping.nom).offset(skip).limit(limit).all()
    
    return MappingListResponse(
        mappings=[MappingResponse.model_validate(m) for m in mappings],
        total=total
    )


@router.get("/mappings/{mapping_id}", response_model=MappingResponse)
async def get_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer un mapping par son ID.
    
    Args:
        mapping_id: ID du mapping
        db: Session de base de données
    
    Returns:
        Détails du mapping
    
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    return MappingResponse.model_validate(mapping)


@router.post("/mappings", response_model=MappingResponse, status_code=201)
async def create_mapping(
    mapping: MappingCreate,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau mapping.
    
    Args:
        mapping: Données du mapping à créer
        db: Session de base de données
    
    Returns:
        Mapping créé
    
    Raises:
        HTTPException: Si un mapping avec le même nom existe déjà
    """
    # Vérifier si un mapping avec le même nom existe déjà
    existing = db.query(Mapping).filter(Mapping.nom == mapping.nom).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec le nom '{mapping.nom}' existe déjà"
        )
    
    # Créer le nouveau mapping
    db_mapping = Mapping(
        nom=mapping.nom,
        level_1=mapping.level_1,
        level_2=mapping.level_2,
        level_3=mapping.level_3,
        is_prefix_match=mapping.is_prefix_match,
        priority=mapping.priority
    )
    
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    
    return MappingResponse.model_validate(db_mapping)


@router.put("/mappings/{mapping_id}", response_model=MappingResponse)
async def update_mapping(
    mapping_id: int,
    mapping_update: MappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Modifier un mapping existant.
    
    Args:
        mapping_id: ID du mapping à modifier
        mapping_update: Données à mettre à jour
        db: Session de base de données
    
    Returns:
        Mapping mis à jour
    
    Raises:
        HTTPException: Si le mapping n'existe pas ou si le nouveau nom existe déjà
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    # Vérifier si le nouveau nom (si modifié) existe déjà
    if mapping_update.nom and mapping_update.nom != mapping.nom:
        existing = db.query(Mapping).filter(Mapping.nom == mapping_update.nom).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un mapping avec le nom '{mapping_update.nom}' existe déjà"
            )
    
    # Mettre à jour les champs
    update_data = mapping_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    db.commit()
    db.refresh(mapping)
    
    return MappingResponse.model_validate(mapping)


@router.delete("/mappings/{mapping_id}", status_code=204)
async def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping.
    
    Args:
        mapping_id: ID du mapping à supprimer
        db: Session de base de données
    
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    db.delete(mapping)
    db.commit()
    
    return None

