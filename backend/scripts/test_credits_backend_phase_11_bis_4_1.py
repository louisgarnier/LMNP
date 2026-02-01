"""
Test d'isolation backend pour l'onglet Crédit (Phase 11).

Ce script teste l'isolation complète des données de crédit entre différentes propriétés.
Il vérifie que chaque propriété ne peut accéder qu'à ses propres configurations de crédit et mensualités.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def print_section(title: str):
    """Affiche une section avec un titre."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_test(test_name: str):
    """Affiche le nom d'un test."""
    print(f"🧪 Test: {test_name}")

def print_success(message: str):
    """Affiche un message de succès."""
    print(f"✅ {message}")

def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"❌ ERREUR: {message}")

def print_info(message: str):
    """Affiche un message d'information."""
    print(f"ℹ️  {message}")

def create_property(name: str) -> Optional[int]:
    """Crée une propriété et retourne son ID."""
    try:
        response = requests.post(
            f"{API_BASE}/properties",
            json={"name": name, "address": f"Adresse de {name}"}
        )
        if response.status_code in [200, 201]:
            prop_data = response.json()
            prop_id = prop_data.get("id")
            print_success(f"Propriété '{name}' créée avec ID={prop_id}")
            return prop_id
        else:
            print_error(f"Impossible de créer {name}: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception lors de la création de {name}: {e}")
        return None

def get_property_id_by_name(name: str) -> Optional[int]:
    """Récupère l'ID d'une propriété par son nom."""
    try:
        response = requests.get(f"{API_BASE}/properties")
        if response.status_code == 200:
            properties = response.json().get("items", [])
            for prop in properties:
                if prop.get("name") == name:
                    return prop.get("id")
        return None
    except Exception as e:
        print_error(f"Exception lors de la récupération de la propriété: {e}")
        return None

