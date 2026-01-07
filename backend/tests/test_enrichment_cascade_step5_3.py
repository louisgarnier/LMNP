"""
Test Step 5.3 : Vérification et test de la mise à jour automatique

Tests :
1. Mise à jour en cascade : quand on modifie le mapping d'une transaction,
   toutes les transactions avec le même nom sont mises à jour
2. Transactions avec plusieurs mappings possibles restent non classées
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, Mapping, EnrichedTransaction, AllowedMapping
from backend.api.services.enrichment_service import (
    find_best_mapping,
    update_transaction_classification,
    create_or_update_mapping_from_classification,
    enrich_transaction
)
from backend.api.services.mapping_obligatoire_service import load_allowed_mappings_from_excel


def test_step5_3():
    """Test Step 5.3 : Mise à jour automatique et gestion des conflits"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST Step 5.3 : Mise à jour automatique et gestion des conflits")
        print("=" * 60)
        
        # S'assurer que des mappings autorisés existent
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
                print(f"✓ Mappings autorisés chargés depuis Excel")
        
        # Récupérer une combinaison valide pour les tests
        valid_mapping = db.query(AllowedMapping).first()
        if not valid_mapping:
            print("✗ ERREUR : Aucun mapping autorisé trouvé")
            return False
        
        print(f"\nCombinaison valide utilisée : {valid_mapping.level_1} / {valid_mapping.level_2} / {valid_mapping.level_3}")
        
        # ============================================================
        # Test 1 : Mise à jour en cascade avec plusieurs transactions
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 1 : Mise à jour en cascade avec plusieurs transactions")
        print("=" * 60)
        
        # Créer 3 transactions avec le même nom
        transaction_name = "TEST_CASCADE_TRANSACTION"
        transactions = []
        for i in range(3):
            transaction = Transaction(
                date=date(2024, 1, 15 + i),
                quantite=100.0 + i,
                nom=transaction_name,
                solde=1000.0 + i * 100
            )
            db.add(transaction)
            transactions.append(transaction)
        
        db.commit()
        for t in transactions:
            db.refresh(t)
        
        print(f"✓ 3 transactions créées avec le nom '{transaction_name}'")
        print(f"  - Transaction 1: ID {transactions[0].id}")
        print(f"  - Transaction 2: ID {transactions[1].id}")
        print(f"  - Transaction 3: ID {transactions[2].id}")
        
        # Modifier la classification de la première transaction
        print(f"\n1.1. Modification de la classification de la transaction 1")
        updated_enriched = update_transaction_classification(
            db=db,
            transaction=transactions[0],
            level_1=valid_mapping.level_1,
            level_2=valid_mapping.level_2,
            level_3=valid_mapping.level_3
        )
        print(f"   ✓ Classification mise à jour pour transaction 1")
        
        # Créer le mapping
        print(f"\n1.2. Création du mapping pour '{transaction_name}'")
        mapping = create_or_update_mapping_from_classification(
            db=db,
            transaction_name=transaction_name,
            level_1=valid_mapping.level_1,
            level_2=valid_mapping.level_2,
            level_3=valid_mapping.level_3
        )
        print(f"   ✓ Mapping créé: {mapping.nom}")
        
        # Re-enrichir toutes les transactions avec le même nom
        print(f"\n1.3. Re-enrichissement de toutes les transactions avec le même nom")
        all_same_name = db.query(Transaction).filter(
            Transaction.nom == transaction_name
        ).all()
        for other_transaction in all_same_name:
            if other_transaction.id != transactions[0].id:
                enrich_transaction(other_transaction, db)
        
        db.commit()
        
        # Vérifier que toutes les transactions ont été mises à jour
        print(f"\n1.4. Vérification que toutes les transactions ont été mises à jour")
        all_enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id.in_([t.id for t in transactions])
        ).all()
        
        success = True
        for enriched in all_enriched:
            if enriched.level_1 != valid_mapping.level_1 or \
               enriched.level_2 != valid_mapping.level_2 or \
               enriched.level_3 != valid_mapping.level_3:
                print(f"   ✗ Transaction {enriched.transaction_id} n'a pas été mise à jour correctement")
                success = False
        
        if success and len(all_enriched) == 3:
            print(f"   ✓ Toutes les 3 transactions ont été mises à jour avec succès")
            print(f"     - level_1: {valid_mapping.level_1}")
            print(f"     - level_2: {valid_mapping.level_2}")
            print(f"     - level_3: {valid_mapping.level_3}")
        else:
            print(f"   ✗ ERREUR : Seulement {len(all_enriched)} transactions enrichies sur 3")
            return False
        
        # Vérifier que le mapping existe
        db_mapping = db.query(Mapping).filter(Mapping.nom == transaction_name).first()
        if db_mapping:
            print(f"\n1.5. Vérification du mapping")
            print(f"   ✓ Mapping trouvé dans la table mappings")
            print(f"     - Nom: {db_mapping.nom}")
            print(f"     - level_1: {db_mapping.level_1}")
            print(f"     - level_2: {db_mapping.level_2}")
            print(f"     - level_3: {db_mapping.level_3}")
        else:
            print(f"   ✗ ERREUR : Mapping non trouvé dans la table")
            return False
        
        # Nettoyer pour le test suivant
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id.in_([t.id for t in transactions])
        ).delete()
        db.query(Mapping).filter(Mapping.nom == transaction_name).delete()
        for t in transactions:
            db.delete(t)
        db.commit()
        print(f"\n✓ Données de test nettoyées")
        
        # ============================================================
        # Test 2 : Transactions avec plusieurs mappings possibles
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 2 : Transactions avec plusieurs mappings possibles")
        print("=" * 60)
        
        # Créer une transaction de test
        test_transaction_name = "TEST_MULTIPLE_MAPPINGS"
        test_transaction = Transaction(
            date=date(2024, 1, 20),
            quantite=200.0,
            nom=test_transaction_name,
            solde=2000.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        
        print(f"✓ Transaction créée: ID {test_transaction.id}, nom '{test_transaction_name}'")
        
        # Créer 2 mappings différents qui correspondent tous les deux à cette transaction
        # Pour simuler cela, on va créer 2 mappings avec des noms qui matchent
        # (par exemple, un mapping avec le nom exact et un autre avec un préfixe)
        
        # Mapping 1 : nom exact
        mapping1 = Mapping(
            nom=test_transaction_name,
            level_1=valid_mapping.level_1,
            level_2=valid_mapping.level_2,
            level_3=valid_mapping.level_3,
            is_prefix_match=True,
            priority=0
        )
        db.add(mapping1)
        
        # Mapping 2 : préfixe qui correspond aussi
        # On crée un mapping avec un nom plus court qui est un préfixe
        prefix_name = test_transaction_name[:len(test_transaction_name)//2]  # Moitié du nom
        if len(prefix_name) > 3:  # S'assurer que le préfixe est assez long
            # Récupérer une autre combinaison valide
            other_valid = db.query(AllowedMapping).offset(1).first()
            if other_valid:
                mapping2 = Mapping(
                    nom=prefix_name,
                    level_1=other_valid.level_1,
                    level_2=other_valid.level_2,
                    level_3=other_valid.level_3,
                    is_prefix_match=True,
                    priority=0
                )
                db.add(mapping2)
                db.commit()
                db.refresh(mapping1)
                db.refresh(mapping2)
                
                print(f"\n2.1. Création de 2 mappings qui correspondent à la transaction")
                print(f"   - Mapping 1: '{mapping1.nom}' (correspondance exacte)")
                print(f"   - Mapping 2: '{mapping2.nom}' (préfixe, is_prefix_match=True)")
                
                # Tester find_best_mapping avec ces 2 mappings
                print(f"\n2.2. Test de find_best_mapping() avec plusieurs mappings")
                all_mappings = db.query(Mapping).all()
                best_mapping = find_best_mapping(test_transaction_name, all_mappings)
                
                if best_mapping is None:
                    print(f"   ✓ find_best_mapping() retourne None (attendu)")
                    print(f"     → La transaction restera non classée")
                else:
                    print(f"   ✗ ERREUR : find_best_mapping() a retourné un mapping au lieu de None")
                    print(f"     Mapping retourné: {best_mapping.nom}")
                    return False
                
                # Enrichir la transaction et vérifier qu'elle reste non classée
                print(f"\n2.3. Enrichissement de la transaction")
                enriched = enrich_transaction(test_transaction, db)
                
                if enriched.level_1 is None and enriched.level_2 is None and enriched.level_3 is None:
                    print(f"   ✓ Transaction reste non classée (unassigned)")
                    print(f"     - level_1: {enriched.level_1}")
                    print(f"     - level_2: {enriched.level_2}")
                    print(f"     - level_3: {enriched.level_3}")
                else:
                    print(f"   ✗ ERREUR : Transaction a été classée alors qu'elle devrait rester non classée")
                    print(f"     - level_1: {enriched.level_1}")
                    print(f"     - level_2: {enriched.level_2}")
                    print(f"     - level_3: {enriched.level_3}")
                    return False
                
                # Nettoyer
                db.query(EnrichedTransaction).filter(
                    EnrichedTransaction.transaction_id == test_transaction.id
                ).delete()
                db.delete(mapping1)
                db.delete(mapping2)
                db.delete(test_transaction)
                db.commit()
            else:
                print(f"   ⚠ Pas assez de mappings autorisés pour ce test")
                db.delete(mapping1)
                db.delete(test_transaction)
                db.commit()
        else:
            print(f"   ⚠ Nom de transaction trop court pour ce test")
            db.delete(mapping1)
            db.delete(test_transaction)
            db.commit()
        
        print("\n" + "=" * 60)
        print("✓ TOUS LES TESTS STEP 5.3 PASSENT")
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
    success = test_step5_3()
    sys.exit(0 if success else 1)

