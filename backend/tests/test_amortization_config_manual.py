"""
Script de test manuel pour les endpoints de configuration d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Usage:
    python backend/tests/test_amortization_config_manual.py
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_get_config():
    """Test GET /api/amortization/config"""
    print("\n📤 Test GET /api/amortization/config")
    print("-" * 50)
    
    response = requests.get(f"{API_BASE_URL}/api/amortization/config")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Configuration trouvée:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    elif response.status_code == 404:
        print("ℹ️  Aucune configuration (normal si pas encore créée)")
    else:
        print(f"❌ Erreur: {response.text}")


def test_create_config():
    """Test PUT /api/amortization/config - Créer configuration"""
    print("\n📤 Test PUT /api/amortization/config - CREATE")
    print("-" * 50)
    
    config_data = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture", "Meubles"],
            "travaux": ["Construction work", "Travaux"],
            "construction": ["Construction loan", "Pret construction"],
            "terrain": ["Land loan", "Pret terrain"]
        },
        "duration_meubles": 10,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    
    print(f"Données envoyées:")
    print(json.dumps(config_data, indent=2, ensure_ascii=False))
    
    response = requests.put(
        f"{API_BASE_URL}/api/amortization/config",
        json=config_data
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Configuration créée:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Erreur: {response.text}")


def test_update_config():
    """Test PUT /api/amortization/config - Mettre à jour"""
    print("\n📤 Test PUT /api/amortization/config - UPDATE")
    print("-" * 50)
    
    config_data = {
        "level_2_value": "ammort",
        "level_3_mapping": {
            "meubles": ["Furniture"],
            "travaux": ["Construction work"],
            "construction": ["Construction loan"],
            "terrain": ["Land loan"]
        },
        "duration_meubles": 15,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    
    print(f"Données envoyées (mise à jour):")
    print(json.dumps(config_data, indent=2, ensure_ascii=False))
    
    response = requests.put(
        f"{API_BASE_URL}/api/amortization/config",
        json=config_data
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Configuration mise à jour:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Erreur: {response.text}")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Tests manuels - Configuration Amortissements")
    print("=" * 50)
    print(f"\n⚠️  Assure-toi que le serveur backend est démarré sur {API_BASE_URL}")
    print("   (cd backend && uvicorn api.main:app --reload)")
    
    try:
        # Test 1: GET (devrait être 404 si pas encore créé)
        test_get_config()
        
        # Test 2: CREATE
        test_create_config()
        
        # Test 3: GET (devrait maintenant retourner la config)
        test_get_config()
        
        # Test 4: UPDATE
        test_update_config()
        
        # Test 5: GET (vérifier la mise à jour)
        test_get_config()
        
        print("\n" + "=" * 50)
        print("✅ Tests terminés")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter au serveur")
        print(f"   Vérifie que le backend est démarré sur {API_BASE_URL}")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

