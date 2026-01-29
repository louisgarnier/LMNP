"""
Test Step 3 : Fonction de validation property_id

Ce script vérifie que :
1. La fonction validate_property_id fonctionne correctement
2. Elle valide un property_id existant
3. Elle lève une exception pour un property_id inexistant
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property
from backend.api.utils.validation import validate_property_id
from fastapi import HTTPException

print("=" * 60)
print("TEST STEP 3 : Fonction de validation property_id")
print("=" * 60)
print()

db = SessionLocal()

try:
    # 1. Lister les propriétés disponibles
    properties = db.query(Property).all()
    print("📋 Propriétés disponibles:")
    for prop in properties:
        print(f"   - ID={prop.id}: {prop.name}")
    
    if not properties:
        print("   ⚠️  Aucune propriété trouvée")
        print("   Créez d'abord une propriété pour tester")
        sys.exit(1)
    
    valid_property_id = properties[0].id
    invalid_property_id = 99999
    
    print(f"\n✅ Test 1: Validation d'un property_id valide (ID={valid_property_id})")
    try:
        result = validate_property_id(db, valid_property_id, "Test")
        print(f"   ✅ Validation réussie: {result}")
    except HTTPException as e:
        print(f"   ❌ Erreur inattendue: {e.detail}")
    
    print(f"\n✅ Test 2: Validation d'un property_id invalide (ID={invalid_property_id})")
    try:
        validate_property_id(db, invalid_property_id, "Test")
        print(f"   ❌ Erreur: La fonction devrait lever une exception mais ne l'a pas fait")
    except HTTPException as e:
        if e.status_code == 400:
            print(f"   ✅ Exception levée correctement: {e.detail}")
        else:
            print(f"   ❌ Mauvais code d'erreur: {e.status_code} (attendu: 400)")
    
    print("\n" + "=" * 60)
    print("✅ Test Step 3 terminé")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
