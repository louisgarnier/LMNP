"""
API routes for amortization types management.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List
from datetime import date

from backend.database import get_db
from backend.database.models import (
    AmortizationType, Transaction, EnrichedTransaction, AmortizationResult
)
from backend.api.models import (
    AmortizationTypeResponse,
    AmortizationTypeCreate,
    AmortizationTypeUpdate,
    AmortizationTypeListResponse,
    AmortizationTypeAmountResponse,
    AmortizationTypeCumulatedResponse
)

router = APIRouter()


@router.get("/amortization/types", response_model=AmortizationTypeListResponse)
async def get_amortization_types(
    db: Session = Depends(get_db)
):
    """
    Récupère tous les types d'amortissement.
    
    Returns:
        Liste de tous les types d'amortissement
    """
    types = db.query(AmortizationType).order_by(AmortizationType.created_at).all()
    
    return AmortizationTypeListResponse(
        types=[AmortizationTypeResponse.model_validate(t) for t in types],
        total=len(types)
    )


@router.get("/amortization/types/{type_id}", response_model=AmortizationTypeResponse)
async def get_amortization_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un type d'amortissement par ID.
    
    Args:
        type_id: ID du type d'amortissement
        
    Returns:
        Type d'amortissement
        
    Raises:
        HTTPException: Si le type n'existe pas
    """
    amortization_type = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not amortization_type:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    return AmortizationTypeResponse.model_validate(amortization_type)


@router.post("/amortization/types", response_model=AmortizationTypeResponse, status_code=201)
async def create_amortization_type(
    type_data: AmortizationTypeCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau type d'amortissement.
    
    Args:
        type_data: Données du type d'amortissement
        
    Returns:
        Type d'amortissement créé
    """
    amortization_type = AmortizationType(
        name=type_data.name,
        level_2_value=type_data.level_2_value,
        level_1_values=type_data.level_1_values,
        start_date=type_data.start_date,
        duration=type_data.duration,
        annual_amount=type_data.annual_amount
    )
    
    db.add(amortization_type)
    db.commit()
    db.refresh(amortization_type)
    
    return AmortizationTypeResponse.model_validate(amortization_type)


@router.put("/amortization/types/{type_id}", response_model=AmortizationTypeResponse)
async def update_amortization_type(
    type_id: int,
    type_data: AmortizationTypeUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un type d'amortissement.
    
    Args:
        type_id: ID du type d'amortissement
        type_data: Données à mettre à jour
        
    Returns:
        Type d'amortissement mis à jour
        
    Raises:
        HTTPException: Si le type n'existe pas
    """
    amortization_type = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not amortization_type:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Mettre à jour uniquement les champs fournis
    # Utiliser model_dump(exclude_unset=True) pour distinguer entre "champ non fourni" et "champ = None"
    update_data = type_data.model_dump(exclude_unset=True)
    
    if 'name' in update_data:
        amortization_type.name = update_data['name']
    if 'level_2_value' in update_data:
        amortization_type.level_2_value = update_data['level_2_value']
    if 'level_1_values' in update_data:
        amortization_type.level_1_values = update_data['level_1_values']
    if 'start_date' in update_data:
        # Permettre explicitement de définir start_date à None pour supprimer la date
        # None signifie "utiliser les dates des transactions" (pas d'override)
        amortization_type.start_date = update_data['start_date']
    if 'duration' in update_data:
        amortization_type.duration = update_data['duration']
    if 'annual_amount' in update_data:
        amortization_type.annual_amount = update_data['annual_amount']
    
    db.commit()
    db.refresh(amortization_type)
    
    return AmortizationTypeResponse.model_validate(amortization_type)


@router.delete("/amortization/types/{type_id}", status_code=204)
async def delete_amortization_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un type d'amortissement.
    
    Args:
        type_id: ID du type d'amortissement
        
    Raises:
        HTTPException: Si le type n'existe pas ou s'il est utilisé dans des amortissements
    """
    amortization_type = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not amortization_type:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Vérifier si le type est réellement utilisé dans des amortissements
    # Si le type n'a pas de level_1_values configurés, il ne peut pas être utilisé → permettre la suppression
    if not amortization_type.level_1_values or len(amortization_type.level_1_values) == 0:
        # Type non configuré (pas de level_1_values) → peut être supprimé même s'il y a des résultats avec ce nom
        # (car ces résultats ne correspondent pas à ce type spécifique)
        pass
    else:
        # Type configuré → vérifier s'il est réellement utilisé
        # On vérifie si des transactions correspondent aux critères du type ET ont généré des résultats
        from backend.database.models import Transaction, EnrichedTransaction
        
        # Compter les résultats d'amortissement qui correspondent réellement à ce type
        # (via les transactions qui matchent level_2_value et level_1_values)
        results_count = db.query(AmortizationResult).join(
            Transaction, AmortizationResult.transaction_id == Transaction.id
        ).join(
            EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                AmortizationResult.category == amortization_type.name,
                EnrichedTransaction.level_2 == amortization_type.level_2_value,
                EnrichedTransaction.level_1.in_(amortization_type.level_1_values)
            )
        ).count()
        
        if results_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de supprimer ce type : il est utilisé dans {results_count} résultat(s) d'amortissement"
            )
    
    db.delete(amortization_type)
    db.commit()
    
    return None


@router.get("/amortization/types/{type_id}/amount", response_model=AmortizationTypeAmountResponse)
async def get_amortization_type_amount(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcule le montant d'immobilisation pour un type d'amortissement.
    
    Montant = Somme de toutes les transactions où :
    - transaction.enriched_transaction.level_2 = level_2_value
    - transaction.enriched_transaction.level_1 IN level_1_values
    
    Args:
        type_id: ID du type d'amortissement
        
    Returns:
        Montant d'immobilisation calculé
        
    Raises:
        HTTPException: Si le type n'existe pas
    """
    amortization_type = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not amortization_type:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Si aucune valeur level_1 mappée, montant = 0
    if not amortization_type.level_1_values or len(amortization_type.level_1_values) == 0:
        return AmortizationTypeAmountResponse(
            type_id=amortization_type.id,
            type_name=amortization_type.name,
            amount=0.0
        )
    
    # Calculer le montant : somme des transactions correspondantes
    # Jointure Transaction -> EnrichedTransaction
    # Filtre : level_2 = level_2_value ET level_1 IN level_1_values
    query = db.query(func.sum(Transaction.quantite)).join(
        EnrichedTransaction,
        Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_2 == amortization_type.level_2_value,
            EnrichedTransaction.level_1.in_(amortization_type.level_1_values)
        )
    )
    
    # Si start_date est renseignée, filtrer par année
    if amortization_type.start_date:
        start_year = amortization_type.start_date.year
        query = query.filter(func.extract('year', Transaction.date) == start_year)
    
    result = query.scalar()
    amount = float(result) if result is not None else 0.0
    
    return AmortizationTypeAmountResponse(
        type_id=amortization_type.id,
        type_name=amortization_type.name,
        amount=amount
    )


