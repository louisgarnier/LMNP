"""
Test script for Pivot isolation - Phase 11 - Onglet 7 (Pivot)

This script tests that pivot configs are properly isolated by property_id.

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


def get_properties():
    """Get all properties."""
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code != 200:
        print(f"❌ Erreur récupération propriétés: {response.text}")
        return []
    data = response.json()
    # Handle both list and dict response formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'properties' in data:
        return data['properties']
    elif isinstance(data, dict) and 'items' in data:
        return data['items']
    return []


def create_pivot_config(property_id: int, name: str, config: dict):
    """Create a pivot config for a property."""
    data = {
        "property_id": property_id,
        "name": name,
        "config": config
    }
    response = requests.post(
        f"{BASE_URL}/api/pivot-configs",
        json=data
    )
    return response


def get_pivot_configs(property_id: int):
    """Get all pivot configs for a property."""
    response = requests.get(
        f"{BASE_URL}/api/pivot-configs",
        params={"property_id": property_id}
    )
    return response


def get_pivot_config(property_id: int, config_id: int):
    """Get a specific pivot config."""
    response = requests.get(
        f"{BASE_URL}/api/pivot-configs/{config_id}",
        params={"property_id": property_id}
    )
    return response


def update_pivot_config(property_id: int, config_id: int, data: dict):
    """Update a pivot config."""
    response = requests.put(
        f"{BASE_URL}/api/pivot-configs/{config_id}",
        params={"property_id": property_id},
        json=data
    )
    return response


def delete_pivot_config(property_id: int, config_id: int):
    """Delete a pivot config."""
    response = requests.delete(
        f"{BASE_URL}/api/pivot-configs/{config_id}",
        params={"property_id": property_id}
    )
    return response


def get_pivot_data(property_id: int, rows: str = None, columns: str = None):
    """Get pivot data for a property."""
    params = {"property_id": property_id}
    if rows:
        params["rows"] = rows
    if columns:
        params["columns"] = columns
    response = requests.get(
        f"{BASE_URL}/api/analytics/pivot",
        params=params
    )
    return response


def run_isolation_tests():
    """Run isolation tests for Pivot."""
    print("\n" + "=" * 60)
    print("TEST D'ISOLATION - PIVOT (Phase 11 - Onglet 7)")
    print("=" * 60 + "\n")
    
    # Get properties
    properties = get_properties()
    if len(properties) < 2:
        print("❌ Il faut au moins 2 propriétés pour les tests d'isolation")
        print(f"   Propriétés trouvées: {len(properties)}")
        return False
    
    prop1 = properties[0]
    prop2 = properties[1]
    print(f"📦 Propriété 1: {prop1['name']} (ID: {prop1['id']})")
    print(f"📦 Propriété 2: {prop2['name']} (ID: {prop2['id']})")
    print()
    
    all_passed = True
    created_configs = []
    
    try:
        # ========================================
        # Test 1: Créer des configs pour prop1
        # ========================================
        print("--- Test 1: Création de pivot configs pour prop1 ---")
        
        config1_data = {
            "rows": ["level_1", "level_2"],
            "columns": ["annee"],
            "data": ["quantite"],
            "filters": {}
        }
        
        response = create_pivot_config(prop1['id'], f"Test TCD 1 - {prop1['name']}", config1_data)
        if response.status_code == 201:
            config1 = response.json()
            created_configs.append((prop1['id'], config1['id']))
            log_test("Création config 1 pour prop1", True, f"ID: {config1['id']}")
        else:
            log_test("Création config 1 pour prop1", False, f"Status: {response.status_code}")
            all_passed = False
        
        response = create_pivot_config(prop1['id'], f"Test TCD 2 - {prop1['name']}", config1_data)
        if response.status_code == 201:
            config2 = response.json()
            created_configs.append((prop1['id'], config2['id']))
            log_test("Création config 2 pour prop1", True, f"ID: {config2['id']}")
        else:
            log_test("Création config 2 pour prop1", False, f"Status: {response.status_code}")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 2: Créer des configs pour prop2
        # ========================================
        print("--- Test 2: Création de pivot configs pour prop2 ---")
        
        config2_data = {
            "rows": ["level_1"],
            "columns": ["mois"],
            "data": ["quantite"],
            "filters": {}
        }
        
        response = create_pivot_config(prop2['id'], f"Test TCD - {prop2['name']}", config2_data)
        if response.status_code == 201:
            config3 = response.json()
            created_configs.append((prop2['id'], config3['id']))
            log_test("Création config pour prop2", True, f"ID: {config3['id']}")
        else:
            log_test("Création config pour prop2", False, f"Status: {response.status_code}")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 3: Vérifier l'isolation - GET list
        # ========================================
        print("--- Test 3: Vérifier l'isolation des listes ---")
        
        response = get_pivot_configs(prop1['id'])
        if response.status_code == 200:
            data = response.json()
            # Filtrer pour ne compter que les configs créées dans ce test
            test_configs = [c for c in data['items'] if 'Test TCD' in c['name']]
            passed = len(test_configs) >= 2
            log_test("GET configs prop1", passed, f"Configs de test trouvées: {len(test_configs)}")
            if not passed:
                all_passed = False
        else:
            log_test("GET configs prop1", False, f"Status: {response.status_code}")
            all_passed = False
        
        response = get_pivot_configs(prop2['id'])
        if response.status_code == 200:
            data = response.json()
            test_configs = [c for c in data['items'] if 'Test TCD' in c['name']]
            passed = len(test_configs) >= 1
            log_test("GET configs prop2", passed, f"Configs de test trouvées: {len(test_configs)}")
            if not passed:
                all_passed = False
        else:
            log_test("GET configs prop2", False, f"Status: {response.status_code}")
            all_passed = False
        
        print()
        
        # ========================================
        # Test 4: Vérifier l'isolation - GET by ID
        # ========================================
        print("--- Test 4: Vérifier qu'on ne peut pas accéder aux configs d'une autre propriété ---")
        
        if created_configs:
            # Essayer d'accéder à une config de prop1 avec prop2
            prop1_config_id = created_configs[0][1]
            response = get_pivot_config(prop2['id'], prop1_config_id)
            passed = response.status_code == 404
            log_test("Accès config prop1 depuis prop2 bloqué", passed, 
                    f"Status attendu: 404, reçu: {response.status_code}")
            if not passed:
                all_passed = False
        
        print()
        
        # ========================================
        # Test 5: Vérifier l'isolation - UPDATE
        # ========================================
        print("--- Test 5: Vérifier qu'on ne peut pas modifier les configs d'une autre propriété ---")
        
        if len(created_configs) >= 2:
            prop1_config_id = created_configs[0][1]
            response = update_pivot_config(prop2['id'], prop1_config_id, {"name": "Hacked!"})
            passed = response.status_code == 404
            log_test("Modification config prop1 depuis prop2 bloquée", passed,
                    f"Status attendu: 404, reçu: {response.status_code}")
            if not passed:
                all_passed = False
        
        print()
        
        # ========================================
        # Test 6: Vérifier l'isolation - DELETE
        # ========================================
        print("--- Test 6: Vérifier qu'on ne peut pas supprimer les configs d'une autre propriété ---")
        
        if len(created_configs) >= 2:
            prop1_config_id = created_configs[0][1]
            response = delete_pivot_config(prop2['id'], prop1_config_id)
            passed = response.status_code == 404
            log_test("Suppression config prop1 depuis prop2 bloquée", passed,
                    f"Status attendu: 404, reçu: {response.status_code}")
            if not passed:
                all_passed = False
        
        print()
        
        # ========================================
        # Test 7: Vérifier l'isolation - Pivot Data
        # ========================================
        print("--- Test 7: Vérifier l'isolation des données pivot ---")
        
        response = get_pivot_data(prop1['id'], "level_1")
        if response.status_code == 200:
            log_test("GET pivot data pour prop1", True)
        else:
            log_test("GET pivot data pour prop1", False, f"Status: {response.status_code}")
            all_passed = False
        
        response = get_pivot_data(prop2['id'], "level_1")
        if response.status_code == 200:
            log_test("GET pivot data pour prop2", True)
        else:
            log_test("GET pivot data pour prop2", False, f"Status: {response.status_code}")
            all_passed = False
        
        print()
        
    finally:
        # ========================================
        # Cleanup
        # ========================================
        print("--- Cleanup: Suppression des configs de test ---")
        for prop_id, config_id in created_configs:
            try:
                response = delete_pivot_config(prop_id, config_id)
                if response.status_code == 204:
                    print(f"   ✓ Config {config_id} supprimée")
                else:
                    print(f"   ⚠ Config {config_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠ Erreur suppression config {config_id}: {e}")
    
    # ========================================
    # Résumé
    # ========================================
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TOUS LES TESTS D'ISOLATION PIVOT SONT PASSÉS")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_isolation_tests()
    sys.exit(0 if success else 1)
