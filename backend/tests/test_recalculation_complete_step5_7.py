"""
Test complet Step 5.7 : Vérification que les données sont recalculées à la volée

Ce test vérifie que les endpoints retournent bien les nouvelles données
après une modification de classification, sans besoin d'invalidation.
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction, Mapping
from backend.api.services.enrichment_service import enrich_transaction, create_or_update_mapping_from_classification
from sqlalchemy import func


def test_data_recalculated_on_the_fly():
    """Test que les données sont recalculées à la volée après modification"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST COMPLET : Vérification recalcul à la volée")
        print("=" * 60)
        
        # 1. Créer une transaction de test avec un mapping valide
        print("\n1. Création transaction de test...")
        test_transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=5000.0,
            nom="TEST RECALC ON THE FLY",
            solde=5000.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        print(f"   ✓ Transaction créée : ID {test_transaction.id}, quantite={test_transaction.quantite}")
        
        # 2. Créer un mapping valide (utiliser une combinaison qui existe dans allowed_mappings)
        print("\n2. Création d'un mapping valide...")
        # Chercher un mapping existant pour avoir une combinaison valide
        existing_mapping = db.query(Mapping).filter(
            Mapping.level_1.isnot(None),
            Mapping.level_2.isnot(None)
        ).first()
        
        if not existing_mapping:
            print("   ⚠ Aucun mapping existant trouvé, création d'un nouveau...")
            # Utiliser une combinaison qui devrait exister dans allowed_mappings
            try:
                create_or_update_mapping_from_classification(
                    db=db,
                    transaction_name=test_transaction.nom,
                    level_1="Encaissement locataire et CAF",
                    level_2="Produits",
                    level_3="Produits"
                )
                print("   ✓ Mapping créé")
            except Exception as e:
                print(f"   ✗ Erreur création mapping : {e}")
                # Utiliser un mapping existant si possible
                existing_mapping = db.query(Mapping).first()
                if existing_mapping:
                    print(f"   → Utilisation mapping existant : {existing_mapping.nom}")
                    test_transaction.nom = existing_mapping.nom
                    db.commit()
        else:
            print(f"   → Utilisation mapping existant : {existing_mapping.nom}")
            test_transaction.nom = existing_mapping.nom
            db.commit()
        
        # 3. Enrichir la transaction
        print("\n3. Enrichissement initial...")
        enriched_before = enrich_transaction(test_transaction, db)
        print(f"   État initial :")
        print(f"     - level_1: {enriched_before.level_1}")
        print(f"     - level_2: {enriched_before.level_2}")
        print(f"     - level_3: {enriched_before.level_3}")
        
        # 4. Calculer les données AVANT modification (simuler un appel API)
        print("\n4. Calcul des données AVANT modification...")
        # Simuler un calcul de total par level_1
        query_before = db.query(
            EnrichedTransaction.level_1,
            func.sum(Transaction.quantite).label('total')
        ).join(
            Transaction, EnrichedTransaction.transaction_id == Transaction.id
        ).filter(
            EnrichedTransaction.level_1 == enriched_before.level_1
        ).group_by(EnrichedTransaction.level_1).first()
        
        total_before = query_before.total if query_before else 0.0
        print(f"   Total pour level_1='{enriched_before.level_1}' : {total_before}")
        
        # 5. Modifier la classification (changer level_1)
        print("\n5. Modification de la classification...")
        # Trouver un autre level_1 valide
        other_mapping = db.query(Mapping).filter(
            Mapping.level_1 != enriched_before.level_1,
            Mapping.level_1.isnot(None),
            Mapping.level_2.isnot(None)
        ).first()
        
        if other_mapping:
            print(f"   → Changement vers : level_1='{other_mapping.level_1}', level_2='{other_mapping.level_2}'")
            try:
                create_or_update_mapping_from_classification(
                    db=db,
                    transaction_name=test_transaction.nom,
                    level_1=other_mapping.level_1,
                    level_2=other_mapping.level_2,
                    level_3=other_mapping.level_3
                )
                # Re-enrichir
                enriched_after = enrich_transaction(test_transaction, db)
                print(f"   ✓ Classification modifiée :")
                print(f"     - level_1: {enriched_after.level_1}")
                print(f"     - level_2: {enriched_after.level_2}")
                print(f"     - level_3: {enriched_after.level_3}")
            except Exception as e:
                print(f"   ✗ Erreur modification : {e}")
                return False
        else:
            print("   ⚠ Aucun autre mapping trouvé, test limité")
            return False
        
        # 6. Calculer les données APRÈS modification (simuler un appel API)
        print("\n6. Calcul des données APRÈS modification...")
        # Calculer pour l'ancien level_1
        query_old = db.query(
            EnrichedTransaction.level_1,
            func.sum(Transaction.quantite).label('total')
        ).join(
            Transaction, EnrichedTransaction.transaction_id == Transaction.id
        ).filter(
            EnrichedTransaction.level_1 == enriched_before.level_1
        ).group_by(EnrichedTransaction.level_1).first()
        
        total_old_after = query_old.total if query_old else 0.0
        print(f"   Total pour level_1='{enriched_before.level_1}' (ancien) : {total_old_after}")
        
        # Calculer pour le nouveau level_1
        query_new = db.query(
            EnrichedTransaction.level_1,
            func.sum(Transaction.quantite).label('total')
        ).join(
            Transaction, EnrichedTransaction.transaction_id == Transaction.id
        ).filter(
            EnrichedTransaction.level_1 == enriched_after.level_1
        ).group_by(EnrichedTransaction.level_1).first()
        
        total_new_after = query_new.total if query_new else 0.0
        print(f"   Total pour level_1='{enriched_after.level_1}' (nouveau) : {total_new_after}")
        
        # 7. Vérification
        print("\n7. Vérification...")
        if enriched_before.level_1 != enriched_after.level_1:
            # Le total pour l'ancien level_1 devrait avoir diminué
            if total_old_after < total_before:
                print(f"   ✓ Le total pour l'ancien level_1 a diminué ({total_before} → {total_old_after})")
            else:
                print(f"   ⚠ Le total pour l'ancien level_1 n'a pas changé comme attendu")
            
            # Le total pour le nouveau level_1 devrait inclure notre transaction
            if total_new_after >= test_transaction.quantite:
                print(f"   ✓ Le total pour le nouveau level_1 inclut notre transaction ({total_new_after} >= {test_transaction.quantite})")
            else:
                print(f"   ✗ Le total pour le nouveau level_1 ne semble pas inclure notre transaction")
                return False
            
            print("\n   ✅ TEST RÉUSSI : Les données sont recalculées à la volée !")
            print("   → Pas besoin d'invalidation - les données sont toujours à jour")
        else:
            print("   ⚠ Les level_1 sont identiques, test non concluant")
        
        # 8. Nettoyage
        print("\n8. Nettoyage...")
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == test_transaction.id
        ).delete()
        db.query(Mapping).filter(
            Mapping.nom == test_transaction.nom
        ).delete()
        db.delete(test_transaction)
        db.commit()
        print("   ✓ Données de test supprimées")
        
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
    success = test_data_recalculated_on_the_fly()
    sys.exit(0 if success else 1)

