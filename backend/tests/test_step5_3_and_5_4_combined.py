"""
Test combiné Step 5.3 + Step 5.4

Vérifie que :
1. Step 5.3 : Mise à jour en cascade fonctionne
2. Step 5.3 : Transactions avec plusieurs mappings restent non classées
3. Step 5.4 : Validation contre allowed_mappings fonctionne
4. Step 5.4 : Validation de level_3 contre liste fixe fonctionne
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
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel,
    validate_mapping,
    validate_level3_value
)


def test_combined_step5_3_and_5_4():
    """Test combiné Step 5.3 + Step 5.4"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST COMBINÉ Step 5.3 + Step 5.4")
        print("=" * 60)
        
        # S'assurer que des mappings autorisés existent
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
                print(f"✓ Mappings autorisés chargés depuis Excel")
        
        # Récupérer des combinaisons valides
        valid_mapping = db.query(AllowedMapping).first()
        if not valid_mapping:
            print("✗ ERREUR : Aucun mapping autorisé trouvé")
            return False
        
        print(f"\nCombinaison valide utilisée : {valid_mapping.level_1} / {valid_mapping.level_2} / {valid_mapping.level_3}")
        
        # ============================================================
        # Test 1 : Step 5.3 - Mise à jour en cascade + Step 5.4 - Validation
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 1 : Step 5.3 (cascade) + Step 5.4 (validation)")
        print("=" * 60)
        
        transaction_name = "TEST_COMBINED_CASCADE"
        transactions = []
        for i in range(2):
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
        
        print(f"✓ 2 transactions créées avec le nom '{transaction_name}'")
        
        # Step 5.4 : Tester la validation avant de créer le mapping
        print(f"\n1.1. Step 5.4 : Validation de la combinaison")
        if validate_mapping(db, valid_mapping.level_1, valid_mapping.level_2, valid_mapping.level_3):
            print(f"   ✓ Combinaison valide validée")
        else:
            print(f"   ✗ ERREUR : Combinaison valide rejetée")
            return False
        
        if validate_level3_value(valid_mapping.level_3):
            print(f"   ✓ level_3 validé contre liste fixe")
        else:
            print(f"   ✗ ERREUR : level_3 valide rejeté")
            return False
        
        # Step 5.3 : Mise à jour avec combinaison valide
        print(f"\n1.2. Step 5.3 : Mise à jour de la classification (combinaison valide)")
        updated_enriched = update_transaction_classification(
            db=db,
            transaction=transactions[0],
            level_1=valid_mapping.level_1,
            level_2=valid_mapping.level_2,
            level_3=valid_mapping.level_3
        )
        print(f"   ✓ Classification mise à jour")
        
        # Step 5.4 : Créer le mapping (validation incluse)
        print(f"\n1.3. Step 5.4 : Création du mapping avec validation")
        try:
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name=transaction_name,
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3=valid_mapping.level_3
            )
            print(f"   ✓ Mapping créé avec succès")
        except ValueError as e:
            print(f"   ✗ ERREUR : Mapping rejeté alors qu'il devrait être valide")
            print(f"     Erreur: {str(e)}")
            return False
        
        # Step 5.3 : Re-enrichir toutes les transactions avec le même nom
        print(f"\n1.4. Step 5.3 : Re-enrichissement en cascade")
        all_same_name = db.query(Transaction).filter(
            Transaction.nom == transaction_name
        ).all()
        for other_transaction in all_same_name:
            if other_transaction.id != transactions[0].id:
                enrich_transaction(other_transaction, db)
        
        db.commit()
        
        # Vérifier que toutes les transactions ont été mises à jour
        all_enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id.in_([t.id for t in transactions])
        ).all()
        
        if len(all_enriched) == 2:
            print(f"   ✓ Toutes les 2 transactions ont été mises à jour en cascade")
        else:
            print(f"   ✗ ERREUR : Seulement {len(all_enriched)} transactions enrichies sur 2")
            return False
        
        # Nettoyer
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id.in_([t.id for t in transactions])
        ).delete()
        db.query(Mapping).filter(Mapping.nom == transaction_name).delete()
        for t in transactions:
            db.delete(t)
        db.commit()
        print(f"✓ Données de test nettoyées")
        
        # ============================================================
        # Test 2 : Step 5.4 - Validation rejette combinaison invalide
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 2 : Step 5.4 - Validation rejette combinaison invalide")
        print("=" * 60)
        
        test_transaction = Transaction(
            date=date(2024, 1, 25),
            quantite=300.0,
            nom="TEST_INVALID_COMBINATION",
            solde=3000.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        
        print(f"✓ Transaction créée: ID {test_transaction.id}")
        
        # Tester avec combinaison invalide
        print(f"\n2.1. Test avec combinaison invalide")
        invalid_level_1 = "INVALIDE_LEVEL_1"
        invalid_level_2 = "INVALIDE_LEVEL_2"
        invalid_level_3 = "INVALIDE_LEVEL_3"
        
        if not validate_mapping(db, invalid_level_1, invalid_level_2, invalid_level_3):
            print(f"   ✓ Combinaison invalide rejetée par validate_mapping()")
        else:
            print(f"   ✗ ERREUR : Combinaison invalide acceptée")
            return False
        
        # Tester create_or_update_mapping_from_classification avec combinaison invalide
        print(f"\n2.2. Test create_or_update_mapping_from_classification() avec combinaison invalide")
        try:
            create_or_update_mapping_from_classification(
                db=db,
                transaction_name=test_transaction.nom,
                level_1=invalid_level_1,
                level_2=invalid_level_2,
                level_3=invalid_level_3
            )
            print(f"   ✗ ERREUR : Mapping créé alors qu'il devrait être rejeté")
            return False
        except ValueError as e:
            print(f"   ✓ ValueError levée (attendu)")
            print(f"     Message: {str(e)[:100]}...")
        
        # Tester avec level_3 invalide
        print(f"\n2.3. Test avec level_3 invalide (pas dans liste fixe)")
        invalid_level_3_value = "INVALIDE"
        if not validate_level3_value(invalid_level_3_value):
            print(f"   ✓ level_3 invalide rejeté par validate_level3_value()")
        else:
            print(f"   ✗ ERREUR : level_3 invalide accepté")
            return False
        
        try:
            create_or_update_mapping_from_classification(
                db=db,
                transaction_name=test_transaction.nom,
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3=invalid_level_3_value
            )
            print(f"   ✗ ERREUR : Mapping créé avec level_3 invalide")
            return False
        except ValueError as e:
            print(f"   ✓ ValueError levée pour level_3 invalide (attendu)")
            print(f"     Message: {str(e)[:100]}...")
        
        # Nettoyer
        db.delete(test_transaction)
        db.commit()
        print(f"✓ Données de test nettoyées")
        
        # ============================================================
        # Test 3 : Step 5.3 - Plusieurs mappings → transaction non classée
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 3 : Step 5.3 - Plusieurs mappings → transaction non classée")
        print("=" * 60)
        
        test_transaction2 = Transaction(
            date=date(2024, 1, 30),
            quantite=400.0,
            nom="TEST_MULTIPLE_MAPPINGS_COMBINED",
            solde=4000.0
        )
        db.add(test_transaction2)
        db.commit()
        db.refresh(test_transaction2)
        
        print(f"✓ Transaction créée: ID {test_transaction2.id}")
        
        # Créer 2 mappings qui correspondent
        mapping1 = Mapping(
            nom=test_transaction2.nom,
            level_1=valid_mapping.level_1,
            level_2=valid_mapping.level_2,
            level_3=valid_mapping.level_3,
            is_prefix_match=True,
            priority=0
        )
        db.add(mapping1)
        
        # Récupérer une autre combinaison valide
        other_valid = db.query(AllowedMapping).offset(1).first()
        if other_valid:
            prefix_name = test_transaction2.nom[:len(test_transaction2.nom)//2]
            if len(prefix_name) > 3:
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
                
                print(f"\n3.1. Création de 2 mappings qui correspondent")
                print(f"   - Mapping 1: '{mapping1.nom}'")
                print(f"   - Mapping 2: '{mapping2.nom}' (préfixe)")
                
                # Step 5.3 : find_best_mapping doit retourner None
                print(f"\n3.2. Step 5.3 : Test find_best_mapping() avec plusieurs mappings")
                all_mappings = db.query(Mapping).all()
                best_mapping = find_best_mapping(test_transaction2.nom, all_mappings)
                
                if best_mapping is None:
                    print(f"   ✓ find_best_mapping() retourne None (attendu)")
                else:
                    print(f"   ✗ ERREUR : find_best_mapping() a retourné un mapping")
                    return False
                
                # Enrichir et vérifier qu'elle reste non classée
                print(f"\n3.3. Enrichissement de la transaction")
                enriched = enrich_transaction(test_transaction2, db)
                
                if enriched.level_1 is None and enriched.level_2 is None and enriched.level_3 is None:
                    print(f"   ✓ Transaction reste non classée (Step 5.3)")
                else:
                    print(f"   ✗ ERREUR : Transaction a été classée")
                    return False
                
                # Nettoyer
                db.query(EnrichedTransaction).filter(
                    EnrichedTransaction.transaction_id == test_transaction2.id
                ).delete()
                db.delete(mapping1)
                db.delete(mapping2)
                db.delete(test_transaction2)
                db.commit()
            else:
                db.delete(mapping1)
                db.delete(test_transaction2)
                db.commit()
        else:
            db.delete(mapping1)
            db.delete(test_transaction2)
            db.commit()
        
        print("\n" + "=" * 60)
        print("✓ TOUS LES TESTS COMBINÉS Step 5.3 + Step 5.4 PASSENT")
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
    success = test_combined_step5_3_and_5_4()
    sys.exit(0 if success else 1)