def test_loan_configs_isolation():
    """Test l'isolation des configurations de crédit."""
    print_section("TEST D'ISOLATION - Configurations de Crédit")
    
    # Créer 2 propriétés avec timestamp pour éviter les conflits
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prop1_name = f"Test Property Credits 1_{timestamp}"
    prop2_name = f"Test Property Credits 2_{timestamp}"
    
    prop1_id = create_property(prop1_name)
    prop2_id = create_property(prop2_name)
    
    if not prop1_id or not prop2_id:
        print_error("Impossible de créer les propriétés de test")
        return False
    
    try:
        # Test 1: Créer des configurations pour chaque propriété
        print_test("Création de configurations de crédit pour chaque propriété")
        
        config1_data = {
            "name": "Prêt principal Prop1",
            "credit_amount": 200000.0,
            "interest_rate": 2.5,
            "duration_years": 20,
            "initial_deferral_months": 0,
            "loan_start_date": "2020-01-01",
            "loan_end_date": "2040-01-01",
            "monthly_insurance": 50.0,
            "property_id": prop1_id
        }
        
        config2_data = {
            "name": "Prêt principal Prop2",
            "credit_amount": 300000.0,
            "interest_rate": 3.0,
            "duration_years": 25,
            "initial_deferral_months": 0,
            "loan_start_date": "2021-01-01",
            "loan_end_date": "2046-01-01",
            "monthly_insurance": 75.0,
            "property_id": prop2_id
        }
        
        response1 = requests.post(f"{API_BASE}/loan-configs", json=config1_data)
        if response1.status_code not in [200, 201]:
            print_error(f"Impossible de créer config1: {response1.status_code} {response1.text}")
            return False
        config1 = response1.json()
        config1_id = config1.get("id")
        print_success(f"Config créée pour prop1: ID={config1_id}, name={config1.get('name')}")
        
        response2 = requests.post(f"{API_BASE}/loan-configs", json=config2_data)
        if response2.status_code not in [200, 201]:
            print_error(f"Impossible de créer config2: {response2.status_code} {response2.text}")
            return False
        config2 = response2.json()
        config2_id = config2.get("id")
        print_success(f"Config créée pour prop2: ID={config2_id}, name={config2.get('name')}")
        
        # Test 2: Vérifier l'isolation - prop1 ne doit voir que sa config
        print_test("Vérification isolation - prop1 ne doit voir que sa config")
        response = requests.get(f"{API_BASE}/loan-configs?property_id={prop1_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-configs échoué: {response.status_code}")
            return False
        
        configs_prop1 = response.json().get("items", [])
        config_ids_prop1 = [c.get("id") for c in configs_prop1]
        
        if config1_id not in config_ids_prop1:
            print_error(f"Config1 (ID={config1_id}) non trouvée dans les configs de prop1")
            return False
        
        if config2_id in config_ids_prop1:
            print_error(f"Config2 (ID={config2_id}) trouvée dans les configs de prop1 (isolation violée!)")
            return False
        
        print_success(f"Prop1 voit {len(configs_prop1)} config(s), dont config1 (ID={config1_id})")
        print_info(f"Configs de prop1: {[c.get('name') for c in configs_prop1]}")
        
        # Test 3: Vérifier l'isolation - prop2 ne doit voir que sa config
        print_test("Vérification isolation - prop2 ne doit voir que sa config")
        response = requests.get(f"{API_BASE}/loan-configs?property_id={prop2_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-configs échoué: {response.status_code}")
            return False
        
        configs_prop2 = response.json().get("items", [])
        config_ids_prop2 = [c.get("id") for c in configs_prop2]
        
        if config2_id not in config_ids_prop2:
            print_error(f"Config2 (ID={config2_id}) non trouvée dans les configs de prop2")
            return False
        
        if config1_id in config_ids_prop2:
            print_error(f"Config1 (ID={config1_id}) trouvée dans les configs de prop2 (isolation violée!)")
            return False
        
        print_success(f"Prop2 voit {len(configs_prop2)} config(s), dont config2 (ID={config2_id})")
        print_info(f"Configs de prop2: {[c.get('name') for c in configs_prop2]}")
        
        # Test 4: Test GET par ID avec isolation
        print_test("Test GET par ID avec isolation")
        response = requests.get(f"{API_BASE}/loan-configs/{config1_id}?property_id={prop1_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-configs/{config1_id} échoué: {response.status_code}")
            return False
        print_success(f"Prop1 peut accéder à sa config (ID={config1_id})")
        
        # Test cross-property access (doit retourner 404)
        response = requests.get(f"{API_BASE}/loan-configs/{config1_id}?property_id={prop2_id}")
        if response.status_code != 404:
            print_error(f"Prop2 peut accéder à la config de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas accéder à la config de prop1 (404 comme attendu)")
        
        # Test 5: Test UPDATE avec isolation
        print_test("Test UPDATE avec isolation")
        update_data = {"credit_amount": 250000.0}
        response = requests.put(
            f"{API_BASE}/loan-configs/{config1_id}?property_id={prop1_id}",
            json=update_data
        )
        if response.status_code != 200:
            print_error(f"PUT /api/loan-configs/{config1_id} échoué: {response.status_code}")
            return False
        updated_config = response.json()
        if updated_config.get("credit_amount") != 250000.0:
            print_error(f"Credit amount non mis à jour: {updated_config.get('credit_amount')}")
            return False
        print_success(f"Prop1 peut mettre à jour sa config (credit_amount={updated_config.get('credit_amount')})")
        
        # Test cross-property update (doit retourner 404)
        response = requests.put(
            f"{API_BASE}/loan-configs/{config1_id}?property_id={prop2_id}",
            json=update_data
        )
        if response.status_code != 404:
            print_error(f"Prop2 peut mettre à jour la config de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas mettre à jour la config de prop1 (404 comme attendu)")
        
        # Test 6: Afficher les crédits actifs par propriété
        print_test("AFFICHAGE DES CRÉDITS ACTIFS PAR PROPRIÉTÉ")
        print_info(f"\n📊 PROPRIÉTÉ 1 (ID={prop1_id}, Name={prop1_name}):")
        response = requests.get(f"{API_BASE}/loan-configs?property_id={prop1_id}")
        if response.status_code == 200:
            configs = response.json().get("items", [])
            if configs:
                for config in configs:
                    print(f"   - ID: {config.get('id')}, Name: {config.get('name')}, Montant: {config.get('credit_amount')} €, Taux: {config.get('interest_rate')}%")
            else:
                print("   Aucun crédit configuré")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
        
        print_info(f"\n📊 PROPRIÉTÉ 2 (ID={prop2_id}, Name={prop2_name}):")
        response = requests.get(f"{API_BASE}/loan-configs?property_id={prop2_id}")
        if response.status_code == 200:
            configs = response.json().get("items", [])
            if configs:
                for config in configs:
                    print(f"   - ID: {config.get('id')}, Name: {config.get('name')}, Montant: {config.get('credit_amount')} €, Taux: {config.get('interest_rate')}%")
            else:
                print("   Aucun crédit configuré")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
        
        # Test 7: Test DELETE avec isolation
        print_test("Test DELETE avec isolation")
        # Créer une config supplémentaire pour prop1 pour tester la suppression
        config3_data = {
            "name": "Prêt secondaire Prop1",
            "credit_amount": 50000.0,
            "interest_rate": 2.0,
            "duration_years": 10,
            "initial_deferral_months": 0,
            "property_id": prop1_id
        }
        response = requests.post(f"{API_BASE}/loan-configs", json=config3_data)
        if response.status_code not in [200, 201]:
            print_error(f"Impossible de créer config3: {response.status_code}")
            return False
        config3_id = response.json().get("id")
        
        # Prop1 peut supprimer sa config
        response = requests.delete(f"{API_BASE}/loan-configs/{config3_id}?property_id={prop1_id}")
        if response.status_code != 204:
            print_error(f"DELETE /api/loan-configs/{config3_id} échoué: {response.status_code}")
            return False
        print_success(f"Prop1 peut supprimer sa config (ID={config3_id})")
        
        # Prop2 ne peut pas supprimer la config de prop1
        response = requests.delete(f"{API_BASE}/loan-configs/{config1_id}?property_id={prop2_id}")
        if response.status_code != 404:
            print_error(f"Prop2 peut supprimer la config de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas supprimer la config de prop1 (404 comme attendu)")
        
        # Nettoyage: supprimer les configs de test
        print_test("Nettoyage")
        requests.delete(f"{API_BASE}/loan-configs/{config1_id}?property_id={prop1_id}")
        requests.delete(f"{API_BASE}/loan-configs/{config2_id}?property_id={prop2_id}")
        print_success("Configs de test supprimées")
        
        return True
        
    except Exception as e:
        print_error(f"Exception lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_loan_payments_isolation():
    """Test l'isolation des mensualités de crédit."""
    print_section("TEST D'ISOLATION - Mensualités de Crédit")
    
    # Créer 2 propriétés avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prop1_name = f"Test Property Payments 1_{timestamp}"
    prop2_name = f"Test Property Payments 2_{timestamp}"
    
    prop1_id = create_property(prop1_name)
    prop2_id = create_property(prop2_name)
    
    if not prop1_id or not prop2_id:
        print_error("Impossible de créer les propriétés de test")
        return False
    
    try:
        # Créer des configurations pour chaque propriété
        config1_data = {
            "name": "Prêt principal Prop1",
            "credit_amount": 200000.0,
            "interest_rate": 2.5,
            "duration_years": 20,
            "initial_deferral_months": 0,
            "property_id": prop1_id
        }
        
        config2_data = {
            "name": "Prêt principal Prop2",
            "credit_amount": 300000.0,
            "interest_rate": 3.0,
            "duration_years": 25,
            "initial_deferral_months": 0,
            "property_id": prop2_id
        }
        
        response1 = requests.post(f"{API_BASE}/loan-configs", json=config1_data)
        config1_id = response1.json().get("id")
        loan_name_prop1 = config1_data["name"]
        
        response2 = requests.post(f"{API_BASE}/loan-configs", json=config2_data)
        config2_id = response2.json().get("id")
        loan_name_prop2 = config2_data["name"]
        
        # Test 1: Créer des mensualités pour chaque propriété
        print_test("Création de mensualités pour chaque propriété")
        
        payment1_data = {
            "date": "2024-01-01",
            "capital": 500.0,
            "interest": 400.0,
            "insurance": 50.0,
            "total": 950.0,
            "loan_name": loan_name_prop1,
            "property_id": prop1_id
        }
        
        payment2_data = {
            "date": "2024-01-01",
            "capital": 600.0,
            "interest": 500.0,
            "insurance": 75.0,
            "total": 1175.0,
            "loan_name": loan_name_prop2,
            "property_id": prop2_id
        }
        
        response1 = requests.post(f"{API_BASE}/loan-payments", json=payment1_data)
        if response1.status_code not in [200, 201]:
            print_error(f"Impossible de créer payment1: {response1.status_code} {response1.text}")
            return False
        payment1 = response1.json()
        payment1_id = payment1.get("id")
        print_success(f"Payment créé pour prop1: ID={payment1_id}, date={payment1.get('date')}")
        
        response2 = requests.post(f"{API_BASE}/loan-payments", json=payment2_data)
        if response2.status_code not in [200, 201]:
            print_error(f"Impossible de créer payment2: {response2.status_code} {response2.text}")
            return False
        payment2 = response2.json()
        payment2_id = payment2.get("id")
        print_success(f"Payment créé pour prop2: ID={payment2_id}, date={payment2.get('date')}")
        
        # Test 2: Vérifier l'isolation - prop1 ne doit voir que ses payments
        print_test("Vérification isolation - prop1 ne doit voir que ses payments")
        response = requests.get(f"{API_BASE}/loan-payments?property_id={prop1_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-payments échoué: {response.status_code}")
            return False
        
        payments_prop1 = response.json().get("items", [])
        payment_ids_prop1 = [p.get("id") for p in payments_prop1]
        
        if payment1_id not in payment_ids_prop1:
            print_error(f"Payment1 (ID={payment1_id}) non trouvé dans les payments de prop1")
            return False
        
        if payment2_id in payment_ids_prop1:
            print_error(f"Payment2 (ID={payment2_id}) trouvé dans les payments de prop1 (isolation violée!)")
            return False
        
        print_success(f"Prop1 voit {len(payments_prop1)} payment(s), dont payment1 (ID={payment1_id})")
        
        # Test 3: Vérifier l'isolation - prop2 ne doit voir que ses payments
        print_test("Vérification isolation - prop2 ne doit voir que ses payments")
        response = requests.get(f"{API_BASE}/loan-payments?property_id={prop2_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-payments échoué: {response.status_code}")
            return False
        
        payments_prop2 = response.json().get("items", [])
        payment_ids_prop2 = [p.get("id") for p in payments_prop2]
        
        if payment2_id not in payment_ids_prop2:
            print_error(f"Payment2 (ID={payment2_id}) non trouvé dans les payments de prop2")
            return False
        
        if payment1_id in payment_ids_prop2:
            print_error(f"Payment1 (ID={payment1_id}) trouvé dans les payments de prop2 (isolation violée!)")
            return False
        
        print_success(f"Prop2 voit {len(payments_prop2)} payment(s), dont payment2 (ID={payment2_id})")
        
        # Test 4: Test GET par ID avec isolation
        print_test("Test GET par ID avec isolation")
        response = requests.get(f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop1_id}")
        if response.status_code != 200:
            print_error(f"GET /api/loan-payments/{payment1_id} échoué: {response.status_code}")
            return False
        print_success(f"Prop1 peut accéder à son payment (ID={payment1_id})")
        
        # Test cross-property access (doit retourner 404)
        response = requests.get(f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop2_id}")
        if response.status_code != 404:
            print_error(f"Prop2 peut accéder au payment de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas accéder au payment de prop1 (404 comme attendu)")
        
        # Test 5: Test UPDATE avec isolation
        print_test("Test UPDATE avec isolation")
        update_data = {"capital": 550.0, "total": 1000.0}
        response = requests.put(
            f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop1_id}",
            json=update_data
        )
        if response.status_code != 200:
            print_error(f"PUT /api/loan-payments/{payment1_id} échoué: {response.status_code}")
            return False
        print_success(f"Prop1 peut mettre à jour son payment (ID={payment1_id})")
        
        # Test cross-property update (doit retourner 404)
        response = requests.put(
            f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop2_id}",
            json=update_data
        )
        if response.status_code != 404:
            print_error(f"Prop2 peut mettre à jour le payment de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas mettre à jour le payment de prop1 (404 comme attendu)")
        
        # Test 6: Test DELETE avec isolation
        print_test("Test DELETE avec isolation")
        # Créer un payment supplémentaire pour prop1
        payment3_data = {
            "date": "2024-02-01",
            "capital": 500.0,
            "interest": 400.0,
            "insurance": 50.0,
            "total": 950.0,
            "loan_name": loan_name_prop1,
            "property_id": prop1_id
        }
        response = requests.post(f"{API_BASE}/loan-payments", json=payment3_data)
        payment3_id = response.json().get("id")
        
        # Prop1 peut supprimer son payment
        response = requests.delete(f"{API_BASE}/loan-payments/{payment3_id}?property_id={prop1_id}")
        if response.status_code != 204:
            print_error(f"DELETE /api/loan-payments/{payment3_id} échoué: {response.status_code}")
            return False
        print_success(f"Prop1 peut supprimer son payment (ID={payment3_id})")
        
        # Prop2 ne peut pas supprimer le payment de prop1
        response = requests.delete(f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop2_id}")
        if response.status_code != 404:
            print_error(f"Prop2 peut supprimer le payment de prop1 (isolation violée! Status={response.status_code})")
            return False
        print_success(f"Prop2 ne peut pas supprimer le payment de prop1 (404 comme attendu)")
        
        # Nettoyage
        print_test("Nettoyage")
        requests.delete(f"{API_BASE}/loan-payments/{payment1_id}?property_id={prop1_id}")
        requests.delete(f"{API_BASE}/loan-payments/{payment2_id}?property_id={prop2_id}")
        requests.delete(f"{API_BASE}/loan-configs/{config1_id}?property_id={prop1_id}")
        requests.delete(f"{API_BASE}/loan-configs/{config2_id}?property_id={prop2_id}")
        print_success("Payments et configs de test supprimés")
        
        return True
        
    except Exception as e:
        print_error(f"Exception lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_credits_by_property():
    """Test qui affiche tous les crédits actifs pour chaque propriété."""
    print_section("AFFICHAGE DES CRÉDITS ACTIFS PAR PROPRIÉTÉ")
    
    try:
        # Récupérer toutes les propriétés
        response = requests.get(f"{API_BASE}/properties")
        if response.status_code != 200:
            print_error(f"GET /api/properties échoué: {response.status_code}")
            return False
        
        properties = response.json().get("items", [])
        print_info(f"Nombre de propriétés trouvées: {len(properties)}\n")
        
        if not properties:
            print_info("Aucune propriété trouvée dans la base de données")
            return True
        
        # Pour chaque propriété, afficher ses crédits
        for prop in properties:
            prop_id = prop.get("id")
            prop_name = prop.get("name")
            
            print(f"📊 PROPRIÉTÉ: {prop_name} (ID={prop_id})")
            print("-" * 80)
            
            # Récupérer les configurations de crédit pour cette propriété
            response = requests.get(f"{API_BASE}/loan-configs?property_id={prop_id}")
            if response.status_code != 200:
                print(f"   ❌ Erreur lors de la récupération: {response.status_code}")
                print()
                continue
            
            configs = response.json().get("items", [])
            
            if not configs:
                print("   Aucun crédit configuré")
            else:
                print(f"   Nombre de crédits: {len(configs)}")
                for i, config in enumerate(configs, 1):
                    print(f"\n   Crédit #{i}:")
                    print(f"      - ID: {config.get('id')}")
                    print(f"      - Nom: {config.get('name')}")
                    print(f"      - Montant: {config.get('credit_amount'):,.2f} €")
                    print(f"      - Taux d'intérêt: {config.get('interest_rate')}%")
                    print(f"      - Durée: {config.get('duration_years')} ans")
                    print(f"      - Assurance mensuelle: {config.get('monthly_insurance'):,.2f} €")
                    if config.get('loan_start_date'):
                        print(f"      - Date de début: {config.get('loan_start_date')}")
                    if config.get('loan_end_date'):
                        print(f"      - Date de fin: {config.get('loan_end_date')}")
                    
                    # Récupérer les mensualités pour ce crédit
                    loan_name = config.get('name')
                    payments_response = requests.get(
                        f"{API_BASE}/loan-payments?property_id={prop_id}&loan_name={loan_name}&limit=1000"
                    )
                    if payments_response.status_code == 200:
                        payments = payments_response.json().get("items", [])
                        print(f"      - Nombre de mensualités: {len(payments)}")
                        if payments:
                            total_capital = sum(p.get('capital', 0) for p in payments)
                            total_interest = sum(p.get('interest', 0) for p in payments)
                            total_insurance = sum(p.get('insurance', 0) for p in payments)
                            print(f"      - Total capital remboursé: {total_capital:,.2f} €")
                            print(f"      - Total intérêts: {total_interest:,.2f} €")
                            print(f"      - Total assurance: {total_insurance:,.2f} €")
            
            print()
        
        return True
        
    except Exception as e:
        print_error(f"Exception lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale."""
    print("\n" + "=" * 80)
    print("  TESTS D'ISOLATION - ONGLET CRÉDIT (Phase 11)")
    print("=" * 80)
    
    results = []
    
    # Test 1: Isolation des configurations de crédit
    result1 = test_loan_configs_isolation()
    results.append(("Isolation Configurations de Crédit", result1))
    
    # Test 2: Isolation des mensualités
    result2 = test_loan_payments_isolation()
    results.append(("Isolation Mensualités", result2))
    
    # Test 3: Affichage des crédits par propriété
    result3 = test_credits_by_property()
    results.append(("Affichage Crédits par Propriété", result3))
    
    # Résumé
    print_section("RÉSUMÉ DES TESTS")
    all_passed = True
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print_success("TOUS LES TESTS SONT PASSÉS !")
        return 0
    else:
        print_error("CERTAINS TESTS ONT ÉCHOUÉ")
        return 1

if __name__ == "__main__":
    exit(main())
