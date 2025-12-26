"""
Script de test manuel pour les endpoints d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Usage:
    python backend/tests/test_amortization_endpoints_manual.py
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


def test_get_results():
    """Test GET /api/amortization/results"""
    print("\n📤 Test GET /api/amortization/results")
    print("-" * 50)
    
    response = requests.get(f"{API_BASE_URL}/api/amortization/results")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Résultats récupérés:")
        print(f"  - Nombre d'années: {len(data.get('results', {}))}")
        print(f"  - Totaux par année: {data.get('totals_by_year', {})}")
        print(f"  - Totaux par catégorie: {data.get('totals_by_category', {})}")
        print(f"  - Grand total: {data.get('grand_total', 0):.2f}")
    else:
        print(f"❌ Erreur: {response.text}")


def test_get_results_aggregated():
    """Test GET /api/amortization/results/aggregated"""
    print("\n📤 Test GET /api/amortization/results/aggregated")
    print("-" * 50)
    
    response = requests.get(f"{API_BASE_URL}/api/amortization/results/aggregated")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Tableau croisé récupéré:")
        print(f"  - Catégories: {data.get('categories', [])}")
        print(f"  - Années: {data.get('years', [])}")
        print(f"  - Données (matrice): {len(data.get('data', []))} lignes x {len(data.get('years', []))} colonnes")
        print(f"  - Totaux par ligne: {data.get('row_totals', [])}")
        print(f"  - Totaux par colonne: {data.get('column_totals', [])}")
        print(f"  - Grand total: {data.get('grand_total', 0):.2f}")
    else:
        print(f"❌ Erreur: {response.text}")


def test_get_results_details():
    """Test GET /api/amortization/results/details"""
    print("\n📤 Test GET /api/amortization/results/details")
    print("-" * 50)
    
    # Test sans filtres
    response = requests.get(f"{API_BASE_URL}/api/amortization/results/details")
    print(f"Status (sans filtres): {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transactions récupérées: {data.get('total', 0)} total, {len(data.get('transactions', []))} dans cette page")
    
    # Test avec filtre année
    response = requests.get(f"{API_BASE_URL}/api/amortization/results/details?year=2021")
    print(f"\nStatus (avec filtre year=2021): {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transactions pour 2021: {data.get('total', 0)} total")
    
    # Test avec filtre catégorie
    response = requests.get(f"{API_BASE_URL}/api/amortization/results/details?category=meubles")
    print(f"\nStatus (avec filtre category=meubles): {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transactions pour meubles: {data.get('total', 0)} total")
    
    # Test avec pagination
    response = requests.get(f"{API_BASE_URL}/api/amortization/results/details?skip=0&limit=10")
    print(f"\nStatus (avec pagination skip=0&limit=10): {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transactions paginées: {len(data.get('transactions', []))} dans cette page")


def test_post_recalculate():
    """Test POST /api/amortization/recalculate"""
    print("\n📤 Test POST /api/amortization/recalculate")
    print("-" * 50)
    
    response = requests.post(f"{API_BASE_URL}/api/amortization/recalculate")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Recalcul effectué:")
        print(f"  - Message: {data.get('message', '')}")
        print(f"  - Transactions traitées: {data.get('transactions_processed', 0)}")
    else:
        print(f"❌ Erreur: {response.text}")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Tests manuels - Endpoints Amortissements")
    print("=" * 50)
    print(f"\n⚠️  Assure-toi que le serveur backend est démarré sur {API_BASE_URL}")
    print("   (cd backend && uvicorn api.main:app --reload)")
    
    try:
        # Test 1: GET results
        test_get_results()
        
        # Test 2: GET results aggregated
        test_get_results_aggregated()
        
        # Test 3: GET results details
        test_get_results_details()
        
        # Test 4: POST recalculate
        test_post_recalculate()
        
        print("\n" + "=" * 50)
        print("✅ Tests terminés")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter au serveur")
        print(f"   Vérifie que le backend est démarré sur {API_BASE_URL}")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

