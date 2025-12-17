"""
API routes for transactions.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from backend.database import get_db
from backend.database.models import Transaction
from backend.api.models import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse
)

router = APIRouter()


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    start_date: Optional[date] = Query(None, description="Date de début (filtre)"),
    end_date: Optional[date] = Query(None, description="Date de fin (filtre)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des transactions.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    - **start_date**: Filtrer par date de début (optionnel)
    - **end_date**: Filtrer par date de fin (optionnel)
    """
    query = db.query(Transaction)
    
    # Filtres optionnels
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    # Compter le total
    total = query.count()
    
    # Pagination
    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    
    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer une transaction par son ID.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    return TransactionResponse.model_validate(transaction)


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle transaction.
    """
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return TransactionResponse.from_orm(db_transaction)


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une transaction existante.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Mettre à jour uniquement les champs fournis
    update_data = transaction_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    return TransactionResponse.from_orm(db_transaction)


@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une transaction.
    Note: Supprime également les données enrichies associées.
    """
    from backend.database.models import EnrichedTransaction, Amortization
    
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Supprimer les données associées en cascade
    db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction_id
    ).delete()
    
    db.query(Amortization).filter(
        Amortization.transaction_id == transaction_id
    ).delete()
    
    # Supprimer la transaction
    db.delete(db_transaction)
    db.commit()
    
    return None

