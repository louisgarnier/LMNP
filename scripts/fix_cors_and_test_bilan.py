#!/usr/bin/env python3
"""
Script pour vérifier et corriger les problèmes CORS avec /api/bilan/calculate

⚠️ Before making changes, read: ../docs/workflow/BEST_PRACTICES.md

Run with: python3 scripts/fix_cors_and_test_bilan.py
"""

import sys
import os
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_URL = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')

def test_endpoint_with_cors(endpoint, description):
    """Test un endpoint avec vérification CORS."""
    print(f"\n🔍 Test: {description}")
    print(f"   Endpoint: {endpoint}")
    print("-" * 80)
    
    try:
        # Test avec Origin header (comme le navigateur)
        response = requests.get(
            f"{API_URL}{endpoint}",
            headers={'Origin': 'http://localhost:3000'},
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        
        # Vérifier les headers CORS
        cors_headers = {
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'access-control-allow-credentials': response.headers.get('access-control-allow-credentials'),
            'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
        }
        
        print(f"   Headers CORS:")
        for key, value in cors_headers.items():
            if value:
                print(f"     ✅ {key}: {value}")
            else:
                print(f"     ❌ {key}: MANQUANT")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Données reçues: {len(data)} clé(s)")
            return True
        else:
            print(f"   ❌ Erreur: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Backend non accessible sur {API_URL}")
        print(f"   💡 Démarrer le backend: cd backend && python3 -m uvicorn api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def main():
    """Fonction principale."""
    print("=" * 80)
    print("VÉRIFICATION CORS ET TEST /api/bilan/calculate")
    print("=" * 80)
    
    # Test 1: Endpoint bilan/calculate
    test1 = test_endpoint_with_cors(
        "/api/bilan/calculate?years=2021",
        "Bilan /calculate"
    )
    
    # Test 2: Endpoint compte-resultat/calculate (pour comparaison)
    test2 = test_endpoint_with_cors(
        "/api/compte-resultat/calculate?years=2021",
        "Compte de résultat /calculate (comparaison)"
    )
    
    # Test 3: Endpoint bilan/mappings (pour vérifier que le backend fonctionne)
    test3 = test_endpoint_with_cors(
        "/api/bilan/mappings",
        "Bilan /mappings (vérification backend)"
    )
    
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"  Bilan /calculate: {'✅ OK' if test1 else '❌ ÉCHEC'}")
    print(f"  Compte de résultat /calculate: {'✅ OK' if test2 else '❌ ÉCHEC'}")
    print(f"  Bilan /mappings: {'✅ OK' if test3 else '❌ ÉCHEC'}")
    print()
    
    if not test1 and test2 and test3:
        print("❌ PROBLÈME IDENTIFIÉ:")
        if not test1 and test2:
            print("   Le endpoint /api/bilan/calculate a un problème CORS")
            print("   alors que /api/compte-resultat/calculate fonctionne.")
            print("   → Vérifier que le backend est bien démarré et redémarré")
        elif not test3:
            print("   Le backend n'est pas accessible")
            print("   → Démarrer le backend: cd backend && python3 -m uvicorn api.main:app --reload --port 8000")
    else:
        print("✅ Tous les tests passent - Le problème vient peut-être du timing")
        print("   (le backend redémarre ou il y a un délai)")


if __name__ == "__main__":
    main()

