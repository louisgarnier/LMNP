"""
Script pour forcer le réenrichissement des transactions pour le mapping ID 420 (PRLV SEPA FREE TELECOM).

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, Mapping, EnrichedTransaction
from backend.api.services.enrichment_service import enrich_transaction, transaction_matches_mapping_name

def re_enrich_mapping_420():
    """Réenrichir toutes les transactions pour le mapping ID 420."""
    db = SessionLocal()
    
    try:
        # Récupérer le mapping ID 420
        mapping = db.query(Mapping).filter(Mapping.id == 420).first()
        if not mapping:
            print("❌ ERREUR: Mapping ID 420 non trouvé")
            return False
        
        print(f"✅ Mapping trouvé: ID={mapping.id}, property_id={mapping.property_id}, nom='{mapping.nom}'")
        print(f"   level_1={mapping.level_1}, level_2={mapping.level_2}, level_3={mapping.level_3}")
        
        # Récupérer toutes les transactions de cette propriété
        all_transactions = db.query(Transaction).filter(
            Transaction.property_id == mapping.property_id
        ).all()
        
        print(f"\n📋 {len(all_transactions)} transaction(s) trouvée(s) pour property_id={mapping.property_id}")
        
        # Filtrer les transactions qui correspondent au mapping
        transactions_to_re_enrich = []
        for transaction in all_transactions:
            if transaction_matches_mapping_name(transaction.nom, mapping.nom):
                transactions_to_re_enrich.append(transaction)
        
        print(f"✅ {len(transactions_to_re_enrich)} transaction(s) correspondent au mapping '{mapping.nom}'")
        
        if not transactions_to_re_enrich:
            print("⚠️  Aucune transaction à réenrichir")
            return True
        
        # Afficher quelques exemples
        print("\n📋 Exemples de transactions à réenrichir:")
        for i, transaction in enumerate(transactions_to_re_enrich[:5]):
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            current_levels = f"level_1={enriched.level_1 if enriched else 'NULL'}, level_2={enriched.level_2 if enriched else 'NULL'}, level_3={enriched.level_3 if enriched else 'NULL'}" if enriched else "Non enrichie"
            print(f"   {i+1}. Transaction ID={transaction.id}, nom='{transaction.nom}' ({current_levels})")
        
        if len(transactions_to_re_enrich) > 5:
            print(f"   ... et {len(transactions_to_re_enrich) - 5} autre(s)")
        
        # Charger tous les mappings de cette propriété
        property_mappings = db.query(Mapping).filter(Mapping.property_id == mapping.property_id).all()
        print(f"\n📋 {len(property_mappings)} mapping(s) chargé(s) pour property_id={mapping.property_id}")
        
        # Réenrichir les transactions
        print("\n🔄 Réenrichissement en cours...")
        enriched_count = 0
        updated_count = 0
        
        for i, transaction in enumerate(transactions_to_re_enrich):
            # Vérifier l'état avant
            enriched_before = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            
            before_levels = None
            if enriched_before:
                before_levels = (enriched_before.level_1, enriched_before.level_2, enriched_before.level_3)
            
            # Réenrichir
            enriched_after = enrich_transaction(transaction, db, property_mappings)
            
            # Vérifier si quelque chose a changé
            after_levels = (enriched_after.level_1, enriched_after.level_2, enriched_after.level_3)
            
            if before_levels != after_levels:
                updated_count += 1
                if not enriched_before:
                    enriched_count += 1
                    print(f"   ✅ Transaction ID={transaction.id}: Enrichie ({after_levels[0]}, {after_levels[1]}, {after_levels[2]})")
                else:
                    print(f"   ✅ Transaction ID={transaction.id}: Mise à jour ({before_levels} → {after_levels})")
            
            # Log de progression
            if (i + 1) % 10 == 0:
                print(f"   ⏳ {i + 1}/{len(transactions_to_re_enrich)} transactions traitées...")
        
        print(f"\n✅ Réenrichissement terminé:")
        print(f"   - {enriched_count} transaction(s) nouvellement enrichie(s)")
        print(f"   - {updated_count} transaction(s) mise(s) à jour")
        print(f"   - {len(transactions_to_re_enrich) - updated_count} transaction(s) inchangée(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Réenrichissement des transactions pour le mapping ID 420 ===\n")
    success = re_enrich_mapping_420()
    if not success:
        sys.exit(1)
