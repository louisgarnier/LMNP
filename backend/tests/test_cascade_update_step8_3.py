"""
Test script for Step 8.3 - Vérification de la mise à jour automatique en cascade.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_cascade_update_step8_3.py

⚠️ IMPORTANT: Le backend doit être démarré sur http://localhost:8000
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
from datetime import date


BASE_URL = "http://localhost:8000"


def test_cascade_update():
    """Test que la mise à jour d'une transaction met à jour toutes les transactions avec le même nom."""
    print("=" * 60)
    print("Test de mise à jour automatique en cascade (Step 8.3)")
    print("=" * 60)
    print()
    
    # Étape 1: Créer plusieurs transactions avec le même nom
    print("📋 Étape 1: Création de transactions avec le même nom")
    transaction_name = "TEST CASCADE UPDATE " + str(date.today())
    
    transaction_ids = []
    for i in range(3):
        transaction_data = {
            "date": str(date.today()),
            "quantite": 100.0 + i,
            "nom": transaction_name,
            "solde": 1000.0 + i,
            "source_file": "test.csv"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/transactions", json=transaction_data)
            response.raise_for_status()
            transaction = response.json()
            transaction_ids.append(transaction["id"])
            print(f"   ✅ Transaction {i+1} créée (ID: {transaction['id']})")
        except Exception as e:
            print(f"   ❌ Erreur lors de la création de la transaction {i+1}: {e}")
            return False
    
    print()
    
    # Étape 2: Vérifier l'état initial (devrait être "unassigned" ou avoir des valeurs par défaut)
    print("📋 Étape 2: Vérification de l'état initial")
    initial_states = {}
    for trans_id in transaction_ids:
        try:
            response = requests.get(f"{BASE_URL}/api/transactions/{trans_id}")
            response.raise_for_status()
            transaction = response.json()
            initial_states[trans_id] = {
                "level_1": transaction.get("level_1"),
                "level_2": transaction.get("level_2"),
                "level_3": transaction.get("level_3")
            }
            print(f"   Transaction {trans_id}: level_1={transaction.get('level_1')}, level_2={transaction.get('level_2')}, level_3={transaction.get('level_3')}")
        except Exception as e:
            print(f"   ❌ Erreur lors de la récupération de la transaction {trans_id}: {e}")
            return False
    
    print()
    
    # Étape 3: Mettre à jour le mapping de la première transaction
    print("📋 Étape 3: Mise à jour du mapping de la première transaction")
    new_level_1 = "CHARGES"
    new_level_2 = "FRAIS BANCAIRES"
    new_level_3 = "TEST"
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/enrichment/transactions/{transaction_ids[0]}",
            params={
                "level_1": new_level_1,
                "level_2": new_level_2,
                "level_3": new_level_3
            }
        )
        response.raise_for_status()
        updated_transaction = response.json()
        print(f"   ✅ Transaction {transaction_ids[0]} mise à jour")
        print(f"      level_1={updated_transaction.get('level_1')}, level_2={updated_transaction.get('level_2')}, level_3={updated_transaction.get('level_3')}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la mise à jour: {e}")
        return False
    
    print()
    
    # Étape 4: Vérifier que toutes les transactions avec le même nom ont été mises à jour
    print("📋 Étape 4: Vérification de la mise à jour en cascade")
    all_updated = True
    for trans_id in transaction_ids:
        try:
            response = requests.get(f"{BASE_URL}/api/transactions/{trans_id}")
            response.raise_for_status()
            transaction = response.json()
            
            level_1_match = transaction.get("level_1") == new_level_1
            level_2_match = transaction.get("level_2") == new_level_2
            level_3_match = transaction.get("level_3") == new_level_3
            
            if level_1_match and level_2_match and level_3_match:
                print(f"   ✅ Transaction {trans_id}: Mise à jour correcte")
            else:
                print(f"   ❌ Transaction {trans_id}: Mise à jour incorrecte")
                print(f"      Attendu: level_1={new_level_1}, level_2={new_level_2}, level_3={new_level_3}")
                print(f"      Reçu: level_1={transaction.get('level_1')}, level_2={transaction.get('level_2')}, level_3={transaction.get('level_3')}")
                all_updated = False
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification de la transaction {trans_id}: {e}")
            all_updated = False
    
    print()
    
    # Nettoyage: Supprimer les transactions de test
    print("📋 Nettoyage: Suppression des transactions de test")
    for trans_id in transaction_ids:
        try:
            response = requests.delete(f"{BASE_URL}/api/transactions/{trans_id}")
            response.raise_for_status()
            print(f"   ✅ Transaction {trans_id} supprimée")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la suppression de la transaction {trans_id}: {e}")
    
    print()
    print("=" * 60)
    if all_updated:
        print("✅ Test réussi: Toutes les transactions avec le même nom ont été mises à jour")
    else:
        print("❌ Test échoué: Certaines transactions n'ont pas été mises à jour")
    print("=" * 60)
    
    return all_updated


if __name__ == "__main__":
    success = test_cascade_update()
    sys.exit(0 if success else 1)