@router.get("/amortization/types/{type_id}/cumulated", response_model=AmortizationTypeCumulatedResponse)
async def get_amortization_type_cumulated(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcule le montant cumulé des amortissements pour un type d'amortissement.
    
    Montant cumulé = Somme de tous les AmortizationResult pour les transactions où :
    - transaction.enriched_transaction.level_2 = level_2_value
    - transaction.enriched_transaction.level_1 IN level_1_values
    - AmortizationResult.year <= année_courante
    
    Args:
        type_id: ID du type d'amortissement
        
    Returns:
        Montant cumulé calculé
        
    Raises:
        HTTPException: Si le type n'existe pas
    """
    from datetime import datetime
    from backend.database.models import Transaction, EnrichedTransaction
    
    amortization_type = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not amortization_type:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    current_year = datetime.now().year
    
    # Si aucune valeur level_1 mappée, montant cumulé = 0
    if not amortization_type.level_1_values or len(amortization_type.level_1_values) == 0:
        return AmortizationTypeCumulatedResponse(
            type_id=amortization_type.id,
            type_name=amortization_type.name,
            cumulated_amount=0.0
        )
    
    # Trouver toutes les transactions correspondantes au type
    # Jointure Transaction -> EnrichedTransaction
    # Filtre : level_2 = level_2_value ET level_1 IN level_1_values
    matching_transactions = db.query(Transaction.id).join(
        EnrichedTransaction,
        Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_2 == amortization_type.level_2_value,
            EnrichedTransaction.level_1.in_(amortization_type.level_1_values)
        )
    ).all()
    
    transaction_ids = [t[0] for t in matching_transactions]
    
    if not transaction_ids:
        return AmortizationTypeCumulatedResponse(
            type_id=amortization_type.id,
            type_name=amortization_type.name,
            cumulated_amount=0.0
        )
    
    # Calculer le montant cumulé : somme de tous les AmortizationResult pour ces transactions
    # jusqu'à l'année courante
    result = db.query(func.sum(AmortizationResult.amount)).filter(
        and_(
            AmortizationResult.transaction_id.in_(transaction_ids),
            AmortizationResult.year <= current_year
        )
    ).scalar()
    
    cumulated_amount = float(result) if result is not None else 0.0
    
    return AmortizationTypeCumulatedResponse(
        type_id=amortization_type.id,
        type_name=amortization_type.name,
        cumulated_amount=cumulated_amount
    )

