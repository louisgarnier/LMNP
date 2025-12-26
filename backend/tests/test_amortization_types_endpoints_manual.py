"""
Script de test manuel pour les endpoints AmortizationType.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Usage:
    python backend/tests/test_amortization_types_endpoints_manual.py

Prérequis:
    - Serveur backend démarré sur http://localhost:8000
    - Base de données initialisée avec les 7 types initiaux
"""

import requests
import json
from datetime import date

API_BASE_URL = "http://localhost:8000"


def print_response(response, title):
    """Affiche la réponse de manière lisible."""
    print(f"\n{'='*60}")
    print(f"📤 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    
    if response.status_code >= 400:
        print(f"❌ Erreur: {response.text}")
    else:
        try:
            print("✅ Réponse:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False, default=str))
        except:
            print(f"✅ Réponse: {response.text}")


def test_get_all_types():
    """Test GET /api/amortization/types"""
    response = requests.get(f"{API_BASE_URL}/api/amortization/types")
    print_response(response, "GET /api/amortization/types - Liste tous les types")
    return response.json() if response.status_code == 200 else None


def test_get_type_by_id(type_id: int):
    """Test GET /api/amortization/types/{id}"""
    response = requests.get(f"{API_BASE_URL}/api/amortization/types/{type_id}")
    print_response(response, f"GET /api/amortization/types/{type_id}")
    return response.json() if response.status_code == 200 else None


def test_create_type():
    """Test POST /api/amortization/types"""
    type_data = {
        "name": "Immobilisation mobilier 2",
        "level_2_value": "ammortissements",
        "level_1_values": ["Test Furniture"],
        "start_date": "2025-01-01",
        "duration": 5.0,
        "annual_amount": None
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/amortization/types",
        json=type_data
    )
    print_response(response, "POST /api/amortization/types - Créer un type")
    return response.json() if response.status_code == 201 else None


def test_update_type(type_id: int):
    """Test PUT /api/amortization/types/{id}"""
    update_data = {
        "duration": 10.0,
        "level_1_values": ["Test Furniture", "Another Value"]
    }
    
    response = requests.put(
        f"{API_BASE_URL}/api/amortization/types/{type_id}",
        json=update_data
    )
    print_response(response, f"PUT /api/amortization/types/{type_id} - Mettre à jour")
    return response.json() if response.status_code == 200 else None


def test_get_amount(type_id: int):
    """Test GET /api/amortization/types/{id}/amount"""
    response = requests.get(f"{API_BASE_URL}/api/amortization/types/{type_id}/amount")
    print_response(response, f"GET /api/amortization/types/{type_id}/amount - Calculer montant")
    return response.json() if response.status_code == 200 else None


def test_get_cumulated(type_id: int):
    """Test GET /api/amortization/types/{id}/cumulated"""
    response = requests.get(f"{API_BASE_URL}/api/amortization/types/{type_id}/cumulated")
    print_response(response, f"GET /api/amortization/types/{type_id}/cumulated - Calculer cumulé")
    return response.json() if response.status_code == 200 else None


def test_delete_type(type_id: int):
    """Test DELETE /api/amortization/types/{id}"""
    response = requests.delete(f"{API_BASE_URL}/api/amortization/types/{type_id}")
    print_response(response, f"DELETE /api/amortization/types/{type_id} - Supprimer")
    return response.status_code == 204


if __name__ == "__main__":
    print("🧪 Tests manuels des endpoints AmortizationType")
    print("=" * 60)
    print("⚠️  Assurez-vous que le serveur backend est démarré sur http://localhost:8000")
    print("=" * 60)
    
    try:
        # Test 1: Liste tous les types
        all_types = test_get_all_types()
        
        if all_types and all_types.get("types"):
            first_type_id = all_types["types"][0]["id"]
            
            # Test 2: Récupérer un type par ID
            test_get_type_by_id(first_type_id)
            
            # Test 3: Calculer montant
            test_get_amount(first_type_id)
            
            # Test 4: Calculer cumulé
            test_get_cumulated(first_type_id)
            
            # Test 5: Créer un nouveau type
            new_type = test_create_type()
            
            if new_type:
                new_type_id = new_type["id"]
                
                # Test 6: Mettre à jour le type
                test_update_type(new_type_id)
                
                # Test 7: Supprimer le type (si pas utilisé)
                test_delete_type(new_type_id)
        
        print("\n" + "=" * 60)
        print("✅ Tests terminés!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter au serveur backend")
        print("   Assurez-vous que le serveur est démarré sur http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

