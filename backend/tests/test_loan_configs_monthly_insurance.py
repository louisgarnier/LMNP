"""
Test manuel pour le champ monthly_insurance dans loan configurations.

⚠️ Ce test nécessite que le serveur backend soit démarré sur http://localhost:8000

Pour exécuter :
    python3 backend/tests/test_loan_configs_monthly_insurance.py
"""

import sys
import requests
import json
from datetime import date

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
            return response.json() if response.content else None
        else:
            print(f"   ❌ Erreur")
            try:
                error = response.json()
                print(f"   Détail: {error.get('detail', response.text)}")
            except:
                print(f"   Détail: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur de connexion - Le serveur backend est-il démarré ?")
        return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("  TEST: monthly_insurance dans LoanConfig")
    print("=" * 60)
    
    # Test 1: Créer un LoanConfig avec monthly_insurance
    print_section("1. Création avec monthly_insurance")
    test_config = {
        "name": "Test Crédit Assurance",
        "credit_amount": 200000.0,
        "interest_rate": 2.5,
        "duration_years": 20,
        "initial_deferral_months": 0,
        "monthly_insurance": 25.50
    }
    created = test_endpoint("POST", "/loan-configs", "Créer un crédit avec monthly_insurance = 25.50", data=test_config)
    config_id = created.get("id") if created else None
    
    if not config_id:
        print("\n❌ Échec de la création, arrêt des tests")
        return
    
    # Test 2: Récupérer le LoanConfig créé
    print_section("2. Récupération avec monthly_insurance")
    retrieved = test_endpoint("GET", f"/loan-configs/{config_id}", "Récupérer le crédit créé")
    
    if retrieved:
        monthly_insurance = retrieved.get("monthly_insurance")
        print(f"\n   ✅ monthly_insurance récupéré: {monthly_insurance}")
        if monthly_insurance != 25.50:
            print(f"   ⚠️  Valeur attendue: 25.50, valeur reçue: {monthly_insurance}")
    
    # Test 3: Mettre à jour monthly_insurance
    print_section("3. Mise à jour de monthly_insurance")
    update_data = {
        "monthly_insurance": 30.75
    }
    updated = test_endpoint("PUT", f"/loan-configs/{config_id}", "Mettre à jour monthly_insurance à 30.75", data=update_data)
    
    if updated:
        new_insurance = updated.get("monthly_insurance")
        print(f"\n   ✅ monthly_insurance mis à jour: {new_insurance}")
        if new_insurance != 30.75:
            print(f"   ⚠️  Valeur attendue: 30.75, valeur reçue: {new_insurance}")
    
    # Test 4: Tester avec monthly_insurance = 0
    print_section("4. Test avec monthly_insurance = 0")
    test_config_zero = {
        "name": "Test Crédit Assurance Zero",
        "credit_amount": 150000.0,
        "interest_rate": 3.0,
        "duration_years": 15,
        "initial_deferral_months": 0,
        "monthly_insurance": 0.0
    }
    created_zero = test_endpoint("POST", "/loan-configs", "Créer un crédit avec monthly_insurance = 0", data=test_config_zero)
    config_id_zero = created_zero.get("id") if created_zero else None
    
    if created_zero:
        insurance_zero = created_zero.get("monthly_insurance")
        print(f"\n   ✅ monthly_insurance = 0 créé: {insurance_zero}")
    
    # Test 5: Tester sans spécifier monthly_insurance (doit utiliser la valeur par défaut 0.0)
    print_section("5. Test sans monthly_insurance (valeur par défaut)")
    test_config_default = {
        "name": "Test Crédit Assurance Default",
        "credit_amount": 100000.0,
        "interest_rate": 2.0,
        "duration_years": 10,
        "initial_deferral_months": 0
        # monthly_insurance non spécifié
    }
    created_default = test_endpoint("POST", "/loan-configs", "Créer un crédit sans monthly_insurance (devrait être 0.0)", data=test_config_default)
    
    if created_default:
        insurance_default = created_default.get("monthly_insurance")
        print(f"\n   ✅ monthly_insurance par défaut: {insurance_default}")
        if insurance_default != 0.0:
            print(f"   ⚠️  Valeur attendue: 0.0, valeur reçue: {insurance_default}")
    
    # Test 6: Liste des LoanConfigs avec monthly_insurance
    print_section("6. Liste des crédits avec monthly_insurance")
    list_response = test_endpoint("GET", "/loan-configs", "Récupérer la liste des crédits")
    
    if list_response and "items" in list_response:
        items = list_response["items"]
        print(f"\n   ✅ {len(items)} crédit(s) trouvé(s)")
        for item in items[:3]:  # Afficher les 3 premiers
            name = item.get("name", "N/A")
            insurance = item.get("monthly_insurance", "N/A")
            print(f"      - {name}: monthly_insurance = {insurance}")
    
    # Nettoyage: Supprimer les crédits de test
    print_section("7. Nettoyage - Suppression des crédits de test")
    if config_id:
        test_endpoint("DELETE", f"/loan-configs/{config_id}", f"Supprimer le crédit de test {config_id}")
    if config_id_zero:
        test_endpoint("DELETE", f"/loan-configs/{config_id_zero}", f"Supprimer le crédit de test {config_id_zero}")
    if created_default and created_default.get("id"):
        test_endpoint("DELETE", f"/loan-configs/{created_default['id']}", f"Supprimer le crédit de test {created_default['id']}")
    
    print("\n" + "=" * 60)
    print("  TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    main()
