"""
Test manuel pour les endpoints API de loan configurations.

⚠️ Ce test nécessite que le serveur backend soit démarré sur http://localhost:8000

Pour exécuter :
    python3 backend/tests/test_loan_configs_endpoints_manual.py
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Affiche une section de test."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_endpoint(method, endpoint, description, data=None, params=None):
    """Teste un endpoint et affiche le résultat."""
    print(f"\n📌 {description}")
    print(f"   {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}")
        else:
            print(f"   ❌ Méthode {method} non supportée")
            return None
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"   ✅ Succès")
            if response.content:
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(result) < 15:
                        print(f"   Réponse: {json.dumps(result, indent=2, default=str)}")
                    else:
                        print(f"   Réponse: {type(result).__name__} ({len(result) if isinstance(result, (list, dict)) else 'N/A'} éléments)")
                except:
                    print(f"   Réponse: {response.text[:200]}")
            return response
        else:
            print(f"   ❌ Erreur: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur: Impossible de se connecter au serveur")
        print(f"   💡 Assurez-vous que le serveur backend est démarré: python3 -m uvicorn api.main:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"   ❌ Erreur: {type(e).__name__}: {e}")
        return None

def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("  TEST DES ENDPOINTS LOAN CONFIGS")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré sur http://localhost:8000")
    
    # Test 1: GET /api/loan-configs (liste vide au début)
    print_section("1. GET /api/loan-configs - Liste des configurations")
    response = test_endpoint("GET", "/loan-configs", "Récupérer la liste des configurations")
    
    # Test 2: POST /api/loan-configs - Créer une configuration
    print_section("2. POST /api/loan-configs - Créer une configuration")
    config_data = {
        "name": "Prêt principal",
        "credit_amount": 200000.0,
        "interest_rate": 2.5,
        "duration_years": 20,
        "initial_deferral_months": 0
    }
    response = test_endpoint("POST", "/loan-configs", "Créer une configuration", data=config_data)
    config_id = None
    if response and response.status_code == 201:
        result = response.json()
        config_id = result.get("id")
        print(f"   💾 ID créé: {config_id}")
    
    # Test 3: POST /api/loan-configs - Essayer de créer un doublon (doit échouer)
    if config_id:
        print_section("3. POST /api/loan-configs - Essayer de créer un doublon")
        test_endpoint("POST", "/loan-configs", "Essayer de créer une configuration avec le même nom (doit échouer)", data=config_data)
    
    # Test 4: GET /api/loan-configs/{id} - Récupérer une configuration
    if config_id:
        print_section(f"4. GET /api/loan-configs/{config_id} - Récupérer une configuration")
        test_endpoint("GET", f"/loan-configs/{config_id}", f"Récupérer la configuration {config_id}")
    
    # Test 5: GET /api/loan-configs - Liste avec tri
    print_section("5. GET /api/loan-configs - Liste avec tri")
    test_endpoint("GET", "/loan-configs", "Liste triée par nom", params={"sort_by": "name", "sort_direction": "asc"})
    test_endpoint("GET", "/loan-configs", "Liste triée par montant", params={"sort_by": "credit_amount", "sort_direction": "desc"})
    
    # Test 6: PUT /api/loan-configs/{id} - Mettre à jour
    if config_id:
        print_section(f"6. PUT /api/loan-configs/{config_id} - Mettre à jour")
        update_data = {
            "interest_rate": 3.0,
            "duration_years": 25
        }
        test_endpoint("PUT", f"/loan-configs/{config_id}", f"Mettre à jour la configuration {config_id}", data=update_data)
    
    # Test 7: Créer une deuxième configuration
    print_section("7. POST /api/loan-configs - Créer une deuxième configuration")
    config_data_2 = {
        "name": "Prêt construction",
        "credit_amount": 150000.0,
        "interest_rate": 2.8,
        "duration_years": 15,
        "initial_deferral_months": 6
    }
    response = test_endpoint("POST", "/loan-configs", "Créer une deuxième configuration", data=config_data_2)
    config_id_2 = None
    if response and response.status_code == 201:
        result = response.json()
        config_id_2 = result.get("id")
        print(f"   💾 ID créé: {config_id_2}")
    
    # Test 8: GET /api/loan-configs - Liste avec plusieurs configurations
    print_section("8. GET /api/loan-configs - Liste avec plusieurs configurations")
    response = test_endpoint("GET", "/loan-configs", "Récupérer toutes les configurations")
    if response and response.status_code == 200:
        result = response.json()
        print(f"   📊 Total: {result.get('total')} configuration(s)")
        for item in result.get('items', [])[:3]:
            print(f"      - {item.get('name')}: {item.get('credit_amount')}€ à {item.get('interest_rate')}% sur {item.get('duration_years')} ans")
    
    # Test 9: DELETE /api/loan-configs/{id} - Supprimer
    if config_id_2:
        print_section(f"9. DELETE /api/loan-configs/{config_id_2} - Supprimer")
        test_endpoint("DELETE", f"/loan-configs/{config_id_2}", f"Supprimer la configuration {config_id_2}")
        
        # Vérifier que c'est bien supprimé
        print("\n   Vérification de la suppression...")
        response = test_endpoint("GET", f"/loan-configs/{config_id_2}", "Tenter de récupérer la configuration supprimée")
        if response and response.status_code == 404:
            print("   ✅ La configuration a bien été supprimée")
    
    # Test 10: DELETE /api/loan-configs/{id} - Supprimer la première
    if config_id:
        print_section(f"10. DELETE /api/loan-configs/{config_id} - Supprimer la première configuration")
        test_endpoint("DELETE", f"/loan-configs/{config_id}", f"Supprimer la configuration {config_id}")
    
    print("\n" + "=" * 60)
    print("  ✅ TESTS TERMINÉS")
    print("=" * 60)

if __name__ == "__main__":
    main()
