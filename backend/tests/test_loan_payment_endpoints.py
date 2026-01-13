"""
Test manuel pour les endpoints API de loan payments.

⚠️ Ce test nécessite que le serveur backend soit démarré sur http://localhost:8000

Pour exécuter :
    python3 backend/tests/test_loan_payment_endpoints.py
"""

import sys
import requests
from datetime import date
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
            if data and isinstance(data, dict):
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", data=data)
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
                    if isinstance(result, dict) and len(result) < 10:
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
    print("  TEST DES ENDPOINTS LOAN PAYMENTS")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré sur http://localhost:8000")
    
    # Test 1: GET /api/loan-payments (liste vide au début)
    print_section("1. GET /api/loan-payments - Liste des mensualités")
    response = test_endpoint("GET", "/loan-payments", "Récupérer la liste des mensualités")
    
    # Test 2: POST /api/loan-payments - Créer une mensualité
    print_section("2. POST /api/loan-payments - Créer une mensualité")
    payment_data = {
        "date": "2024-01-01",
        "capital": 1000.0,
        "interest": 200.0,
        "insurance": 50.0,
        "total": 1250.0,
        "loan_name": "Prêt principal"
    }
    response = test_endpoint("POST", "/loan-payments", "Créer une mensualité", data=payment_data)
    payment_id = None
    if response and response.status_code == 201:
        result = response.json()
        payment_id = result.get("id")
        print(f"   💾 ID créé: {payment_id}")
    
    # Test 3: GET /api/loan-payments/{id} - Récupérer une mensualité
    if payment_id:
        print_section(f"3. GET /api/loan-payments/{payment_id} - Récupérer une mensualité")
        test_endpoint("GET", f"/loan-payments/{payment_id}", f"Récupérer la mensualité {payment_id}")
    
    # Test 4: GET /api/loan-payments - Liste avec filtres
    print_section("4. GET /api/loan-payments - Liste avec filtres")
    test_endpoint("GET", "/loan-payments", "Liste filtrée par loan_name", params={"loan_name": "Prêt principal"})
    test_endpoint("GET", "/loan-payments", "Liste filtrée par date", params={"start_date": "2024-01-01", "end_date": "2024-12-31"})
    
    # Test 5: PUT /api/loan-payments/{id} - Mettre à jour
    if payment_id:
        print_section(f"5. PUT /api/loan-payments/{payment_id} - Mettre à jour")
        update_data = {
            "capital": 1500.0,
            "interest": 250.0
        }
        test_endpoint("PUT", f"/loan-payments/{payment_id}", f"Mettre à jour la mensualité {payment_id}", data=update_data)
    
    # Test 6: DELETE /api/loan-payments/{id} - Supprimer
    if payment_id:
        print_section(f"6. DELETE /api/loan-payments/{payment_id} - Supprimer")
        test_endpoint("DELETE", f"/loan-payments/{payment_id}", f"Supprimer la mensualité {payment_id}")
        
        # Vérifier que c'est bien supprimé
        print("\n   Vérification de la suppression...")
        response = test_endpoint("GET", f"/loan-payments/{payment_id}", "Tenter de récupérer la mensualité supprimée")
        if response and response.status_code == 404:
            print("   ✅ La mensualité a bien été supprimée")
    
    # Test 7: POST /api/loan-payments/preview - Preview (nécessite un fichier)
    print_section("7. POST /api/loan-payments/preview - Preview Excel")
    print("   ⚠️  Ce test nécessite un fichier Excel. Testez manuellement avec:")
    print("   curl -X POST http://localhost:8000/api/loan-payments/preview -F 'file=@chemin/vers/fichier.xlsx'")
    
    # Test 8: POST /api/loan-payments/import - Import (nécessite un fichier)
    print_section("8. POST /api/loan-payments/import - Import Excel")
    print("   ⚠️  Ce test nécessite un fichier Excel. Testez manuellement avec:")
    print("   curl -X POST 'http://localhost:8000/api/loan-payments/import?loan_name=Prêt principal' -F 'file=@chemin/vers/fichier.xlsx'")
    
    print("\n" + "=" * 60)
    print("  ✅ TESTS TERMINÉS")
    print("=" * 60)
    print("\n💡 Pour tester preview et import, utilisez un fichier Excel avec:")
    print("   - Colonne 'annee' avec valeurs: 'capital', 'interets', 'assurance cred', 'total'")
    print("   - Colonnes années: 2021, 2022, 2023, etc.")
    print("   - Chaque ligne = un type de montant pour toutes les années")

if __name__ == "__main__":
    main()
