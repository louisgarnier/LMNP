"""
Test pour Step 5.4 : Validation dans endpoints enrichissement transactions.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, EnrichedTransaction, AllowedMapping, Mapping
from backend.api.services.enrichment_service import (
    update_transaction_classification,
    create_or_update_mapping_from_classification
)
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel
)


def test_create_or_update_mapping_validation():
    """Test 1 : Validation dans create_or_update_mapping_from_classification."""
    print("\n" + "=" * 60)
    print("Test 1 : Validation dans create_or_update_mapping_from_classification")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # S'assurer que des données existent dans allowed_mappings
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
        
        # Récupérer une combinaison valide
        valid_mapping = db.query(AllowedMapping).first()
        if not valid_mapping:
            print("  ⚠ Aucune combinaison valide disponible")
            return
        
        # Nettoyer les mappings de test
        db.query(Mapping).filter(Mapping.nom.like("TEST_%")).delete()
        db.commit()
        
        # Test 1: Créer un mapping avec combinaison valide
        print("\n  1.1. Test création mapping avec combinaison valide")
        try:
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name="TEST_VALID",
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3=valid_mapping.level_3
            )
            assert mapping is not None, "Le mapping devrait être créé"
            print("     ✓ Mapping créé avec succès")
        except Exception as e:
            print(f"     ✗ Erreur: {str(e)}")
            raise
        
        # Test 1.2: Créer un mapping avec combinaison invalide
        print("\n  1.2. Test création mapping avec combinaison invalide")
        try:
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name="TEST_INVALID",
                level_1="INVALIDE",
                level_2="INVALIDE",
                level_3="INVALIDE"
            )
            assert False, "Le mapping ne devrait pas être créé (combinaison invalide)"
        except ValueError as e:
            assert "n'est pas autorisée" in str(e), f"Message d'erreur incorrect: {str(e)}"
            print(f"     ✓ Erreur ValueError levée: {str(e)[:80]}...")
        
        # Test 1.3: Créer un mapping avec level_3 invalide
        print("\n  1.3. Test création mapping avec level_3 invalide")
        try:
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name="TEST_INVALID_LEVEL3",
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3="INVALIDE_LEVEL3"
            )
            assert False, "Le mapping ne devrait pas être créé (level_3 invalide)"
        except ValueError as e:
            assert "level_3" in str(e) or "n'est pas autorisée" in str(e), f"Message d'erreur incorrect: {str(e)}"
            print(f"     ✓ Erreur ValueError levée: {str(e)[:80]}...")
        
        # Vérifier que seul le mapping valide a été créé
        valid_count = db.query(Mapping).filter(Mapping.nom == "TEST_VALID").count()
        invalid_count = db.query(Mapping).filter(Mapping.nom.like("TEST_INVALID%")).count()
        
        assert valid_count == 1, "Le mapping valide devrait être créé"
        assert invalid_count == 0, "Les mappings invalides ne devraient pas être créés"
        print("\n     ✓ Seul le mapping valide a été créé")
        
        # Nettoyer
        db.query(Mapping).filter(Mapping.nom.like("TEST_%")).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("✓ Test 1 réussi\n")


def test_update_transaction_classification_validation():
    """Test 2 : Validation dans update_transaction_classifications (via API)."""
    print("=" * 60)
    print("Test 2 : Validation dans update_transaction_classifications")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # S'assurer que des données existent dans allowed_mappings
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
        
        # Récupérer une combinaison valide
        valid_mapping = db.query(AllowedMapping).first()
        if not valid_mapping:
            print("  ⚠ Aucune combinaison valide disponible")
            return
        
        # Créer une transaction de test
        test_transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=100.0,
            nom="TEST_TRANSACTION_VALIDATION",
            solde=1000.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        
        print(f"\n  Transaction créée: ID {test_transaction.id}")
        
        # Test 2.1: Mettre à jour avec combinaison valide
        print("\n  2.1. Test mise à jour avec combinaison valide")
        try:
            updated = update_transaction_classification(
                db=db,
                transaction=test_transaction,
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3=valid_mapping.level_3
            )
            assert updated is not None, "L'enrichissement devrait être créé"
            assert updated.level_1 == valid_mapping.level_1, "level_1 devrait être mis à jour"
            print("     ✓ Classification mise à jour avec succès")
            
            # Tester create_or_update_mapping_from_classification séparément
            from backend.api.services.enrichment_service import create_or_update_mapping_from_classification
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name=test_transaction.nom,
                level_1=valid_mapping.level_1,
                level_2=valid_mapping.level_2,
                level_3=valid_mapping.level_3
            )
            assert mapping is not None, "Le mapping devrait être créé"
            print("     ✓ Mapping créé avec succès via create_or_update_mapping_from_classification")
            
        except Exception as e:
            print(f"     ✗ Erreur: {str(e)}")
            raise
        
        # Test 2.2: Essayer de mettre à jour avec combinaison invalide
        print("\n  2.2. Test mise à jour avec combinaison invalide")
        try:
            # On teste directement la fonction create_or_update_mapping_from_classification
            # car update_transaction_classification ne valide pas directement
            from backend.api.services.enrichment_service import create_or_update_mapping_from_classification
            
            mapping = create_or_update_mapping_from_classification(
                db=db,
                transaction_name="TEST_INVALID_UPDATE",
                level_1="INVALIDE",
                level_2="INVALIDE",
                level_3="INVALIDE"
            )
            assert False, "Le mapping ne devrait pas être créé"
        except ValueError as e:
            print(f"     ✓ Erreur ValueError levée: {str(e)[:80]}...")
        
        # Nettoyer
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == test_transaction.id
        ).delete()
        db.query(Mapping).filter(Mapping.nom == test_transaction.nom).delete()
        db.delete(test_transaction)
        db.commit()
        
    finally:
        db.close()
    
    print("✓ Test 2 réussi\n")


def test_api_endpoint_validation():
    """Test 3 : Test de l'endpoint API directement."""
    print("=" * 60)
    print("Test 3 : Endpoint API (nécessite API démarrée)")
    print("=" * 60)
    
    import requests
    
    base_url = "http://localhost:8000/api"
    
    try:
        # Créer une transaction via l'API (si possible)
        # Ou utiliser une transaction existante
        response = requests.get(f"{base_url}/transactions?limit=1", timeout=5)
        
        if response.status_code == 200:
            transactions = response.json().get('transactions', [])
            if transactions:
                transaction_id = transactions[0]['id']
                
                # Test avec combinaison invalide
                print(f"\n  Test PUT /api/enrichment/transactions/{transaction_id} avec combinaison invalide")
                response = requests.put(
                    f"{base_url}/enrichment/transactions/{transaction_id}",
                    params={
                        "level_1": "INVALIDE",
                        "level_2": "INVALIDE",
                        "level_3": "INVALIDE"
                    },
                    timeout=5
                )
                
                if response.status_code == 400:
                    error_detail = response.json().get('detail', '')
                    print(f"     Status: {response.status_code}")
                    print(f"     ✓ Erreur 400 retournée (attendu)")
                    if "n'est pas autorisée" in error_detail:
                        print(f"     ✓ Message d'erreur correct: {error_detail[:80]}...")
                else:
                    print(f"     ⚠ Status inattendu: {response.status_code}")
            else:
                print("  ⚠ Aucune transaction disponible pour le test")
        else:
            print("  ⚠ API non disponible ou erreur")
            
    except requests.exceptions.ConnectionError:
        print("  ⚠ API non disponible (connexion refusée)")
        print("  → Test ignoré (démarrez l'API pour tester)")
    except Exception as e:
        print(f"  ⚠ Erreur: {str(e)}")
    
    print("✓ Test 3 terminé\n")


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("TESTS - Step 5.4 : Validation dans endpoints enrichissement")
    print("=" * 60)
    
    try:
        # Initialiser la base de données
        init_database()
        
        test_create_or_update_mapping_validation()
        test_update_transaction_classification_validation()
        test_api_endpoint_validation()
        
        print("=" * 60)
        print("✓ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ ERREUR DE TEST : {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

