"""
API routes for amortization types management.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import date, datetime

from backend.database import get_db
from backend.database.models import (
    AmortizationType,
    AmortizationResult,
    Transaction,
    EnrichedTransaction
)
from backend.api.models import (
    AmortizationTypeCreate,
    AmortizationTypeUpdate,
    AmortizationTypeResponse,
    AmortizationTypeListResponse,
    AmortizationTypeAmountResponse,
    AmortizationTypeCumulatedResponse,
    AmortizationTypeTransactionCountResponse
)
from backend.api.services.amortization_service import calculate_yearly_amounts

router = APIRouter()


@router.get("/amortization/types", response_model=AmortizationTypeListResponse)
async def get_amortization_types(
    level_2_value: Optional[str] = Query(None, description="Filtrer par level_2_value"),
    db: Session = Depends(get_db)
):
    """
    Liste tous les types d'amortissement.
    
    Args:
        level_2_value: Filtrer par valeur level_2 (optionnel)
        db: Session de base de données
    
    Returns:
        Liste de tous les types d'amortissement
    """
    query = db.query(AmortizationType)
    
    if level_2_value:
        query = query.filter(AmortizationType.level_2_value == level_2_value)
    
    types = query.order_by(AmortizationType.name).all()
    
    # Convertir level_1_values de JSON en liste
    items = []
    for atype in types:
        type_dict = {
            "id": atype.id,
            "name": atype.name,
            "level_2_value": atype.level_2_value,
            "level_1_values": json.loads(atype.level_1_values or "[]"),
            "start_date": atype.start_date,
            "duration": atype.duration,
            "annual_amount": atype.annual_amount,
            "created_at": atype.created_at,
            "updated_at": atype.updated_at
        }
        items.append(AmortizationTypeResponse(**type_dict))
    
    return AmortizationTypeListResponse(
        items=items,
        total=len(items)
    )


@router.post("/amortization/types", response_model=AmortizationTypeResponse, status_code=201)
async def create_amortization_type(
    type_data: AmortizationTypeCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau type d'amortissement.
    
    Args:
        type_data: Données du type à créer
        db: Session de base de données
    
    Returns:
        Type d'amortissement créé
    """
    # Créer le type
    new_type = AmortizationType(
        name=type_data.name,
        level_2_value=type_data.level_2_value,
        level_1_values=json.dumps(type_data.level_1_values or []),
        start_date=type_data.start_date,
        duration=type_data.duration,
        annual_amount=type_data.annual_amount
    )
    
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    
    # Retourner la réponse
    return AmortizationTypeResponse(
        id=new_type.id,
        name=new_type.name,
        level_2_value=new_type.level_2_value,
        level_1_values=json.loads(new_type.level_1_values or "[]"),
        start_date=new_type.start_date,
        duration=new_type.duration,
        annual_amount=new_type.annual_amount,
        created_at=new_type.created_at,
        updated_at=new_type.updated_at
    )


@router.get("/amortization/types/{type_id}", response_model=AmortizationTypeResponse)
async def get_amortization_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un type d'amortissement par son ID.
    
    Args:
        type_id: ID du type
        db: Session de base de données
    
    Returns:
        Type d'amortissement
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    return AmortizationTypeResponse(
        id=atype.id,
        name=atype.name,
        level_2_value=atype.level_2_value,
        level_1_values=json.loads(atype.level_1_values or "[]"),
        start_date=atype.start_date,
        duration=atype.duration,
        annual_amount=atype.annual_amount,
        created_at=atype.created_at,
        updated_at=atype.updated_at
    )


