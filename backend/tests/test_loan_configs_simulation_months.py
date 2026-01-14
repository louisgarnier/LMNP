"""
Test manuel pour le champ simulation_months dans loan configurations.

⚠️ Ce test nécessite que le serveur backend soit démarré sur http://localhost:8000

Pour exécuter :
    python3 backend/tests/test_loan_configs_simulation_months.py
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
    print("  TEST: simulation_months dans LoanConfig")
    print("=" * 60)
    
    # Test 1: Créer un LoanConfig avec simulation_months
    print_section("1. Création avec simulation_months")
    test_config = {
        "name": "Test Crédit Simulation",
        "credit_amount": 200000.0,
        "interest_rate": 2.5,
        "duration_years": 20,
        "initial_deferral_months": 0,
        "monthly_insurance": 25.50,
        "simulation_months": "[1, 50, 100, 150, 200]"
    }
    created = test_endpoint("POST", "/loan-configs", "Créer un crédit avec simulation_months", data=test_config)
    config_id = created.get("id") if created else None
    
    if not config_id:
        print("\n❌ Échec de la création, arrêt des tests")
        return
    
    # Vérifier simulation_months
    if created:
        sim_months = created.get("simulation_months")
        print(f"\n   ✅ simulation_months récupéré: {sim_months}")
        if sim_months != "[1, 50, 100, 150, 200]":
            print(f"   ⚠️  Valeur attendue: '[1, 50, 100, 150, 200]', valeur reçue: {sim_months}")
    
    # Test 2: Récupérer le LoanConfig créé
    print_section("2. Récupération avec simulation_months")
    retrieved = test_endpoint("GET", f"/loan-configs/{config_id}", "Récupérer le crédit créé")
    
    if retrieved:
        sim_months = retrieved.get("simulation_months")
        print(f"\n   ✅ simulation_months récupéré: {sim_months}")
        # Parser le JSON pour vérifier
        try:
            months_array = json.loads(sim_months) if sim_months else []
            print(f"   ✅ Parsing JSON réussi: {months_array}")
        except:
            print(f"   ⚠️  Erreur lors du parsing JSON")
    
    # Test 3: Mettre à jour simulation_months
    print_section("3. Mise à jour de simulation_months")
    update_data = {
        "simulation_months": "[1, 25, 50, 75, 100, 150, 200]"
    }
    updated = test_endpoint("PUT", f"/loan-configs/{config_id}", "Mettre à jour simulation_months", data=update_data)
    
    if updated:
        new_sim_months = updated.get("simulation_months")
        print(f"\n   ✅ simulation_months mis à jour: {new_sim_months}")
        try:
            months_array = json.loads(new_sim_months) if new_sim_months else []
            print(f"   ✅ Parsing JSON réussi: {months_array}")
            print(f"   ✅ Nombre de mensualités: {len(months_array)}")
        except:
            print(f"   ⚠️  Erreur lors du parsing JSON")
    
    # Test 4: Tester avec simulation_months = null
    print_section("4. Test avec simulation_months = null")
    test_config_null = {
        "name": "Test Crédit Simulation Null",
        "credit_amount": 150000.0,
        "interest_rate": 3.0,
        "duration_years": 15,
        "initial_deferral_months": 0,
        "monthly_insurance": 0.0
        # simulation_months non spécifié (devrait être null)
    }
    created_null = test_endpoint("POST", "/loan-configs", "Créer un crédit sans simulation_months (devrait être null)", data=test_config_null)
    config_id_null = created_null.get("id") if created_null else None
    
    if created_null:
        sim_months_null = created_null.get("simulation_months")
        print(f"\n   ✅ simulation_months par défaut: {sim_months_null}")
        if sim_months_null is not None:
            print(f"   ⚠️  Valeur attendue: null, valeur reçue: {sim_months_null}")
    
    # Test 5: Liste des LoanConfigs avec simulation_months
    print_section("5. Liste des crédits avec simulation_months")
    list_response = test_endpoint("GET", "/loan-configs", "Récupérer la liste des crédits")
    
    if list_response and "items" in list_response:
        items = list_response["items"]
        print(f"\n   ✅ {len(items)} crédit(s) trouvé(s)")
        for item in items[:3]:  # Afficher les 3 premiers
            name = item.get("name", "N/A")
            sim_months = item.get("simulation_months", "N/A")
            print(f"      - {name}: simulation_months = {sim_months}")
    
    # Test 6: Tester avec un JSON invalide (devrait être accepté comme string, validation côté frontend)
    print_section("6. Test avec JSON personnalisé")
    update_custom = {
        "simulation_months": "[1, 12, 24, 36, 48, 60]"
    }
    updated_custom = test_endpoint("PUT", f"/loan-configs/{config_id}", "Mettre à jour avec mensualités personnalisées", data=update_custom)
    
    if updated_custom:
        custom_sim_months = updated_custom.get("simulation_months")
        print(f"\n   ✅ simulation_months personnalisé: {custom_sim_months}")
        try:
            months_array = json.loads(custom_sim_months) if custom_sim_months else []
            print(f"   ✅ Parsing JSON réussi: {months_array}")
            print(f"   ✅ Mensualités: {months_array}")
        except:
            print(f"   ⚠️  Erreur lors du parsing JSON")
    
    # Nettoyage: Supprimer les crédits de test
    print_section("7. Nettoyage - Suppression des crédits de test")
    if config_id:
        test_endpoint("DELETE", f"/loan-configs/{config_id}", f"Supprimer le crédit de test {config_id}")
    if config_id_null:
        test_endpoint("DELETE", f"/loan-configs/{config_id_null}", f"Supprimer le crédit de test {config_id_null}")
    
    print("\n" + "=" * 60)
    print("  TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    main()
