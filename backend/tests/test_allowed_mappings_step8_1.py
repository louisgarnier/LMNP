"""
Test script for Step 8.1 - Allowed Mappings Service and API Endpoints.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_allowed_mappings_step8_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import AllowedMapping
from backend.api.services.mapping_default_service import (
    get_allowed_level1_values,
    get_allowed_level2_values,
    get_allowed_level3_values,
    validate_mapping
)


def test_service_functions():
    """Test les fonctions du service mapping_default_service."""
    print("=" * 60)
    print("Test des fonctions du service mapping_default_service")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Test 1: get_allowed_level1_values
        print("📋 Test 1: get_allowed_level1_values()")
        level1_values = get_allowed_level1_values(db)
        print(f"   ✅ Nombre de valeurs level_1: {len(level1_values)}")
        if level1_values:
            print(f"   ✅ Premières valeurs: {level1_values[:5]}")
        else:
            print("   ⚠️  Aucune valeur level_1 trouvée (table vide)")
        print()
        
        # Test 2: get_allowed_level2_values (si on a des level_1)
        if level1_values:
            print(f"📋 Test 2: get_allowed_level2_values(level_1='{level1_values[0]}')")
            level2_values = get_allowed_level2_values(db, level1_values[0])
            print(f"   ✅ Nombre de valeurs level_2 pour '{level1_values[0]}': {len(level2_values)}")
            if level2_values:
                print(f"   ✅ Premières valeurs: {level2_values[:5]}")
            print()
            
            # Test 3: get_allowed_level3_values (si on a des level_2)
            if level2_values:
                print(f"📋 Test 3: get_allowed_level3_values(level_1='{level1_values[0]}', level_2='{level2_values[0]}')")
                level3_values = get_allowed_level3_values(db, level1_values[0], level2_values[0])
                print(f"   ✅ Nombre de valeurs level_3 pour ('{level1_values[0]}', '{level2_values[0]}'): {len(level3_values)}")
                if level3_values:
                    print(f"   ✅ Premières valeurs: {level3_values[:5]}")
                print()
                
                # Test 4: validate_mapping
                print(f"📋 Test 4: validate_mapping(level_1='{level1_values[0]}', level_2='{level2_values[0]}', level_3={level3_values[0] if level3_values else None})")
                is_valid = validate_mapping(db, level1_values[0], level2_values[0], level3_values[0] if level3_values else None)
                print(f"   ✅ Mapping valide: {is_valid}")
                print()
                
                # Test 5: validate_mapping avec combinaison invalide
                print("📋 Test 5: validate_mapping avec combinaison invalide")
                is_valid_invalid = validate_mapping(db, "INVALID_LEVEL1", "INVALID_LEVEL2", "INVALID_LEVEL3")
                print(f"   ✅ Mapping invalide détecté: {not is_valid_invalid}")
                print()
        
        # Afficher le nombre total de mappings autorisés
        total_mappings = db.query(AllowedMapping).count()
        print(f"📊 Total de mappings autorisés en BDD: {total_mappings}")
        if total_mappings == 0:
            print("   ⚠️  La table est vide. Utilisez le script load_allowed_mappings_from_excel.py pour charger les données.")
        print()
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    print("=" * 60)
    print("✅ Tests terminés !")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_service_functions()
    sys.exit(0 if success else 1)

