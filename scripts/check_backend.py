#!/usr/bin/env python3
"""
Script de vérification du backend
Vérifie que le backend est démarré et accessible

⚠️ Before making changes, read: ../docs/workflow/BEST_PRACTICES.md

Run with: python3 scripts/check_backend.py
"""

import sys
import os
import requests
from urllib.parse import urljoin

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_URL = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')

def check_backend():
    """Vérifie que le backend est accessible."""
    print(f"🔍 Vérification du backend sur {API_URL}...")
    print()
    
    # Test 1: Endpoint de santé basique
    try:
        response = requests.get(f"{API_URL}/api/bilan/calculate?years=2021", timeout=2)
        if response.status_code == 200:
            print("✅ Backend accessible")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Réponse: {len(data)} année(s) calculée(s)")
            return True
        else:
            print(f"❌ Backend répond mais avec erreur: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend non accessible - Impossible de se connecter")
        print()
        print("💡 Pour démarrer le backend:")
        print("   cd backend && python3 -m uvicorn api.main:app --reload --port 8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend ne répond pas (timeout)")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = check_backend()
    sys.exit(0 if success else 1)

