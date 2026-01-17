"""
Test script for Step 9.4: Bilan API endpoints.

This script tests:
1. GET /api/bilan/mappings - Liste des mappings
2. POST /api/bilan/mappings - Créer un mapping
3. GET /api/bilan/mappings/{id} - Détails d'un mapping
4. PUT /api/bilan/mappings/{id} - Mettre à jour un mapping
5. DELETE /api/bilan/mappings/{id} - Supprimer un mapping
6. POST /api/bilan/calculate - Générer le bilan
7. GET /api/bilan - Récupérer les données
8. GET /api/bilan/config - Récupérer la configuration
9. PUT /api/bilan/config - Mettre à jour la configuration

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import SessionLocal, init_database
from backend.database.models import BilanMapping, BilanConfig

# Initialize database
init_database()

# Create test client
client = TestClient(app)


def test_get_mappings():
    """Test GET /api/bilan/mappings."""
    print("📋 Testing GET /api/bilan/mappings...")
    
    try:
        response = client.get("/api/bilan/mappings")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"   ✅ GET /api/bilan/mappings - {data['total']} mapping(s) found")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_mapping():
    """Test POST /api/bilan/mappings."""
    print("\n📋 Testing POST /api/bilan/mappings...")
    
    try:
        mapping_data = {
            "category_name": "Test Category",
            "type": "ACTIF",
            "sub_category": "Test Sub Category",
            "level_1_values": json.dumps(["TEST_LEVEL_1"]),
            "is_special": False
        }
        
        response = client.post("/api/bilan/mappings", json=mapping_data)
        assert response.status_code == 201
        data = response.json()
        assert data["category_name"] == "Test Category"
        assert data["type"] == "ACTIF"
        mapping_id = data["id"]
        print(f"   ✅ POST /api/bilan/mappings - Mapping created with id={mapping_id}")
        
        # Cleanup
        db = SessionLocal()
        try:
            mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
            if mapping:
                db.delete(mapping)
                db.commit()
        finally:
            db.close()
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_mapping_by_id():
    """Test GET /api/bilan/mappings/{id}."""
    print("\n📋 Testing GET /api/bilan/mappings/{id}...")
    
    try:
        # Créer un mapping de test
        db = SessionLocal()
        test_mapping = BilanMapping(
            category_name="Test Get Mapping",
            type="ACTIF",
            sub_category="Test Sub Category",
            level_1_values=json.dumps(["TEST"]),
            is_special=False
        )
        db.add(test_mapping)
        db.commit()
        db.refresh(test_mapping)
        mapping_id = test_mapping.id
        db.close()
        
        # Tester GET
        response = client.get(f"/api/bilan/mappings/{mapping_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mapping_id
        assert data["category_name"] == "Test Get Mapping"
        print(f"   ✅ GET /api/bilan/mappings/{mapping_id} - Mapping retrieved")
        
        # Cleanup
        db = SessionLocal()
        try:
            mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
            if mapping:
                db.delete(mapping)
                db.commit()
        finally:
            db.close()
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_mapping():
    """Test PUT /api/bilan/mappings/{id}."""
    print("\n📋 Testing PUT /api/bilan/mappings/{id}...")
    
    try:
        # Créer un mapping de test
        db = SessionLocal()
        test_mapping = BilanMapping(
            category_name="Test Update Mapping",
            type="ACTIF",
            sub_category="Test Sub Category",
            level_1_values=json.dumps(["TEST"]),
            is_special=False
        )
        db.add(test_mapping)
        db.commit()
        db.refresh(test_mapping)
        mapping_id = test_mapping.id
        db.close()
        
        # Tester PUT
        update_data = {
            "category_name": "Test Update Mapping (modifié)"
        }
        response = client.put(f"/api/bilan/mappings/{mapping_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["category_name"] == "Test Update Mapping (modifié)"
        print(f"   ✅ PUT /api/bilan/mappings/{mapping_id} - Mapping updated")
        
        # Cleanup
        db = SessionLocal()
        try:
            mapping = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
            if mapping:
                db.delete(mapping)
                db.commit()
        finally:
            db.close()
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_mapping():
    """Test DELETE /api/bilan/mappings/{id}."""
    print("\n📋 Testing DELETE /api/bilan/mappings/{id}...")
    
    try:
        # Créer un mapping de test
        db = SessionLocal()
        test_mapping = BilanMapping(
            category_name="Test Delete Mapping",
            type="ACTIF",
            sub_category="Test Sub Category",
            level_1_values=json.dumps(["TEST"]),
            is_special=False
        )
        db.add(test_mapping)
        db.commit()
        db.refresh(test_mapping)
        mapping_id = test_mapping.id
        db.close()
        
        # Tester DELETE
        response = client.delete(f"/api/bilan/mappings/{mapping_id}")
        assert response.status_code == 204
        print(f"   ✅ DELETE /api/bilan/mappings/{mapping_id} - Mapping deleted")
        
        # Vérifier que le mapping n'existe plus
        response = client.get(f"/api/bilan/mappings/{mapping_id}")
        assert response.status_code == 404
        print(f"   ✅ Mapping {mapping_id} confirmed deleted")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculate_bilan():
    """Test POST /api/bilan/calculate."""
    print("\n📋 Testing POST /api/bilan/calculate...")
    
    try:
        request_data = {
            "year": 2024
        }
        
        response = client.post("/api/bilan/calculate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "year" in data
        assert "types" in data
        assert "actif_total" in data
        assert "passif_total" in data
        assert "difference" in data
        assert "difference_percent" in data
        print(f"   ✅ POST /api/bilan/calculate - Bilan calculated for year {data['year']}")
        print(f"      - ACTIF total: {data['actif_total']:.2f} €")
        print(f"      - PASSIF total: {data['passif_total']:.2f} €")
        print(f"      - Difference: {data['difference']:.2f} € ({data['difference_percent']:.2f}%)")
        print(f"      - Types: {len(data['types'])}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_bilan():
    """Test GET /api/bilan."""
    print("\n📋 Testing GET /api/bilan...")
    
    try:
        response = client.get("/api/bilan")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"   ✅ GET /api/bilan - {data['total']} data item(s) found")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_config():
    """Test GET /api/bilan/config."""
    print("\n📋 Testing GET /api/bilan/config...")
    
    try:
        response = client.get("/api/bilan/config")
        assert response.status_code == 200
        data = response.json()
        assert "level_3_values" in data
        print(f"   ✅ GET /api/bilan/config - Config retrieved")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_config():
    """Test PUT /api/bilan/config."""
    print("\n📋 Testing PUT /api/bilan/config...")
    
    try:
        update_data = {
            "level_3_values": json.dumps(["VALEUR1", "VALEUR2"])
        }
        
        response = client.put("/api/bilan/config", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["level_3_values"] == json.dumps(["VALEUR1", "VALEUR2"])
        print(f"   ✅ PUT /api/bilan/config - Config updated")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Bilan API Endpoints (Step 9.4)")
    print("=" * 60)
    
    results = []
    
    results.append(("GET /api/bilan/mappings", test_get_mappings()))
    results.append(("POST /api/bilan/mappings", test_create_mapping()))
    results.append(("GET /api/bilan/mappings/{id}", test_get_mapping_by_id()))
    results.append(("PUT /api/bilan/mappings/{id}", test_update_mapping()))
    results.append(("DELETE /api/bilan/mappings/{id}", test_delete_mapping()))
    results.append(("POST /api/bilan/calculate", test_calculate_bilan()))
    results.append(("GET /api/bilan", test_get_bilan()))
    results.append(("GET /api/bilan/config", test_get_config()))
    results.append(("PUT /api/bilan/config", test_update_config()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
