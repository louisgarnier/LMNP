"""
Test : Re-enrichir toutes les transactions avec la nouvelle logique de find_best_mapping
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction
from backend.api.services.enrichment_service import enrich_transaction, enrich_all_transactions


def test_re_enrich():
    """Re-enrichir toutes les transactions"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST : Re-enrichissement de toutes les transactions")
        print("=" * 60)
        
        transaction_name = "VIR MANGOPAY D64E8E716D144BFD99C45E0C6B9FF431 MASTEOS 6911163C LOYER 1 HOMEGA"
        
        # Trouver la transaction
        transaction = db.query(Transaction).filter(
            Transaction.nom == transaction_name
        ).first()
        
        if transaction:
            print(f"\n1. Transaction trouvée : ID {transaction.id}")
            
            # Re-enrichir cette transaction
            print(f"\n2. Re-enrichissement de la transaction...")
            enriched = enrich_transaction(transaction, db)
            
            print(f"   Résultat :")
            print(f"     - level_1: {enriched.level_1}")
            print(f"     - level_2: {enriched.level_2}")
            print(f"     - level_3: {enriched.level_3}")
            
            if enriched.level_1 and enriched.level_2:
                print(f"   ✓ Transaction maintenant classée !")
            else:
                print(f"   ✗ Transaction toujours non classée")
        else:
            print(f"   ⚠ Transaction non trouvée")
        
        # Re-enrichir toutes les transactions
        print(f"\n3. Re-enrichissement de toutes les transactions...")
        enriched_count, already_enriched_count = enrich_all_transactions(db)
        print(f"   - Nouvelles enrichies : {enriched_count}")
        print(f"   - Re-enrichies : {already_enriched_count}")
        print(f"   - Total : {enriched_count + already_enriched_count}")
        
        # Vérifier à nouveau la transaction
        if transaction:
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            
            if enriched:
                print(f"\n4. État final de la transaction :")
                print(f"     - level_1: {enriched.level_1}")
                print(f"     - level_2: {enriched.level_2}")
                print(f"     - level_3: {enriched.level_3}")
                
                if enriched.level_1 and enriched.level_2:
                    print(f"   ✓ Transaction maintenant classée !")
                else:
                    print(f"   ✗ Transaction toujours non classée")
        
        print("\n" + "=" * 60)
        print("FIN DU TEST")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERREUR DE TEST : {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    success = test_re_enrich()
    sys.exit(0 if success else 1)

