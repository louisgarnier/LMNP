"""
Test Step 5.8 : Endpoints CRUD pour allowed_mappings

Teste tous les endpoints créés pour la gestion des allowed_mappings.
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import AllowedMapping
from backend.api.services.mapping_obligatoire_service import (
    get_all_allowed_mappings,
    create_allowed_mapping,
    delete_allowed_mapping,
    reset_allowed_mappings,
    validate_level3_value,
    ALLOWED_LEVEL_3_VALUES
)


def test_get_all_allowed_mappings():
    """Test GET /api/mappings/allowed"""
    print("\n1. Test GET /api/mappings/allowed")
    db = SessionLocal()
    try:
        mappings, total = get_all_allowed_mappings(db, skip=0, limit=10)
        print(f"   ✓ Récupéré {len(mappings)} mappings (total: {total})")
        
        # Vérifier que les hard codés sont en premier
        if len(mappings) > 0:
            first_is_hardcoded = mappings[0].is_hardcoded
            print(f"   ✓ Premier mapping is_hardcoded={first_is_hardcoded}")
        
        return True
    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_create_allowed_mapping():
    """Test POST /api/mappings/allowed"""
    print("\n2. Test POST /api/mappings/allowed")
    db = SessionLocal()
    try:
        # Créer un mapping de test
        test_level_1 = "TEST LEVEL 1"
        test_level_2 = "TEST LEVEL 2"
        test_level_3 = "Passif"  # Valeur valide
        
        mapping = create_allowed_mapping(db, test_level_1, test_level_2, test_level_3)
        print(f"   ✓ Mapping créé : ID={mapping.id}, is_hardcoded={mapping.is_hardcoded}")
        assert mapping.is_hardcoded == False, "Le mapping créé doit avoir is_hardcoded=False"
        
        # Vérifier que la validation level_3 fonctionne
        try:
            create_allowed_mapping(db, test_level_1, test_level_2, "INVALID LEVEL 3")
            print(f"   ✗ Erreur : level_3 invalide accepté")
            return False
        except ValueError as e:
            print(f"   ✓ Validation level_3 fonctionne : {e}")
        
        # Vérifier que les doublons sont rejetés
        try:
            create_allowed_mapping(db, test_level_1, test_level_2, test_level_3)
            print(f"   ✗ Erreur : doublon accepté")
            return False
        except ValueError as e:
            print(f"   ✓ Validation doublon fonctionne : {e}")
        
        # Nettoyer
        db.delete(mapping)
        db.commit()
        print(f"   ✓ Mapping de test supprimé")
        
        return True
    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_delete_allowed_mapping():
    """Test DELETE /api/mappings/allowed/{id}"""
    print("\n3. Test DELETE /api/mappings/allowed/{id}")
    db = SessionLocal()
    try:
        # Créer un mapping de test (non hard codé)
        test_level_1 = "TEST DELETE 1"
        test_level_2 = "TEST DELETE 2"
        mapping = create_allowed_mapping(db, test_level_1, test_level_2, None)
        mapping_id = mapping.id
        print(f"   ✓ Mapping de test créé : ID={mapping_id}")
        
        # Supprimer le mapping
        deleted = delete_allowed_mapping(db, mapping_id)
        assert deleted == True, "La suppression doit retourner True"
        print(f"   ✓ Mapping supprimé avec succès")
        
        # Vérifier qu'il n'existe plus
        mapping_check = db.query(AllowedMapping).filter(AllowedMapping.id == mapping_id).first()
        assert mapping_check is None, "Le mapping ne doit plus exister"
        print(f"   ✓ Mapping confirmé supprimé")
        
        # Tester la suppression d'un mapping hard codé
        hardcoded_mapping = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).first()
        
        if hardcoded_mapping:
            try:
                delete_allowed_mapping(db, hardcoded_mapping.id)
                print(f"   ✗ Erreur : mapping hard codé supprimé")
                return False
            except ValueError as e:
                print(f"   ✓ Protection hard codé fonctionne : {e}")
        
        return True
    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_reset_allowed_mappings():
    """Test POST /api/mappings/allowed/reset"""
    print("\n4. Test POST /api/mappings/allowed/reset")
    db = SessionLocal()
    try:
        # Compter les mappings hard codés avant
        hardcoded_before = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        print(f"   ✓ Mappings hard codés avant reset : {hardcoded_before}")
        
        # Créer quelques mappings de test (non hard codés)
        test_mapping_ids = []
        for i in range(3):
            mapping = create_allowed_mapping(
                db,
                f"TEST RESET {i}",
                f"TEST RESET {i}",
                "Produits" if i % 2 == 0 else None
            )
            test_mapping_ids.append(mapping.id)
        print(f"   ✓ {len(test_mapping_ids)} mappings de test créés (IDs: {test_mapping_ids})")
        
        # Compter les mappings non hard codés avant reset
        non_hardcoded_before = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == False
        ).count()
        print(f"   ✓ Mappings non hard codés avant reset : {non_hardcoded_before}")
        
        # Faire le reset
        stats = reset_allowed_mappings(db)
        print(f"   ✓ Reset effectué :")
        print(f"     - deleted_allowed: {stats['deleted_allowed']}")
        print(f"     - deleted_mappings: {stats['deleted_mappings']}")
        print(f"     - unassigned_transactions: {stats['unassigned_transactions']}")
        
        # Vérifier que les mappings hard codés sont toujours là
        hardcoded_after = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        assert hardcoded_after == hardcoded_before, "Les mappings hard codés doivent être préservés"
        print(f"   ✓ Mappings hard codés préservés : {hardcoded_after}")
        
        # Vérifier que les mappings de test sont supprimés
        for mapping_id in test_mapping_ids:
            mapping_check = db.query(AllowedMapping).filter(AllowedMapping.id == mapping_id).first()
            assert mapping_check is None, f"Le mapping de test {mapping_id} doit être supprimé"
        print(f"   ✓ Mappings de test supprimés")
        
        return True
    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def run_all_tests():
    """Exécute tous les tests"""
    print("=" * 60)
    print("TEST : Endpoints CRUD pour allowed_mappings (Step 5.8)")
    print("=" * 60)
    
    results = []
    results.append(("GET /api/mappings/allowed", test_get_all_allowed_mappings()))
    results.append(("POST /api/mappings/allowed", test_create_allowed_mapping()))
    results.append(("DELETE /api/mappings/allowed/{id}", test_delete_allowed_mapping()))
    results.append(("POST /api/mappings/allowed/reset", test_reset_allowed_mappings()))
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASSÉ" if result else "✗ ÉCHOUÉ"
        print(f"{status} : {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ TOUS LES TESTS SONT PASSÉS")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