@router.put("/amortization/types/{type_id}", response_model=AmortizationTypeResponse)
async def update_amortization_type(
    type_id: int,
    type_data: AmortizationTypeUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un type d'amortissement.
    
    Args:
        type_id: ID du type
        type_data: Données à mettre à jour
        db: Session de base de données
    
    Returns:
        Type d'amortissement mis à jour
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Mettre à jour les champs fournis
    # Utiliser model_dump(exclude_unset=True) pour ne mettre à jour que les champs fournis
    update_data = type_data.model_dump(exclude_unset=True)
    
    # Pour start_date et annual_amount, on doit vérifier s'ils sont explicitement fournis
    # en utilisant hasattr pour vérifier si le champ a été défini dans le modèle
    if "name" in update_data:
        atype.name = update_data["name"]
    if "level_2_value" in update_data:
        atype.level_2_value = update_data["level_2_value"]
    if "level_1_values" in update_data:
        atype.level_1_values = json.dumps(update_data["level_1_values"] or [])
    if "start_date" in update_data:
        # start_date peut être None (pour supprimer la date)
        atype.start_date = update_data["start_date"]
    if "duration" in update_data:
        atype.duration = update_data["duration"]
    if "annual_amount" in update_data:
        # annual_amount peut être None (pour utiliser le calcul automatique)
        atype.annual_amount = update_data["annual_amount"]
    
    db.commit()
    db.refresh(atype)
    
    return AmortizationTypeResponse(
        id=atype.id,
        name=atype.name,
        level_2_value=atype.level_2_value,
        level_1_values=json.loads(atype.level_1_values or "[]"),
        start_date=atype.start_date,
        duration=atype.duration,
        annual_amount=atype.annual_amount,
        created_at=atype.created_at,
        updated_at=atype.updated_at
    )


@router.delete("/amortization/types/all", status_code=200)
async def delete_all_amortization_types(
    db: Session = Depends(get_db)
):
    """
    Supprime TOUS les types d'amortissement de TOUS les Level 2 (toute la table).
    
    ⚠️ ATTENTION : Cette action est irréversible et supprime définitivement tous les types d'amortissement.
    Supprime également tous les AmortizationResult associés pour éviter les erreurs de contrainte.
    
    Returns:
        Nombre de types supprimés
    """
    # Compter les types avant suppression
    count_before = db.query(AmortizationType).count()
    
    # Supprimer tous les résultats d'amortissement associés
    db.query(AmortizationResult).delete()
    
    # Supprimer tous les types
    db.query(AmortizationType).delete()
    db.commit()
    
    return {"deleted_count": count_before}


@router.delete("/amortization/types/{type_id}", status_code=204)
async def delete_amortization_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un type d'amortissement.
    
    Supprime automatiquement tous les AmortizationResult associés avant de supprimer le type.
    
    Args:
        type_id: ID du type
        db: Session de base de données
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Supprimer tous les résultats d'amortissement associés
    # Filtrer par category == type.name, level_2 == type.level_2_value, et level_1 IN type.level_1_values
    level_1_values = json.loads(atype.level_1_values or "[]")
    
    if level_1_values:
        # Récupérer les transactions correspondantes
        matching_transactions = db.query(Transaction.id).join(
            EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                EnrichedTransaction.level_2 == atype.level_2_value,
                EnrichedTransaction.level_1.in_(level_1_values)
            )
        ).all()
        
        transaction_ids = [t[0] for t in matching_transactions]
        
        if transaction_ids:
            db.query(AmortizationResult).filter(
                and_(
                    AmortizationResult.category == atype.name,
                    AmortizationResult.transaction_id.in_(transaction_ids)
                )
            ).delete()
    
    # Supprimer le type
    db.delete(atype)
    db.commit()
    
    return None


@router.get("/amortization/types/{type_id}/amount", response_model=AmortizationTypeAmountResponse)
async def get_amortization_type_amount(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcule le montant total d'immobilisation pour un type donné.
    
    Le montant est la somme des transactions qui correspondent au type
    (level_2 == type.level_2_value ET level_1 IN type.level_1_values).
    
    Args:
        type_id: ID du type
        db: Session de base de données
    
    Returns:
        Montant total d'immobilisation
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    level_1_values = json.loads(atype.level_1_values or "[]")
    
    if not level_1_values:
        return AmortizationTypeAmountResponse(
            type_id=atype.id,
            type_name=atype.name,
            amount=0.0
        )
    
    # Calculer la somme des transactions correspondantes
    result = db.query(func.sum(Transaction.quantite)).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_2 == atype.level_2_value,
            EnrichedTransaction.level_1.in_(level_1_values)
        )
    ).scalar()
    
    amount = abs(result) if result else 0.0
    
    return AmortizationTypeAmountResponse(
        type_id=atype.id,
        type_name=atype.name,
        amount=amount
    )


