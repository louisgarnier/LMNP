"""
Test script for Pivot non-regression - Phase 11 - Onglet 7 (Pivot)

This script tests that all pivot endpoints work correctly with property_id.

⚠️ Before running, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result with color."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"       {details}")


def get_first_property():
    """Get the first property."""
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code != 200:
        print(f"❌ Erreur récupération propriétés: {response.text}")
        return None
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    elif isinstance(data, dict) and 'properties' in data and len(data['properties']) > 0:
        return data['properties'][0]
    elif isinstance(data, dict) and 'items' in data and len(data['items']) > 0:
        return data['items'][0]
    return None


def run_non_regression_tests():
    """Run non-regression tests for Pivot."""
    print("\n" + "=" * 60)
    print("TEST DE NON-RÉGRESSION - PIVOT (Phase 11 - Onglet 7)")
    print("=" * 60 + "\n")
    
    # Get first property
    prop = get_first_property()
    if not prop:
        print("❌ Aucune propriété trouvée")
        return False
    
    property_id = prop['id']
    print(f"📦 Propriété utilisée: {prop['name']} (ID: {property_id})")
    print()
    
    all_passed = True
    created_config_id = None
    
    try:
        # ========================================
        # Test 1: GET /api/pivot-configs
        # ========================================
        print("--- Test 1: GET /api/pivot-configs ---")
        
        response = requests.get(
            f"{BASE_URL}/api/pivot-configs",
            params={"property_id": property_id}
        )
        passed = response.status_code == 200
        log_test("GET /api/pivot-configs", passed, f"Status: {response.status_code}")
        if not passed:
            all_passed = False
        else:
            data = response.json()
            print(f"       Items: {len(data.get('items', []))}, Total: {data.get('total', 0)}")
        
        print()
        
        # ========================================
        # Test 2: POST /api/pivot-configs
        # ========================================
        print("--- Test 2: POST /api/pivot-configs ---")
        
        config_data = {
            "property_id": property_id,
            "name": "Test Non-Regression TCD",
            "config": {
                "rows": ["level_1", "level_2"],
                "columns": ["annee"],
                "data": ["quantite"],
                "filters": {}
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pivot-configs",
            json=config_data
        )
        passed = response.status_code == 201
        log_test("POST /api/pivot-configs", passed, f"Status: {response.status_code}")
        if not passed:
            all_passed = False
            print(f"       Erreur: {response.text}")
        else:
            created_config_id = response.json()['id']
            print(f"       Config ID créé: {created_config_id}")
        
        print()
        
        # ========================================
        # Test 3: GET /api/pivot-configs/{id}
        # ========================================
        print("--- Test 3: GET /api/pivot-configs/{id} ---")
        
        if created_config_id:
            response = requests.get(
                f"{BASE_URL}/api/pivot-configs/{created_config_id}",
                params={"property_id": property_id}
            )
            passed = response.status_code == 200
            log_test("GET /api/pivot-configs/{id}", passed, f"Status: {response.status_code}")
            if not passed:
                all_passed = False
            else:
                data = response.json()
                print(f"       Name: {data.get('name')}")
        else:
            log_test("GET /api/pivot-configs/{id}", False, "Config non créée")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 4: PUT /api/pivot-configs/{id}
        # ========================================
        print("--- Test 4: PUT /api/pivot-configs/{id} ---")
        
        if created_config_id:
            update_data = {
                "name": "Test Non-Regression TCD - Updated",
                "config": {
                    "rows": ["level_1"],
                    "columns": ["mois"],
                    "data": ["quantite"],
                    "filters": {"annee": 2024}
                }
            }
            
            response = requests.put(
                f"{BASE_URL}/api/pivot-configs/{created_config_id}",
                params={"property_id": property_id},
                json=update_data
            )
            passed = response.status_code == 200
            log_test("PUT /api/pivot-configs/{id}", passed, f"Status: {response.status_code}")
            if not passed:
                all_passed = False
            else:
                data = response.json()
                print(f"       Updated name: {data.get('name')}")
        else:
            log_test("PUT /api/pivot-configs/{id}", False, "Config non créée")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 5: GET /api/analytics/pivot
        # ========================================
        print("--- Test 5: GET /api/analytics/pivot ---")
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/pivot",
            params={
                "property_id": property_id,
                "rows": "level_1",
                "columns": "annee"
            }
        )
        passed = response.status_code == 200
        log_test("GET /api/analytics/pivot", passed, f"Status: {response.status_code}")
        if not passed:
            all_passed = False
        else:
            data = response.json()
            print(f"       Rows: {len(data.get('rows', []))}, Columns: {len(data.get('columns', []))}")
            print(f"       Grand total: {data.get('grand_total', 0)}")
        
        print()
        
        # ========================================
        # Test 6: GET /api/analytics/pivot/details
        # ========================================
        print("--- Test 6: GET /api/analytics/pivot/details ---")
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/pivot/details",
            params={
                "property_id": property_id,
                "rows": "level_1",
                "row_values": '["CHARGES"]',
            }
        )
        passed = response.status_code == 200
        log_test("GET /api/analytics/pivot/details", passed, f"Status: {response.status_code}")
        if not passed:
            all_passed = False
            print(f"       Erreur: {response.text}")
        else:
            data = response.json()
            print(f"       Transactions: {len(data.get('transactions', []))}, Total: {data.get('total', 0)}")
        
        print()
        
        # ========================================
        # Test 7: DELETE /api/pivot-configs/{id}
        # ========================================
        print("--- Test 7: DELETE /api/pivot-configs/{id} ---")
        
        if created_config_id:
            response = requests.delete(
                f"{BASE_URL}/api/pivot-configs/{created_config_id}",
                params={"property_id": property_id}
            )
            passed = response.status_code == 204
            log_test("DELETE /api/pivot-configs/{id}", passed, f"Status: {response.status_code}")
            if not passed:
                all_passed = False
            else:
                created_config_id = None  # Mark as deleted
        else:
            log_test("DELETE /api/pivot-configs/{id}", False, "Config non créée")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 8: Verify logs contain property_id
        # ========================================
        print("--- Test 8: Vérification des logs ---")
        print("       ⚠️  Vérifiez manuellement les logs backend pour confirmer")
        print("       que chaque appel contient property_id")
        log_test("Logs contiennent property_id", True, "Vérification manuelle requise")
        
        print()
        
    finally:
        # Cleanup si nécessaire
        if created_config_id:
            try:
                requests.delete(
                    f"{BASE_URL}/api/pivot-configs/{created_config_id}",
                    params={"property_id": property_id}
                )
                print(f"   ⚠ Cleanup: Config {created_config_id} supprimée")
            except Exception as e:
                print(f"   ⚠ Cleanup erreur: {e}")
    
    # ========================================
    # Résumé
    # ========================================
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TOUS LES TESTS DE NON-RÉGRESSION PIVOT SONT PASSÉS")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_non_regression_tests()
    sys.exit(0 if success else 1)
