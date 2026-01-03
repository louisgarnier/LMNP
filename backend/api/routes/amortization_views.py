"""
API routes for amortization views management.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.database.models import AmortizationView
from backend.api.models import (
    AmortizationViewResponse,
    AmortizationViewCreate,
    AmortizationViewUpdate,
    AmortizationViewListResponse
)

router = APIRouter()


@router.get("/amortization/views", response_model=AmortizationViewListResponse)
async def get_amortization_views(
    level_2_value: Optional[str] = Query(None, description="Filtrer par Level 2"),
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les vues d'amortissement.
    
    Args:
        level_2_value: Optionnel, filtre par Level 2
        
    Returns:
        Liste de toutes les vues d'amortissement (filtrées si level_2_value fourni)
    """
    query = db.query(AmortizationView)
    
    if level_2_value:
        query = query.filter(AmortizationView.level_2_value == level_2_value)
    
    views = query.order_by(AmortizationView.created_at.desc()).all()
    
    return AmortizationViewListResponse(
        views=[AmortizationViewResponse.model_validate(v) for v in views],
        total=len(views)
    )


@router.get("/amortization/views/{view_id}", response_model=AmortizationViewResponse)
async def get_amortization_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une vue d'amortissement par ID.
    
    Args:
        view_id: ID de la vue
        
    Returns:
        Vue d'amortissement
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(AmortizationView).filter(AmortizationView.id == view_id).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue d'amortissement non trouvée")
    
    return AmortizationViewResponse.model_validate(view)


@router.post("/amortization/views", response_model=AmortizationViewResponse, status_code=201)
async def create_amortization_view(
    view_data: AmortizationViewCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle vue d'amortissement.
    
    Args:
        view_data: Données de la vue à créer
        
    Returns:
        Vue créée
        
    Raises:
        HTTPException: Si une vue avec le même nom existe déjà pour ce Level 2
    """
    # Vérifier si une vue avec le même nom existe déjà pour ce Level 2
    existing = db.query(AmortizationView).filter(
        and_(
            AmortizationView.name == view_data.name,
            AmortizationView.level_2_value == view_data.level_2_value
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une vue avec le nom '{view_data.name}' existe déjà pour le Level 2 '{view_data.level_2_value}'"
        )
    
    view = AmortizationView(
        name=view_data.name,
        level_2_value=view_data.level_2_value,
        view_data=view_data.view_data
    )
    
    db.add(view)
    db.commit()
    db.refresh(view)
    
    # Invalider tous les comptes de résultat (les vues d'amortissement ont changé)
    from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
    invalidate_all_compte_resultat(db)
    
    # Invalider tous les bilans (les vues d'amortissement ont changé)
    from backend.api.services.bilan_service import invalidate_all_bilan
    invalidate_all_bilan(db)
    
    return AmortizationViewResponse.model_validate(view)


@router.put("/amortization/views/{view_id}", response_model=AmortizationViewResponse)
async def update_amortization_view(
    view_id: int,
    view_data: AmortizationViewUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour une vue d'amortissement (renommage ou mise à jour des données).
    
    Args:
        view_id: ID de la vue
        view_data: Données à mettre à jour
        
    Returns:
        Vue mise à jour
        
    Raises:
        HTTPException: Si la vue n'existe pas ou si le nouveau nom existe déjà
    """
    view = db.query(AmortizationView).filter(AmortizationView.id == view_id).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue d'amortissement non trouvée")
    
    # Si le nom change, vérifier qu'il n'existe pas déjà pour ce Level 2
    if view_data.name and view_data.name != view.name:
        existing = db.query(AmortizationView).filter(
            and_(
                AmortizationView.name == view_data.name,
                AmortizationView.level_2_value == view.level_2_value,
                AmortizationView.id != view_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une vue avec le nom '{view_data.name}' existe déjà pour le Level 2 '{view.level_2_value}'"
            )
    
    # Mettre à jour les champs fournis
    update_data = view_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(view, key, value)
    
    view.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(view)
    
    # Invalider tous les comptes de résultat (les vues d'amortissement ont changé)
    from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
    invalidate_all_compte_resultat(db)
    
    return AmortizationViewResponse.model_validate(view)


@router.delete("/amortization/views/{view_id}", status_code=204)
async def delete_amortization_view(
    view_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une vue d'amortissement.
    
    Args:
        view_id: ID de la vue
        
    Raises:
        HTTPException: Si la vue n'existe pas
    """
    view = db.query(AmortizationView).filter(AmortizationView.id == view_id).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Vue d'amortissement non trouvée")
    
    db.delete(view)
    db.commit()
    
    # Invalider tous les comptes de résultat (les vues d'amortissement ont changé)
    from backend.api.services.compte_resultat_service import invalidate_all_compte_resultat
    invalidate_all_compte_resultat(db)
    
    # Invalider tous les bilans (les vues d'amortissement ont changé)
    from backend.api.services.bilan_service import invalidate_all_bilan
    invalidate_all_bilan(db)
    
    return None