@router.get("/amortization/types/{type_id}/cumulated", response_model=AmortizationTypeCumulatedResponse)
async def get_amortization_type_cumulated(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcule le montant cumulé d'amortissement pour un type donné.
    
    Le montant cumulé est calculé dynamiquement en fonction des transactions :
    - Pour chaque transaction du type, calculer le montant cumulé jusqu'à aujourd'hui
    - Utiliser la convention 30/360 avec prorata pour l'année de la transaction
    - Si start_date est renseignée dans le type, utiliser cette date pour toutes les transactions
    - Sinon, utiliser la date de chaque transaction individuellement
    - Sommer tous les montants cumulés de toutes les transactions
    
    Args:
        type_id: ID du type
        db: Session de base de données
    
    Returns:
        Montant cumulé d'amortissement
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    # Cas particuliers
    if atype.duration <= 0:
        return AmortizationTypeCumulatedResponse(
            type_id=atype.id,
            type_name=atype.name,
            cumulated_amount=0.0
        )
    
    level_1_values = json.loads(atype.level_1_values or "[]")
    
    if not level_1_values:
        return AmortizationTypeCumulatedResponse(
            type_id=atype.id,
            type_name=atype.name,
            cumulated_amount=0.0
        )
    
    # Récupérer toutes les transactions correspondantes au type
    transactions = db.query(Transaction).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_2 == atype.level_2_value,
            EnrichedTransaction.level_1.in_(level_1_values)
        )
    ).all()
    
    if not transactions:
        return AmortizationTypeCumulatedResponse(
            type_id=atype.id,
            type_name=atype.name,
            cumulated_amount=0.0
        )
    
    # Date d'aujourd'hui
    today = date.today()
    
    # Calculer l'annuité du type (si définie, sinon sera calculée par transaction)
    annual_amount = atype.annual_amount if atype.annual_amount is not None and atype.annual_amount != 0 else None
    
    # Calculer le montant cumulé pour chaque transaction
    total_cumulated = 0.0
    
    for transaction in transactions:
        # Déterminer la date de début
        # Si start_date est renseignée dans le type, utiliser cette date (override)
        # Sinon, utiliser la date de la transaction
        start_date = atype.start_date if atype.start_date else transaction.date
        
        # Vérifier si la date de début est dans le futur
        if start_date > today:
            continue  # Montant cumulé = 0 pour cette transaction
        
        # Montant de la transaction
        transaction_amount = abs(transaction.quantite)
        
        # Calculer l'annuité pour cette transaction
        # Si annual_amount est définie dans le type, l'utiliser
        # Sinon, calculer : abs(Montant transaction) / duration
        if annual_amount is None:
            transaction_annual_amount = transaction_amount / atype.duration
        else:
            transaction_annual_amount = annual_amount
        
        # Calculer les montants par année avec calculate_yearly_amounts
        yearly_amounts = calculate_yearly_amounts(
            start_date=start_date,
            total_amount=-transaction_amount,  # Négatif car convention
            duration=atype.duration,
            annual_amount=transaction_annual_amount
        )
        
        # Sommer les montants jusqu'à l'année en cours (incluse)
        # Logique :
        # - Année d'achat : prorata (déjà calculé par calculate_yearly_amounts)
        # - Années complètes suivantes : annuité complète
        # - Année en cours : annuité complète (pas de prorata jusqu'à aujourd'hui)
        transaction_cumulated = 0.0
        
        for year, amount in yearly_amounts.items():
            if year <= today.year:
                # Prendre le montant complet de l'année (pas de prorata pour l'année en cours)
                transaction_cumulated += abs(amount)
        
        total_cumulated += transaction_cumulated
    
    return AmortizationTypeCumulatedResponse(
        type_id=atype.id,
        type_name=atype.name,
        cumulated_amount=total_cumulated
    )


@router.get("/amortization/types/{type_id}/transaction-count", response_model=AmortizationTypeTransactionCountResponse)
async def get_amortization_type_transaction_count(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Compte le nombre de transactions correspondant à un type d'amortissement.
    
    Args:
        type_id: ID du type
        db: Session de base de données
    
    Returns:
        Nombre de transactions correspondant au type
    
    Raises:
        HTTPException: Si le type n'existe pas
    """
    atype = db.query(AmortizationType).filter(AmortizationType.id == type_id).first()
    
    if not atype:
        raise HTTPException(status_code=404, detail="Type d'amortissement non trouvé")
    
    level_1_values = json.loads(atype.level_1_values or "[]")
    
    if not level_1_values:
        return AmortizationTypeTransactionCountResponse(
            type_id=atype.id,
            type_name=atype.name,
            transaction_count=0
        )
    
    # Compter les transactions correspondantes
    count = db.query(Transaction).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_2 == atype.level_2_value,
            EnrichedTransaction.level_1.in_(level_1_values)
        )
    ).count()
    
    return AmortizationTypeTransactionCountResponse(
        type_id=atype.id,
        type_name=atype.name,
        transaction_count=count
    )

