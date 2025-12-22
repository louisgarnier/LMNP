"""
API routes for transaction enrichment.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import Transaction, EnrichedTransaction
from backend.api.models import TransactionResponse
from backend.api.services.enrichment_service import (
    update_transaction_classification,
    create_or_update_mapping_from_classification,
    enrich_transaction,
    transaction_matches_mapping_name,
    enrich_all_transactions
)

router = APIRouter()


@router.put("/enrichment/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_classifications(
    transaction_id: int,
    level_1: str | None = Query(None, description="Nouvelle valeur pour level_1"),
    level_2: str | None = Query(None, description="Nouvelle valeur pour level_2"),
    level_3: str | None = Query(None, description="Nouvelle valeur pour level_3"),
    db: Session = Depends(get_db)
):
    """
    Modifier les classifications (level_1, level_2, level_3) d'une transaction.
    
    Cette fonction :
    1. Met à jour les classifications de la transaction
    2. Crée ou met à jour automatiquement un mapping pour le nom de la transaction
    
    Args:
        transaction_id: ID de la transaction à modifier
        level_1: Nouvelle valeur pour level_1 (optionnel)
        level_2: Nouvelle valeur pour level_2 (optionnel)
        level_3: Nouvelle valeur pour level_3 (optionnel)
        db: Session de base de données
    
    Returns:
        Transaction mise à jour avec les nouvelles classifications
    
    Raises:
        HTTPException: Si la transaction n'existe pas
    """
    # Récupérer la transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction avec ID {transaction_id} non trouvée")
    
    # Récupérer les valeurs actuelles de l'enriched_transaction si elles existent
    existing_enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction.id
    ).first()
    
    # Utiliser les nouvelles valeurs si fournies, sinon garder les valeurs existantes
    final_level_1 = level_1 if level_1 is not None else (existing_enriched.level_1 if existing_enriched else None)
    final_level_2 = level_2 if level_2 is not None else (existing_enriched.level_2 if existing_enriched else None)
    final_level_3 = level_3 if level_3 is not None else (existing_enriched.level_3 if existing_enriched else None)
    
    # Mettre à jour les classifications
    updated_enriched = update_transaction_classification(
        db=db,
        transaction=transaction,
        level_1=level_1,
        level_2=level_2,
        level_3=level_3
    )
    
    # Créer ou mettre à jour le mapping automatiquement
    # Le mapping est la source de vérité, donc on crée/mise à jour un mapping
    # avec le nom de la transaction et les classifications finales (nouvelles ou existantes)
    if final_level_1 and final_level_2:  # level_1 et level_2 sont obligatoires, level_3 est optionnel
        create_or_update_mapping_from_classification(
            db=db,
            transaction_name=transaction.nom,
            level_1=final_level_1,
            level_2=final_level_2,
            level_3=final_level_3
        )
        
        # Après avoir mis à jour le mapping, re-enrichir TOUTES les transactions
        # avec le même nom pour qu'elles utilisent le nouveau mapping
        all_transactions = db.query(Transaction).all()
        for other_transaction in all_transactions:
            if other_transaction.id != transaction.id:  # Ne pas re-enrichir la transaction qu'on vient de modifier
                if transaction_matches_mapping_name(other_transaction.nom, transaction.nom):
                    enrich_transaction(other_transaction, db)
        
        db.commit()
    
    # Recharger la transaction avec les données enrichies
    db.refresh(transaction)
    
    # Construire la réponse avec les données enrichies
    enriched_data = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction.id
    ).first()
    
    return TransactionResponse(
        id=transaction.id,
        date=transaction.date,
        quantite=transaction.quantite,
        nom=transaction.nom,
        solde=transaction.solde,
        source_file=transaction.source_file,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
        level_1=enriched_data.level_1 if enriched_data else None,
        level_2=enriched_data.level_2 if enriched_data else None,
        level_3=enriched_data.level_3 if enriched_data else None,
    )


@router.post("/enrichment/re-enrich")
async def re_enrich_all_transactions(
    db: Session = Depends(get_db)
):
    """
    Re-enrichit toutes les transactions avec les mappings disponibles.
    
    Utile après avoir importé de nouveaux mappings pour que toutes les transactions
    soient re-enrichies avec les nouveaux mappings.
    
    Returns:
        Dict avec le nombre de transactions enrichies et déjà enrichies
    """
    enriched_count, already_enriched_count = enrich_all_transactions(db)
    db.commit()
    
    return {
        "enriched_count": enriched_count,
        "already_enriched_count": already_enriched_count,
        "total_processed": enriched_count + already_enriched_count,
        "message": f"Re-enrichissement terminé: {enriched_count} nouvelles enrichies, {already_enriched_count} re-enrichies"
    }

