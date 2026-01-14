"""
Tests manuels pour les endpoints API du compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script teste les endpoints API du compte de résultat.
Il doit être exécuté avec le serveur backend démarré.

Usage:
    1. Démarrer le serveur backend: uvicorn backend.api.main:app --reload
    2. Exécuter ce script: python backend/tests/test_compte_resultat_endpoints_manual.py
"""

import sys
from pathlib import Path
import requests
import json

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configuration
BASE_URL = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}


def print_section(title):
    """Afficher un titre de section."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_get_mappings():
    """Test GET /api/compte-resultat/mappings"""
    print_section("1. Test GET /api/compte-resultat/mappings")
    
    response = requests.get(f"{BASE_URL}/compte-resultat/mappings")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total mappings: {data['total']}")
        print(f"✓ Items: {len(data['items'])}")
        if data['items']:
            print(f"  Premier mapping: {data['items'][0]}")
    else:
        print(f"❌ Error: {response.text}")
    
    return response.status_code == 200


def test_create_mapping():
    """Test POST /api/compte-resultat/mappings"""
    print_section("2. Test POST /api/compte-resultat/mappings")
    
    mapping_data = {
        "category_name": "Test Catégorie",
        "level_1_values": '["TEST_LEVEL_1"]'
    }
    
    response = requests.post(
        f"{BASE_URL}/compte-resultat/mappings",
        headers=HEADERS,
        json=mapping_data
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Mapping créé: ID={data['id']}, Category={data['category_name']}")
        return data['id']
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_update_mapping(mapping_id):
    """Test PUT /api/compte-resultat/mappings/{id}"""
    if not mapping_id:
        print_section("3. Test PUT /api/compte-resultat/mappings/{id} - SKIPPED (pas de mapping créé)")
        return
    
    print_section("3. Test PUT /api/compte-resultat/mappings/{id}")
    
    update_data = {
        "category_name": "Test Catégorie Modifiée",
        "level_1_values": '["TEST_LEVEL_1", "TEST_LEVEL_2"]'
    }
    
    response = requests.put(
        f"{BASE_URL}/compte-resultat/mappings/{mapping_id}",
        headers=HEADERS,
        json=update_data
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Mapping mis à jour: Category={data['category_name']}")
    else:
        print(f"❌ Error: {response.text}")


def test_calculate_compte_resultat():
    """Test GET /api/compte-resultat/calculate"""
    print_section("4. Test GET /api/compte-resultat/calculate")
    
    # Utiliser des années récentes
    years = "2023,2024"
    
    response = requests.get(
        f"{BASE_URL}/compte-resultat/calculate",
        params={"years": years}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Années calculées: {data['years']}")
        for year, result in data['results'].items():
            print(f"  Année {year}:")
            print(f"    - Total produits: {result.get('total_produits', 0)}")
            print(f"    - Total charges: {result.get('total_charges', 0)}")
            print(f"    - Résultat exploitation: {result.get('resultat_exploitation', 0)}")
    else:
        print(f"❌ Error: {response.text}")


def test_generate_compte_resultat():
    """Test POST /api/compte-resultat/generate"""
    print_section("5. Test POST /api/compte-resultat/generate")
    
    year = 2024
    
    response = requests.post(
        f"{BASE_URL}/compte-resultat/generate",
        params={"year": year}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Compte de résultat généré pour l'année {data['year']}")
        print(f"  Message: {data['message']}")
    else:
        print(f"❌ Error: {response.text}")


def test_get_compte_resultat():
    """Test GET /api/compte-resultat"""
    print_section("6. Test GET /api/compte-resultat")
    
    # Test avec une année spécifique
    response = requests.get(
        f"{BASE_URL}/compte-resultat",
        params={"year": 2024}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total données: {data['total']}")
        print(f"✓ Items: {len(data['items'])}")
        if data['items']:
            print(f"  Première donnée: Année={data['items'][0]['annee']}, Catégorie={data['items'][0]['category_name']}, Montant={data['items'][0]['amount']}")
    else:
        print(f"❌ Error: {response.text}")


def test_get_compte_resultat_data():
    """Test GET /api/compte-resultat/data"""
    print_section("7. Test GET /api/compte-resultat/data")
    
    response = requests.get(f"{BASE_URL}/compte-resultat/data")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total données: {data['total']}")
        print(f"✓ Items: {len(data['items'])}")
    else:
        print(f"❌ Error: {response.text}")


def test_delete_mapping(mapping_id):
    """Test DELETE /api/compte-resultat/mappings/{id}"""
    if not mapping_id:
        print_section("8. Test DELETE /api/compte-resultat/mappings/{id} - SKIPPED (pas de mapping créé)")
        return
    
    print_section("8. Test DELETE /api/compte-resultat/mappings/{id}")
    
    response = requests.delete(f"{BASE_URL}/compte-resultat/mappings/{mapping_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 204:
        print("✓ Mapping supprimé")
    else:
        print(f"❌ Error: {response.text}")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("Tests manuels pour les endpoints API du compte de résultat")
    print("=" * 60)
    print("\n⚠️  Vérification que le serveur backend est démarré...")
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✓ Serveur backend accessible")
        else:
            print("❌ Serveur backend répond mais avec une erreur")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Serveur backend non accessible")
        print("   Démarrez-le avec: uvicorn backend.api.main:app --reload")
        sys.exit(1)
    
    try:
        # Test 1: GET mappings
        test_get_mappings()
        
        # Test 2: CREATE mapping
        mapping_id = test_create_mapping()
        
        # Test 3: UPDATE mapping
        test_update_mapping(mapping_id)
        
        # Test 4: CALCULATE compte de résultat
        test_calculate_compte_resultat()
        
        # Test 5: GENERATE compte de résultat
        test_generate_compte_resultat()
        
        # Test 6: GET compte de résultat
        test_get_compte_resultat()
        
        # Test 7: GET compte de résultat data
        test_get_compte_resultat_data()
        
        # Test 8: DELETE mapping
        test_delete_mapping(mapping_id)
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests terminés!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur de connexion: Le serveur backend n'est pas démarré.")
        print("   Démarrez-le avec: uvicorn backend.api.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
