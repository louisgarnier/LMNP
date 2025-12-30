"""
Test manuel pour les endpoints API des configurations de crédit (loan configs).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_loan_configs_endpoints_manual.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def print_section(title):
    """Affiche une section de test."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success, message):
    """Affiche le résultat d'un test."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def test_get_loan_configs():
    """Test GET /api/loan-configs"""
    print_section("Test 1: GET /api/loan-configs (Liste)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/loan-configs")
        if response.status_code == 200:
            data = response.json()
            print(f"Total: {data.get('total', 0)}")
            print(f"Configs: {len(data.get('configs', []))}")
            print_result(True, f"Liste récupérée: {data.get('total', 0)} configuration(s)")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_create_loan_config():
    """Test POST /api/loan-configs"""
    print_section("Test 2: POST /api/loan-configs (Création)")
    try:
        config_data = {
            "name": "Prêt principal",
            "credit_amount": 200000.0,
            "interest_rate": 3.2,
            "duration_years": 20,
            "initial_deferral_months": 12
        }
        response = requests.post(
            f"{API_BASE_URL}/api/loan-configs",
            json=config_data
        )
        if response.status_code == 201:
            data = response.json()
            print(f"ID créé: {data.get('id')}")
            print(f"Nom: {data.get('name')}")
            print(f"Montant: {data.get('credit_amount')} €")
            print(f"Taux: {data.get('interest_rate')} %")
            print(f"Durée: {data.get('duration_years')} ans")
            print_result(True, f"Configuration créée avec ID {data.get('id')}")
            return data.get('id')
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return None

def test_get_loan_config_by_id(config_id):
    """Test GET /api/loan-configs/{id}"""
    print_section(f"Test 3: GET /api/loan-configs/{config_id} (Détail)")
    if not config_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        response = requests.get(f"{API_BASE_URL}/api/loan-configs/{config_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"ID: {data.get('id')}")
            print(f"Nom: {data.get('name')}")
            print(f"Montant: {data.get('credit_amount')} €")
            print_result(True, f"Configuration récupérée")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_update_loan_config(config_id):
    """Test PUT /api/loan-configs/{id}"""
    print_section(f"Test 4: PUT /api/loan-configs/{config_id} (Mise à jour)")
    if not config_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        update_data = {
            "credit_amount": 250000.0,
            "interest_rate": 3.5,
            "duration_years": 25
        }
        response = requests.put(
            f"{API_BASE_URL}/api/loan-configs/{config_id}",
            json=update_data
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Montant mis à jour: {data.get('credit_amount')} €")
            print(f"Taux mis à jour: {data.get('interest_rate')} %")
            print(f"Durée mise à jour: {data.get('duration_years')} ans")
            print_result(True, f"Configuration mise à jour")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_delete_loan_config(config_id):
    """Test DELETE /api/loan-configs/{id}"""
    print_section(f"Test 5: DELETE /api/loan-configs/{config_id} (Suppression)")
    if not config_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        response = requests.delete(f"{API_BASE_URL}/api/loan-configs/{config_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            print_result(True, f"Configuration supprimée")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("  TESTS MANUELS - Endpoints API Loan Configs")
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print("⚠️  Assurez-vous que le serveur backend est démarré (uvicorn backend.api.main:app)")
    
    results = []
    
    # Test 1: Liste
    results.append(("GET Liste", test_get_loan_configs()))
    
    # Test 2: Création
    config_id = test_create_loan_config()
    results.append(("POST Création", config_id is not None))
    
    # Test 3: Détail
    results.append(("GET Détail", test_get_loan_config_by_id(config_id)))
    
    # Test 4: Mise à jour
    results.append(("PUT Mise à jour", test_update_loan_config(config_id)))
    
    # Test 5: Suppression
    results.append(("DELETE Suppression", test_delete_loan_config(config_id)))
    
    # Résumé
    print_section("RÉSUMÉ DES TESTS")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result is True:
            print_result(True, test_name)
            passed += 1
        elif result is False:
            print_result(False, test_name)
            failed += 1
    
    print(f"\n✅ Réussis: {passed}")
    print(f"❌ Échoués: {failed}")
    print(f"📊 Total: {len(results)}")

if __name__ == "__main__":
    main()

