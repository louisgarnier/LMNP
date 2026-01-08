"""
Test script manuel pour les endpoints d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script teste les endpoints API d'amortissement.
Le serveur backend doit être démarré pour exécuter ces tests.

Usage:
    python backend/tests/test_amortization_endpoints_manual.py
"""

import sys
import json
from pathlib import Path

try:
    import httpx
except ImportError:
    print("⚠️  Le module 'httpx' n'est pas installé.")
    print("   Installez-le avec: pip install httpx")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_URL = "http://localhost:8000/api"


def test_get_results():
    """Test GET /api/amortization/results"""
    print("Test 1: GET /api/amortization/results")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/results", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Results by year: {len(data.get('results', {}))} années")
        print(f"✓ Grand total: {data.get('grand_total', 0):.2f}")
        print(f"✓ Response keys: {list(data.keys())}")
        
        # Afficher un aperçu
        if data.get('results'):
            first_year = min(data['results'].keys())
            print(f"✓ Exemple année {first_year}: {data['results'][first_year]}")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_get_aggregated():
    """Test GET /api/amortization/results/aggregated"""
    print("\nTest 2: GET /api/amortization/results/aggregated")
    print("-" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/amortization/results/aggregated", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Categories: {len(data.get('categories', []))} catégories")
        print(f"✓ Years: {len(data.get('years', []))} années")
        print(f"✓ Data matrix: {len(data.get('data', []))} lignes")
        print(f"✓ Grand total: {data.get('grand_total', 0):.2f}")
        
        # Afficher un aperçu
        if data.get('categories'):
            print(f"✓ Catégories: {data['categories'][:5]}...")
        if data.get('years'):
            print(f"✓ Années: {data['years'][:5]}...")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_get_details():
    """Test GET /api/amortization/results/details"""
    print("\nTest 3: GET /api/amortization/results/details")
    print("-" * 60)
    
    try:
        # Test sans filtres
        response = httpx.get(f"{BASE_URL}/amortization/results/details", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Total items: {data.get('total', 0)}")
        print(f"✓ Items returned: {len(data.get('items', []))}")
        print(f"✓ Page: {data.get('page', 1)}")
        print(f"✓ Page size: {data.get('page_size', 100)}")
        
        # Test avec filtre année
        if data.get('total', 0) > 0:
            first_item = data['items'][0]
            test_year = first_item.get('year')
            
            response2 = httpx.get(
                f"{BASE_URL}/amortization/results/details",
                params={"year": test_year},
                timeout=10.0
            )
            response2.raise_for_status()
            data2 = response2.json()
            print(f"✓ Filtre par année {test_year}: {data2.get('total', 0)} résultats")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def test_recalculate():
    """Test POST /api/amortization/recalculate"""
    print("\nTest 4: POST /api/amortization/recalculate")
    print("-" * 60)
    
    try:
        response = httpx.post(f"{BASE_URL}/amortization/recalculate", timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Message: {data.get('message', '')}")
        print(f"✓ Results created: {data.get('results_created', 0)}")
        
        return True
    except httpx.RequestError as e:
        print(f"✗ Erreur: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Amortization API Endpoints")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré (uvicorn backend.api.main:app)")
    print()
    
    results = []
    
    results.append(("GET /amortization/results", test_get_results()))
    results.append(("GET /amortization/results/aggregated", test_get_aggregated()))
    results.append(("GET /amortization/results/details", test_get_details()))
    results.append(("POST /amortization/recalculate", test_recalculate()))
    
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

