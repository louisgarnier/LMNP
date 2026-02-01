"""
Test de non-régression du Compte de Résultat - Phase 11 bis 5.2

Ce script vérifie que toutes les fonctionnalités existantes fonctionnent après l'ajout de property_id.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def get_first_property():
    """Récupérer la première propriété disponible."""
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer les propriétés: {response.status_code}")
        return None
    data = response.json()
    if data.get('items') and len(data['items']) > 0:
        return data['items'][0]
    log_error("Aucune propriété trouvée")
    return None

def test_mappings_crud(property_id):
    """Tester les opérations CRUD sur les mappings."""
    log_info("=== Test CRUD Mappings ===")
    
    # CREATE
    mapping_data = {
        "category_name": f"Test NR {datetime.now().strftime('%H%M%S')}",
        "type": "Produits d'exploitation",
        "level_1_values": '["TEST_NR"]',
        "property_id": property_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/mappings", json=mapping_data)
    if response.status_code != 201:
        log_error(f"POST mapping échoué: {response.status_code} {response.text}")
        return False
    mapping = response.json()
    mapping_id = mapping['id']
    log_success(f"POST /api/compte-resultat/mappings - créé id={mapping_id}")
    
    # READ (list)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/mappings?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET mappings échoué: {response.status_code}")
        return False
    mappings_list = response.json()
    log_success(f"GET /api/compte-resultat/mappings - {mappings_list['total']} mappings")
    
    # UPDATE
    update_data = {"category_name": "Test NR Updated"}
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/mappings/{mapping_id}?property_id={property_id}",
        json=update_data
    )
    if response.status_code != 200:
        log_error(f"PUT mapping échoué: {response.status_code} {response.text}")
        return False
    updated = response.json()
    if updated['category_name'] != "Test NR Updated":
        log_error("Mise à jour du mapping non appliquée")
        return False
    log_success(f"PUT /api/compte-resultat/mappings/{mapping_id} - mis à jour")
    
    # DELETE
    response = requests.delete(f"{BASE_URL}/api/compte-resultat/mappings/{mapping_id}?property_id={property_id}")
    if response.status_code != 204:
        log_error(f"DELETE mapping échoué: {response.status_code}")
        return False
    log_success(f"DELETE /api/compte-resultat/mappings/{mapping_id} - supprimé")
    
    return True

def test_config_crud(property_id):
    """Tester les opérations sur la config."""
    log_info("=== Test Config ===")
    
    # GET config
    response = requests.get(f"{BASE_URL}/api/compte-resultat/config?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET config échoué: {response.status_code}")
        return False
    config = response.json()
    log_success(f"GET /api/compte-resultat/config - id={config['id']}")
    
    # PUT config
    update_data = {"level_3_values": '["TestNR"]'}
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/config?property_id={property_id}",
        json=update_data
    )
    if response.status_code != 200:
        log_error(f"PUT config échoué: {response.status_code} {response.text}")
        return False
    updated = response.json()
    log_success(f"PUT /api/compte-resultat/config - mis à jour")
    
    # Restaurer
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/config?property_id={property_id}",
        json={"level_3_values": '[]'}
    )
    
    return True

def test_overrides_crud(property_id):
    """Tester les opérations CRUD sur les overrides."""
    log_info("=== Test CRUD Overrides ===")
    
    test_year = 2099  # Année de test pour éviter les conflits
    
    # CREATE
    override_data = {
        "year": test_year,
        "override_value": 99999.99,
        "property_id": property_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/override", json=override_data)
    if response.status_code != 201:
        log_error(f"POST override échoué: {response.status_code} {response.text}")
        return False
    override = response.json()
    log_success(f"POST /api/compte-resultat/override - créé pour year={test_year}")
    
    # READ (list)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/override?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET overrides list échoué: {response.status_code}")
        return False
    overrides_list = response.json()
    log_success(f"GET /api/compte-resultat/override - {len(overrides_list)} overrides")
    
    # READ (single)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/override/{test_year}?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET override by year échoué: {response.status_code}")
        return False
    log_success(f"GET /api/compte-resultat/override/{test_year} - trouvé")
    
    # UPDATE (via POST - upsert)
    update_data = {
        "year": test_year,
        "override_value": 11111.11,
        "property_id": property_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/override", json=update_data)
    if response.status_code != 201:
        log_error(f"POST override (update) échoué: {response.status_code}")
        return False
    updated = response.json()
    if abs(updated['override_value'] - 11111.11) > 0.01:
        log_error("Mise à jour de l'override non appliquée")
        return False
    log_success(f"POST /api/compte-resultat/override (upsert) - mis à jour")
    
    # DELETE
    response = requests.delete(f"{BASE_URL}/api/compte-resultat/override/{test_year}?property_id={property_id}")
    if response.status_code != 204:
        log_error(f"DELETE override échoué: {response.status_code}")
        return False
    log_success(f"DELETE /api/compte-resultat/override/{test_year} - supprimé")
    
    return True

def test_calculate(property_id):
    """Tester le calcul du compte de résultat."""
    log_info("=== Test Calculate ===")
    
    response = requests.get(f"{BASE_URL}/api/compte-resultat/calculate?property_id={property_id}&years=2023,2024")
    if response.status_code != 200:
        log_error(f"GET calculate échoué: {response.status_code} {response.text}")
        return False
    result = response.json()
    log_success(f"GET /api/compte-resultat/calculate - années calculées: {result.get('years', [])}")
    
    return True

def test_data_endpoints(property_id):
    """Tester les endpoints de données."""
    log_info("=== Test Data Endpoints ===")
    
    # GET data
    response = requests.get(f"{BASE_URL}/api/compte-resultat?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET compte-resultat échoué: {response.status_code}")
        return False
    log_success(f"GET /api/compte-resultat - OK")
    
    # GET data (alternate endpoint)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/data?property_id={property_id}")
    if response.status_code != 200:
        log_error(f"GET compte-resultat/data échoué: {response.status_code}")
        return False
    log_success(f"GET /api/compte-resultat/data - OK")
    
    return True

def main():
    print("\n" + "="*60)
    print("TEST DE NON-RÉGRESSION - COMPTE DE RÉSULTAT - PHASE 11 bis 5.2")
    print("="*60 + "\n")
    
    # Récupérer une propriété existante
    prop = get_first_property()
    if not prop:
        return 1
    
    property_id = prop['id']
    log_info(f"Utilisation de la propriété: {property_id} - {prop['name']}")
    
    all_passed = True
    
    # Test CRUD mappings
    if not test_mappings_crud(property_id):
        all_passed = False
    
    # Test config
    if not test_config_crud(property_id):
        all_passed = False
    
    # Test CRUD overrides
    if not test_overrides_crud(property_id):
        all_passed = False
    
    # Test calculate
    if not test_calculate(property_id):
        all_passed = False
    
    # Test data endpoints
    if not test_data_endpoints(property_id):
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        log_success("TOUS LES TESTS DE NON-RÉGRESSION SONT PASSÉS ✓")
        return 0
    else:
        log_error("CERTAINS TESTS ONT ÉCHOUÉ ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
