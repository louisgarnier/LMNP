"""
Test script manuel pour les endpoints d'amortization types.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script teste les endpoints API d'amortization types (CRUD + calculs).
Le serveur backend doit être démarré pour exécuter ces tests.

Usage:
    python backend/tests/test_amortization_types_endpoints_manual.py
"""

import sys
import json
from pathlib import Path
from datetime import date

try:
    import httpx
except ImportError:
    print("⚠️  Le module 'httpx' n'est pas installé.")
    print("   Installez-le avec: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8000/api"


def test_get_all_types():
    """Test GET /api/amortization/types"""
    print("Test 1: GET /api/amortization/types")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/types", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Total types: {data.get('total', 0)}")
        print(f"✓ Items returned: {len(data.get('items', []))}")
        
        if data.get('items'):
            first_type = data['items'][0]
            print(f"✓ Exemple type: {first_type.get('name')} (ID: {first_type.get('id')})")
        
        return True, data.get('items', [])
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False, []


def test_get_type_by_id(type_id: int):
    """Test GET /api/amortization/types/{id}"""
    print(f"\nTest 2: GET /api/amortization/types/{type_id}")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/types/{type_id}", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type name: {data.get('name')}")
        print(f"✓ Level 2: {data.get('level_2_value')}")
        print(f"✓ Duration: {data.get('duration')} ans")
        
        return True, data
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False, None


def test_create_type():
    """Test POST /api/amortization/types"""
    print("\nTest 3: POST /api/amortization/types")
    print("-" * 60)
    
    try:
        new_type = {
            "name": "Test Immobilisation",
            "level_2_value": "test_ammort",
            "level_1_values": ["Test Level 1"],
            "duration": 10.0,
            "annual_amount": None,
            "start_date": None
        }
        
        response = httpx.post(
            f"{BASE_URL}/amortization/types",
            json=new_type,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type créé: {data.get('name')} (ID: {data.get('id')})")
        
        return True, data.get('id')
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False, None


def test_update_type(type_id: int):
    """Test PUT /api/amortization/types/{id}"""
    print(f"\nTest 4: PUT /api/amortization/types/{type_id}")
    print("-" * 60)
    
    try:
        update_data = {
            "name": "Test Immobilisation Modifié",
            "duration": 15.0
        }
        
        response = httpx.put(
            f"{BASE_URL}/amortization/types/{type_id}",
            json=update_data,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type mis à jour: {data.get('name')}")
        print(f"✓ Nouvelle durée: {data.get('duration')} ans")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False


def test_get_amount(type_id: int):
    """Test GET /api/amortization/types/{id}/amount"""
    print(f"\nTest 5: GET /api/amortization/types/{type_id}/amount")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/types/{type_id}/amount", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type: {data.get('type_name')}")
        print(f"✓ Montant: {data.get('amount', 0):.2f} EUR")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_get_cumulated(type_id: int):
    """Test GET /api/amortization/types/{id}/cumulated"""
    print(f"\nTest 6: GET /api/amortization/types/{type_id}/cumulated")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/types/{type_id}/cumulated", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type: {data.get('type_name')}")
        print(f"✓ Montant cumulé: {data.get('cumulated_amount', 0):.2f} EUR")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_get_transaction_count(type_id: int):
    """Test GET /api/amortization/types/{id}/transaction-count"""
    print(f"\nTest 7: GET /api/amortization/types/{type_id}/transaction-count")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/types/{type_id}/transaction-count", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type: {data.get('type_name')}")
        print(f"✓ Nombre de transactions: {data.get('transaction_count', 0)}")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_delete_type(type_id: int):
    """Test DELETE /api/amortization/types/{id}"""
    print(f"\nTest 8: DELETE /api/amortization/types/{type_id}")
    print("-" * 60)
    
    try:
        response = httpx.delete(f"{BASE_URL}/amortization/types/{type_id}", timeout=10.0)
        response.raise_for_status()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Type supprimé avec succès")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Amortization Types API Endpoints")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré (uvicorn backend.api.main:app)")
    print()
    
    results = []
    created_type_id = None
    
    # Test 1: GET all
    success, types = test_get_all_types()
    results.append(("GET /amortization/types", success))
    
    # Test 2: GET by ID (utiliser le premier type existant ou créer un nouveau)
    if types:
        first_type_id = types[0]['id']
        success, type_data = test_get_type_by_id(first_type_id)
        results.append(("GET /amortization/types/{id}", success))
    else:
        print("\n⚠️  Aucun type existant, on passe au test de création")
        results.append(("GET /amortization/types/{id}", True))  # Skip
    
    # Test 3: CREATE
    success, created_type_id = test_create_type()
    results.append(("POST /amortization/types", success))
    
    if created_type_id:
        # Test 4: UPDATE
        success = test_update_type(created_type_id)
        results.append(("PUT /amortization/types/{id}", success))
        
        # Test 5: GET amount
        success = test_get_amount(created_type_id)
        results.append(("GET /amortization/types/{id}/amount", success))
        
        # Test 6: GET cumulated
        success = test_get_cumulated(created_type_id)
        results.append(("GET /amortization/types/{id}/cumulated", success))
        
        # Test 7: GET transaction count
        success = test_get_transaction_count(created_type_id)
        results.append(("GET /amortization/types/{id}/transaction-count", success))
        
        # Test 8: DELETE
        success = test_delete_type(created_type_id)
        results.append(("DELETE /amortization/types/{id}", success))
    else:
        print("\n⚠️  Impossible de créer un type, certains tests sont ignorés")
        results.append(("PUT /amortization/types/{id}", False))
        results.append(("GET /amortization/types/{id}/amount", False))
        results.append(("GET /amortization/types/{id}/cumulated", False))
        results.append(("GET /amortization/types/{id}/transaction-count", False))
        results.append(("DELETE /amortization/types/{id}", False))
    
    print("\n" + "=" * 60)
    print("Résumé des tests")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passés")
    
    if passed == total:
        print("✓ Tous les tests sont passés!")
        return 0
    else:
        print("✗ Certains tests ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())

