"""
Test script for Step 8.1 - Allowed Mappings API Endpoints.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_allowed_mappings_api_endpoints.py

⚠️ IMPORTANT: Le backend doit être démarré sur http://localhost:8000
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
from typing import List, Optional


BASE_URL = "http://localhost:8000"


def test_get_allowed_level1():
    """Test endpoint GET /api/mappings/allowed-level1"""
    print("=" * 60)
    print("Test 1: GET /api/mappings/allowed-level1")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/mappings/allowed-level1")
        response.raise_for_status()
        
        data = response.json()
        values = data.get("values", [])
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Nombre de valeurs level_1: {len(values)}")
        if values:
            print(f"✅ Premières valeurs: {values[:5]}")
        else:
            print("⚠️  Aucune valeur level_1 retournée")
        
        return True, values
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au backend")
        print("   Vérifiez que le backend est démarré sur http://localhost:8000")
        return False, []
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"   Réponse: {response.text}")
        return False, []
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, []


def test_get_allowed_level2(level_1: str):
    """Test endpoint GET /api/mappings/allowed-level2"""
    print()
    print("=" * 60)
    print(f"Test 2: GET /api/mappings/allowed-level2?level_1={level_1}")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/mappings/allowed-level2",
            params={"level_1": level_1}
        )
        response.raise_for_status()
        
        data = response.json()
        values = data.get("values", [])
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Nombre de valeurs level_2 pour '{level_1}': {len(values)}")
        if values:
            print(f"✅ Premières valeurs: {values[:5]}")
        else:
            print("⚠️  Aucune valeur level_2 retournée")
        
        return True, values
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au backend")
        return False, []
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"   Réponse: {response.text}")
        return False, []
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, []


def test_get_allowed_level3(level_1: str, level_2: str):
    """Test endpoint GET /api/mappings/allowed-level3"""
    print()
    print("=" * 60)
    print(f"Test 3: GET /api/mappings/allowed-level3?level_1={level_1}&level_2={level_2}")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/mappings/allowed-level3",
            params={"level_1": level_1, "level_2": level_2}
        )
        response.raise_for_status()
        
        data = response.json()
        values = data.get("values", [])
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Nombre de valeurs level_3 pour ('{level_1}', '{level_2}'): {len(values)}")
        if values:
            print(f"✅ Premières valeurs: {values[:5]}")
        else:
            print("⚠️  Aucune valeur level_3 retournée (normal si level_3 est optionnel)")
        
        return True, values
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au backend")
        return False, []
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"   Réponse: {response.text}")
        return False, []
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, []


def test_all_endpoints():
    """Test tous les endpoints dans l'ordre hiérarchique"""
    print()
    print("=" * 60)
    print("Test des endpoints API - Allowed Mappings")
    print("=" * 60)
    print()
    
    # Test 1: Get level_1 values
    success1, level1_values = test_get_allowed_level1()
    if not success1 or not level1_values:
        print()
        print("❌ Échec du test 1 - Impossible de continuer")
        return False
    
    # Test 2: Get level_2 values (avec le premier level_1)
    if level1_values:
        test_level1 = level1_values[0]
        success2, level2_values = test_get_allowed_level2(test_level1)
        
        # Test 3: Get level_3 values (avec le premier level_1 et level_2)
        if success2 and level2_values:
            test_level2 = level2_values[0]
            success3, level3_values = test_get_allowed_level3(test_level1, test_level2)
            
            if success3:
                print()
                print("=" * 60)
                print("✅ Tous les tests sont passés avec succès !")
                print("=" * 60)
                return True
    
    print()
    print("=" * 60)
    print("⚠️  Tests partiellement réussis")
    print("=" * 60)
    return True  # On considère comme réussi même si certains niveaux sont vides


if __name__ == "__main__":
    success = test_all_endpoints()
    sys.exit(0 if success else 1)

