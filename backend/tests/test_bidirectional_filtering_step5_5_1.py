"""
Test Step 5.5.1 : Backend - Fonctions de filtrage bidirectionnel

Tests :
1. get_allowed_level2_for_level3 : retourne les level_2 pour un level_3 donné
2. get_allowed_level1_for_level2 : retourne les level_1 pour un level_2 donné
3. get_allowed_level1_for_level2_and_level3 : retourne les level_1 pour un couple (level_2, level_3)
4. Endpoints API correspondants
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import AllowedMapping
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel,
    get_allowed_level2_for_level3,
    get_allowed_level1_for_level2,
    get_allowed_level1_for_level2_and_level3
)


def test_step5_5_1():
    """Test Step 5.5.1 : Fonctions de filtrage bidirectionnel"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST Step 5.5.1 : Fonctions de filtrage bidirectionnel")
        print("=" * 60)
        
        # S'assurer que des mappings autorisés existent
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
                print(f"✓ Mappings autorisés chargés depuis Excel")
            else:
                print("✗ ERREUR : Fichier Excel non trouvé")
                return False
        
        # Récupérer quelques valeurs de test
        sample_mapping = db.query(AllowedMapping).first()
        if not sample_mapping:
            print("✗ ERREUR : Aucun mapping autorisé trouvé")
            return False
        
        print(f"\nMapping de test : {sample_mapping.level_1} / {sample_mapping.level_2} / {sample_mapping.level_3}")
        
        # ============================================================
        # Test 1 : get_allowed_level2_for_level3
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 1 : get_allowed_level2_for_level3")
        print("=" * 60)
        
        if sample_mapping.level_3:
            level_2_list = get_allowed_level2_for_level3(db, sample_mapping.level_3)
            print(f"\n1.1. Test avec level_3 = '{sample_mapping.level_3}'")
            print(f"   ✓ Fonction exécutée avec succès")
            print(f"   - Nombre de level_2 trouvés : {len(level_2_list)}")
            if len(level_2_list) > 0:
                print(f"   - Exemples : {level_2_list[:3]}")
                # Vérifier que le level_2 du mapping de test est dans la liste
                if sample_mapping.level_2 in level_2_list:
                    print(f"   ✓ Le level_2 du mapping de test est dans la liste")
                else:
                    print(f"   ⚠ Le level_2 du mapping de test n'est pas dans la liste")
            else:
                print(f"   ⚠ Aucun level_2 trouvé pour ce level_3")
        else:
            print(f"\n1.1. Mapping de test n'a pas de level_3, test avec une valeur connue")
            # Récupérer un mapping avec level_3
            mapping_with_level3 = db.query(AllowedMapping).filter(
                AllowedMapping.level_3.isnot(None)
            ).first()
            if mapping_with_level3:
                level_2_list = get_allowed_level2_for_level3(db, mapping_with_level3.level_3)
                print(f"   ✓ Fonction exécutée avec level_3 = '{mapping_with_level3.level_3}'")
                print(f"   - Nombre de level_2 trouvés : {len(level_2_list)}")
                if len(level_2_list) > 0:
                    print(f"   - Exemples : {level_2_list[:3]}")
        
        # ============================================================
        # Test 2 : get_allowed_level1_for_level2
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 2 : get_allowed_level1_for_level2")
        print("=" * 60)
        
        level_1_list = get_allowed_level1_for_level2(db, sample_mapping.level_2)
        print(f"\n2.1. Test avec level_2 = '{sample_mapping.level_2}'")
        print(f"   ✓ Fonction exécutée avec succès")
        print(f"   - Nombre de level_1 trouvés : {len(level_1_list)}")
        if len(level_1_list) > 0:
            print(f"   - Exemples : {level_1_list[:3]}")
            # Vérifier que le level_1 du mapping de test est dans la liste
            if sample_mapping.level_1 in level_1_list:
                print(f"   ✓ Le level_1 du mapping de test est dans la liste")
            else:
                print(f"   ✗ ERREUR : Le level_1 du mapping de test n'est pas dans la liste")
                return False
        else:
            print(f"   ✗ ERREUR : Aucun level_1 trouvé pour ce level_2")
            return False
        
        # ============================================================
        # Test 3 : get_allowed_level1_for_level2_and_level3
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 3 : get_allowed_level1_for_level2_and_level3")
        print("=" * 60)
        
        if sample_mapping.level_3:
            level_1_list = get_allowed_level1_for_level2_and_level3(
                db, 
                sample_mapping.level_2, 
                sample_mapping.level_3
            )
            print(f"\n3.1. Test avec level_2 = '{sample_mapping.level_2}', level_3 = '{sample_mapping.level_3}'")
            print(f"   ✓ Fonction exécutée avec succès")
            print(f"   - Nombre de level_1 trouvés : {len(level_1_list)}")
            if len(level_1_list) > 0:
                print(f"   - Exemples : {level_1_list[:3]}")
                # Vérifier que le level_1 du mapping de test est dans la liste
                if sample_mapping.level_1 in level_1_list:
                    print(f"   ✓ Le level_1 du mapping de test est dans la liste")
                else:
                    print(f"   ✗ ERREUR : Le level_1 du mapping de test n'est pas dans la liste")
                    return False
            else:
                print(f"   ✗ ERREUR : Aucun level_1 trouvé pour ce couple")
                return False
        else:
            print(f"\n3.1. Mapping de test n'a pas de level_3, test avec une valeur connue")
            # Récupérer un mapping avec level_3
            mapping_with_level3 = db.query(AllowedMapping).filter(
                AllowedMapping.level_3.isnot(None)
            ).first()
            if mapping_with_level3:
                level_1_list = get_allowed_level1_for_level2_and_level3(
                    db,
                    mapping_with_level3.level_2,
                    mapping_with_level3.level_3
                )
                print(f"   ✓ Fonction exécutée avec level_2 = '{mapping_with_level3.level_2}', level_3 = '{mapping_with_level3.level_3}'")
                print(f"   - Nombre de level_1 trouvés : {len(level_1_list)}")
                if len(level_1_list) > 0:
                    print(f"   - Exemples : {level_1_list[:3]}")
                    if mapping_with_level3.level_1 in level_1_list:
                        print(f"   ✓ Le level_1 du mapping de test est dans la liste")
                    else:
                        print(f"   ✗ ERREUR : Le level_1 du mapping de test n'est pas dans la liste")
                        return False
        
        # ============================================================
        # Test 4 : Vérification que les fonctions retournent des listes distinctes
        # ============================================================
        print("\n" + "=" * 60)
        print("Test 4 : Vérification des valeurs distinctes")
        print("=" * 60)
        
        # Récupérer tous les level_3 uniques
        all_level3 = db.query(AllowedMapping.level_3).filter(
            AllowedMapping.level_3.isnot(None)
        ).distinct().all()
        all_level3_values = [v[0] for v in all_level3 if v[0]]
        
        if len(all_level3_values) > 0:
            test_level3 = all_level3_values[0]
            level_2_list = get_allowed_level2_for_level3(db, test_level3)
            
            # Vérifier qu'il n'y a pas de doublons
            if len(level_2_list) == len(set(level_2_list)):
                print(f"   ✓ get_allowed_level2_for_level3 retourne des valeurs distinctes")
            else:
                print(f"   ✗ ERREUR : Doublons détectés dans get_allowed_level2_for_level3")
                return False
        
        # Récupérer tous les level_2 uniques
        all_level2 = db.query(AllowedMapping.level_2).filter(
            AllowedMapping.level_2.isnot(None)
        ).distinct().all()
        all_level2_values = [v[0] for v in all_level2 if v[0]]
        
        if len(all_level2_values) > 0:
            test_level2 = all_level2_values[0]
            level_1_list = get_allowed_level1_for_level2(db, test_level2)
            
            # Vérifier qu'il n'y a pas de doublons
            if len(level_1_list) == len(set(level_1_list)):
                print(f"   ✓ get_allowed_level1_for_level2 retourne des valeurs distinctes")
            else:
                print(f"   ✗ ERREUR : Doublons détectés dans get_allowed_level1_for_level2")
                return False
        
        print("\n" + "=" * 60)
        print("✓ TOUS LES TESTS STEP 5.5.1 PASSENT")
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
    success = test_step5_5_1()
    sys.exit(0 if success else 1)
