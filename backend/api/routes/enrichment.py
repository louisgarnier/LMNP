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
from backend.api.services.mapping_obligatoire_service import (
    validate_mapping,
    validate_level3_value
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
    
    # Validation contre allowed_mappings (Step 5.4)
    if final_level_1 and final_level_2:
        # Valider que level_3 est dans la liste fixe si fourni
        if final_level_3 and not validate_level3_value(final_level_3):
            raise HTTPException(
                status_code=400,
                detail=f"La valeur level_3 '{final_level_3}' n'est pas autorisée. Valeurs autorisées : Passif, Produits, Emprunt, Charges Déductibles, Actif"
            )
        
        # Valider que la combinaison existe dans allowed_mappings pour cette propriété
        if not validate_mapping(db, final_level_1, final_level_2, final_level_3, transaction.property_id):
            raise HTTPException(
                status_code=400,
                detail=f"La combinaison (level_1='{final_level_1}', level_2='{final_level_2}', level_3='{final_level_3}') n'est pas autorisée pour cette propriété. Veuillez utiliser une combinaison valide depuis les mappings autorisés."
            )
    
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
        try:
            create_or_update_mapping_from_classification(
                db=db,
                transaction_name=transaction.nom,
                level_1=final_level_1,
                level_2=final_level_2,
                level_3=final_level_3,
                property_id=transaction.property_id  # Passer property_id pour l'isolation multi-propriétés
            )
        except ValueError as e:
            # La validation dans create_or_update_mapping_from_classification a échoué
            raise HTTPException(status_code=400, detail=str(e))
        
        # Après avoir mis à jour le mapping, re-enrichir TOUTES les transactions
        # avec le même nom (correspondance exacte) pour qu'elles utilisent le nouveau mapping
        # Step 5.3 : Utiliser correspondance exacte du nom au lieu de matching par préfixe
        # IMPORTANT: Filtrer par property_id pour l'isolation multi-propriétés
        all_transactions = db.query(Transaction).filter(
            Transaction.nom == transaction.nom,
            Transaction.property_id == transaction.property_id
        ).all()
        
        # Liste des IDs de transactions à recalculer (incluant la transaction modifiée)
        transaction_ids_to_recalculate = [transaction_id]
        
        for other_transaction in all_transactions:
            if other_transaction.id != transaction.id:  # Ne pas re-enrichir la transaction qu'on vient de modifier
                enrich_transaction(other_transaction, db)
                # Ajouter cette transaction à la liste des transactions à recalculer
                transaction_ids_to_recalculate.append(other_transaction.id)
        
        db.commit()
    
    # Recharger la transaction avec les données enrichies
    db.refresh(transaction)
    
    # Recalculer les amortissements pour TOUTES les transactions affectées
    # (la transaction modifiée + toutes les transactions re-enrichies avec le même nom)
    # (gestion silencieuse des erreurs pour ne pas bloquer la modification)
    try:
        from backend.api.services.amortization_service import recalculate_transaction_amortization
        for tid in transaction_ids_to_recalculate:
            try:
                recalculate_transaction_amortization(db, tid)
            except Exception as e:
                # Log l'erreur pour cette transaction spécifique mais continue avec les autres
                import traceback
                error_details = traceback.format_exc()
                print(f"⚠️ [update_transaction_classifications] Erreur lors du recalcul des amortissements pour transaction {tid}: {error_details}")
    except Exception as e:
        # Log l'erreur globale mais ne bloque pas la modification
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_transaction_classifications] Erreur lors du recalcul des amortissements: {error_details}")
    
    # Invalider tous les bilans (les classifications ont changé)
    try:
        from backend.api.services.bilan_service import invalidate_all_bilan
        invalidate_all_bilan(db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_transaction_classifications] Erreur lors de l'invalidation du bilan: {error_details}")
    
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
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    db: Session = Depends(get_db)
):
    """
    Re-enrichit toutes les transactions d'une propriété avec les mappings disponibles.
    
    Utile après avoir importé de nouveaux mappings pour que toutes les transactions
    de cette propriété soient re-enrichies avec les nouveaux mappings.
    
    Args:
        property_id: ID de la propriété (obligatoire)
        db: Session de base de données
    
    Returns:
        Dict avec le nombre de transactions enrichies et déjà enrichies pour cette propriété
    """
    from backend.api.utils.validation import validate_property_id
    import logging
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"[Enrichment] POST /enrichment/re-enrich - property_id={property_id}")
    
    # Valider property_id
    validate_property_id(db, property_id, "Enrichment")
    
    # Re-enrichir uniquement les transactions de cette propriété
    enriched_count, already_enriched_count = enrich_all_transactions(db, property_id=property_id)
    db.commit()
    
    logger.info(f"[Enrichment] Re-enrichissement terminé pour property_id={property_id}: {enriched_count} nouvelles, {already_enriched_count} re-enrichies")
    
    return {
        "enriched_count": enriched_count,
        "already_enriched_count": already_enriched_count,
        "total_processed": enriched_count + already_enriched_count,
        "message": f"Re-enrichissement terminé: {enriched_count} nouvelles enrichies, {already_enriched_count} re-enrichies"
    }

