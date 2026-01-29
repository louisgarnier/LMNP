"""
Balance calculation utilities.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from sqlalchemy.orm import Session
from backend.database.models import Transaction
from datetime import date


def recalculate_balances_from_date(db: Session, from_date: date, property_id: int) -> None:
    """
    Recalcule les soldes de toutes les transactions à partir d'une date donnée pour une propriété.
    
    Args:
        db: Session de base de données
        from_date: Date à partir de laquelle recalculer (inclusive)
        property_id: ID de la propriété (obligatoire)
    """
    # Récupérer toutes les transactions triées par date - FILTRER PAR PROPERTY_ID
    all_transactions = db.query(Transaction).filter(
        Transaction.property_id == property_id
    ).order_by(Transaction.date, Transaction.id).all()
    
    if not all_transactions:
        return
    
    # Trouver l'index de la première transaction à partir de from_date
    start_index = 0
    for i, trans in enumerate(all_transactions):
        if trans.date >= from_date:
            start_index = i
            break
    
    # Si on commence au début, solde initial = 0
    # Sinon, prendre le solde de la transaction précédente
    if start_index == 0:
        current_solde = 0.0
    else:
        current_solde = all_transactions[start_index - 1].solde
    
    # Recalculer les soldes à partir de start_index
    for i in range(start_index, len(all_transactions)):
        transaction = all_transactions[i]
        current_solde = current_solde + transaction.quantite
        transaction.solde = current_solde
    
    db.commit()


def recalculate_all_balances(db: Session, property_id: int) -> None:
    """
    Recalcule tous les soldes depuis le début (solde initial = 0).
    
    Args:
        db: Session de base de données
    """
    transactions = db.query(Transaction).filter(
        Transaction.property_id == property_id
    ).order_by(Transaction.date, Transaction.id).all()
    
    current_solde = 0.0
    for transaction in transactions:
        current_solde = current_solde + transaction.quantite
        transaction.solde = current_solde
    
    db.commit()

