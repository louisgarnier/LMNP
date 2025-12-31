"""
Test manuel des endpoints API pour le compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_compte_resultat_endpoints_manual.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
from datetime import date

API_BASE_URL = "http://localhost:8000"


def test_get_mappings():
    """Test GET /api/compte-resultat/mappings"""
    print("=" * 60)
    print("Test GET /api/compte-resultat/mappings")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE_URL}/api/compte-resultat/mappings")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total mappings: {data['total']}")
        print(f"✅ Mappings: {len(data['mappings'])}")
        if data['mappings']:
            print(f"   Premier mapping: {data['mappings'][0]}")
    else:
        print(f"❌ Erreur: {response.text}")
    
    return response.status_code == 200


def test_create_mapping():
    """Test POST /api/compte-resultat/mappings"""
    print("\n" + "=" * 60)
    print("Test POST /api/compte-resultat/mappings")
    print("=" * 60)
    
    mapping_data = {
        "category_name": "Loyers hors charge encaissés",
        "level_1_values": ["PRODUITS"],
        "level_2_values": ["LOYERS"],
        "level_3_values": None
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/compte-resultat/mappings",
        json=mapping_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Mapping créé avec ID: {data['id']}")
        print(f"   Category: {data['category_name']}")
        print(f"   Level 1: {data['level_1_values']}")
        print(f"   Level 2: {data['level_2_values']}")
        return data['id']
    else:
        print(f"❌ Erreur: {response.text}")
        return None


def test_update_mapping(mapping_id: int):
    """Test PUT /api/compte-resultat/mappings/{id}"""
    print("\n" + "=" * 60)
    print(f"Test PUT /api/compte-resultat/mappings/{mapping_id}")
    print("=" * 60)
    
    update_data = {
        "level_2_values": ["LOYERS", "LOYERS_CHARGES"]
    }
    
    response = requests.put(
        f"{API_BASE_URL}/api/compte-resultat/mappings/{mapping_id}",
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Mapping mis à jour")
        print(f"   Level 2: {data['level_2_values']}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_generate_compte_resultat():
    """Test POST /api/compte-resultat/generate"""
    print("\n" + "=" * 60)
    print("Test POST /api/compte-resultat/generate")
    print("=" * 60)
    
    request_data = {
        "year": 2024,
        "amortization_view_id": None
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/compte-resultat/generate",
        json=request_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Compte de résultat généré pour l'année {data['year']}")
        print(f"   Total produits: {data['total_produits']}")
        print(f"   Total charges: {data['total_charges']}")
        print(f"   Résultat exploitation: {data['resultat_exploitation']}")
        print(f"   Résultat net: {data['resultat_net']}")
        print(f"   Nombre de catégories: {len(data['categories'])}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_get_compte_resultat():
    """Test GET /api/compte-resultat"""
    print("\n" + "=" * 60)
    print("Test GET /api/compte-resultat")
    print("=" * 60)
    
    # Test avec une année spécifique
    response = requests.get(
        f"{API_BASE_URL}/api/compte-resultat",
        params={"year": 2024}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Comptes de résultat récupérés")
        print(f"   Nombre d'années: {len(data)}")
        if 2024 in data:
            cr = data[2024]
            print(f"   Année 2024:")
            print(f"     Total produits: {cr['total_produits']}")
            print(f"     Total charges: {cr['total_charges']}")
            print(f"     Résultat exploitation: {cr['resultat_exploitation']}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_get_compte_resultat_data():
    """Test GET /api/compte-resultat/data"""
    print("\n" + "=" * 60)
    print("Test GET /api/compte-resultat/data")
    print("=" * 60)
    
    response = requests.get(
        f"{API_BASE_URL}/api/compte-resultat/data",
        params={"year": 2024}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Données récupérées")
        print(f"   Total: {data['total']}")
        if data['data']:
            print(f"   Première donnée: {data['data'][0]}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_delete_mapping(mapping_id: int):
    """Test DELETE /api/compte-resultat/mappings/{id}"""
    print("\n" + "=" * 60)
    print(f"Test DELETE /api/compte-resultat/mappings/{mapping_id}")
    print("=" * 60)
    
    response = requests.delete(
        f"{API_BASE_URL}/api/compte-resultat/mappings/{mapping_id}"
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✅ Mapping supprimé")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Tests manuels des endpoints API compte de résultat")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré sur http://localhost:8000")
    print()
    
    results = []
    
    # Test 1: GET mappings
    results.append(("GET mappings", test_get_mappings()))
    
    # Test 2: CREATE mapping
    mapping_id = test_create_mapping()
    results.append(("CREATE mapping", mapping_id is not None))
    
    if mapping_id:
        # Test 3: UPDATE mapping
        results.append(("UPDATE mapping", test_update_mapping(mapping_id)))
    
    # Test 4: GENERATE compte de résultat
    results.append(("GENERATE compte de résultat", test_generate_compte_resultat()))
    
    # Test 5: GET compte de résultat
    results.append(("GET compte de résultat", test_get_compte_resultat()))
    
    # Test 6: GET compte de résultat data
    results.append(("GET compte de résultat data", test_get_compte_resultat_data()))
    
    if mapping_id:
        # Test 7: DELETE mapping
        results.append(("DELETE mapping", test_delete_mapping(mapping_id)))
    
    # Résumé
    print("\n" + "=" * 60)
    print("Résumé des tests")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Tous les tests sont passés !")
    else:
        print("❌ Certains tests ont échoué")
    print("=" * 60)

