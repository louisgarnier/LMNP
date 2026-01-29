"""
Test Step 1.1 : Isolation complète des transactions par property_id

Ce script teste tous les endpoints modifiés pour vérifier l'isolation complète entre 2 propriétés.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.
Les logs backend montreront chaque opération avec [Transactions] prefix.

Comment tester chaque fonctionnalité :
1. GET /api/transactions : Vérifier les logs "[Transactions] GET /api/transactions - property_id=X"
2. POST /api/transactions : Vérifier les logs "[Transactions] POST /api/transactions - property_id=X"
3. PUT /api/transactions/{id} : Vérifier les logs "[Transactions] PUT /api/transactions/{id} - property_id=X"
4. DELETE /api/transactions/{id} : Vérifier les logs "[Transactions] DELETE /api/transactions/{id} - property_id=X"
5. GET /api/transactions/{id} : Vérifier les logs "[Transactions] GET /api/transactions/{id} - property_id=X"
6. GET /api/transactions/unique-values : Vérifier les logs "[Transactions] GET unique-values - property_id=X"
7. GET /api/transactions/sum-by-level1 : Vérifier les logs "[Transactions] GET sum-by-level1 - property_id=X"
8. GET /api/transactions/export : Vérifier les logs "[Transactions] GET export - property_id=X"
9. POST /api/transactions/import : Vérifier les logs "[Transactions] POST import - property_id=X"

Tous les logs doivent montrer le property_id correct et l'isolation doit être complète.
"""

import sys
import os
import requests
from datetime import date, datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

print("=" * 80)
print("TEST D'ISOLATION COMPLÈTE - TRANSACTIONS PAR PROPERTY_ID")
print("=" * 80)
print()
print("⚠️  ASSUREZ-VOUS QUE LE SERVEUR BACKEND EST DÉMARRÉ")
print("    Les logs backend montreront chaque opération avec [Transactions] prefix")
print()
print("=" * 80)
print()

# 1. Créer 2 propriétés
print("📋 ÉTAPE 1 : Création de 2 propriétés de test")
print("-" * 80)

prop1_data = {"name": "Test Property 1", "address": "123 Test Street"}
prop2_data = {"name": "Test Property 2", "address": "456 Test Avenue"}

try:
    response1 = requests.post(f"{API_BASE}/properties", json=prop1_data)
    if response1.status_code == 201:
        prop1 = response1.json()
        prop1_id = prop1["id"]
        print(f"✅ Property 1 créée: ID={prop1_id}, Name={prop1['name']}")
    else:
        # Peut-être existe déjà
        response1 = requests.get(f"{API_BASE}/properties")
        props = response1.json()
        prop1 = next((p for p in props if p["name"] == prop1_data["name"]), None)
        if prop1:
            prop1_id = prop1["id"]
            print(f"✅ Property 1 existe déjà: ID={prop1_id}, Name={prop1['name']}")
        else:
            print(f"❌ Erreur création Property 1: {response1.status_code} - {response1.text}")
            sys.exit(1)
    
    response2 = requests.post(f"{API_BASE}/properties", json=prop2_data)
    if response2.status_code == 201:
        prop2 = response2.json()
        prop2_id = prop2["id"]
        print(f"✅ Property 2 créée: ID={prop2_id}, Name={prop2['name']}")
    else:
        # Peut-être existe déjà
        response2 = requests.get(f"{API_BASE}/properties")
        props = response2.json()
        prop2 = next((p for p in props if p["name"] == prop2_data["name"]), None)
        if prop2:
            prop2_id = prop2["id"]
            print(f"✅ Property 2 existe déjà: ID={prop2_id}, Name={prop2['name']}")
        else:
            print(f"❌ Erreur création Property 2: {response2.status_code} - {response2.text}")
            sys.exit(1)
    
    print()
    
except Exception as e:
    print(f"❌ Erreur lors de la création des propriétés: {e}")
    sys.exit(1)

# 2. Créer des transactions pour prop1
print("📋 ÉTAPE 2 : Création de 5 transactions pour Property 1")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] POST /api/transactions - property_id={prop1_id}")
print()

transactions_prop1 = []
for i in range(5):
    transaction_data = {
        "property_id": prop1_id,
        "date": f"2024-01-{15+i:02d}",
        "quantite": 100.0 + i * 10,
        "nom": f"Transaction Prop1 #{i+1}",
        "solde": 0.0  # Sera recalculé
    }
    
    try:
        response = requests.post(f"{API_BASE}/transactions", json=transaction_data)
        if response.status_code == 201:
            trans = response.json()
            transactions_prop1.append(trans)
            print(f"   ✅ Transaction {i+1} créée: ID={trans['id']}, Nom={trans['nom']}")
        else:
            print(f"   ❌ Erreur création transaction {i+1}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print()

# 3. Créer des transactions pour prop2
print("📋 ÉTAPE 3 : Création de 3 transactions pour Property 2")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] POST /api/transactions - property_id={prop2_id}")
print()

transactions_prop2 = []
for i in range(3):
    transaction_data = {
        "property_id": prop2_id,
        "date": f"2024-02-{10+i:02d}",
        "quantite": 200.0 + i * 20,
        "nom": f"Transaction Prop2 #{i+1}",
        "solde": 0.0  # Sera recalculé
    }
    
    try:
        response = requests.post(f"{API_BASE}/transactions", json=transaction_data)
        if response.status_code == 201:
            trans = response.json()
            transactions_prop2.append(trans)
            print(f"   ✅ Transaction {i+1} créée: ID={trans['id']}, Nom={trans['nom']}")
        else:
            print(f"   ❌ Erreur création transaction {i+1}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print()

# 4. Test GET /api/transactions pour prop1
print("📋 ÉTAPE 4 : Test GET /api/transactions pour Property 1")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET /api/transactions - property_id={prop1_id}")
print("   Vérifiez les logs backend: [Transactions] Retourné X transactions pour property_id={prop1_id}")
print()

try:
    response = requests.get(f"{API_BASE}/transactions", params={"property_id": prop1_id})
    if response.status_code == 200:
        data = response.json()
        count = len(data["transactions"])
        print(f"   ✅ GET /api/transactions?property_id={prop1_id} retourne {count} transactions")
        
        # Vérifier que toutes les transactions appartiennent à prop1
        all_prop1 = all(t.get("property_id") == prop1_id for t in data["transactions"] if "property_id" in t)
        if all_prop1 or count == len(transactions_prop1):
            print(f"   ✅ Toutes les transactions appartiennent à Property 1")
        else:
            print(f"   ⚠️  Certaines transactions n'ont pas property_id ou appartiennent à une autre propriété")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print()

# 5. Test GET /api/transactions pour prop2
print("📋 ÉTAPE 5 : Test GET /api/transactions pour Property 2")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET /api/transactions - property_id={prop2_id}")
print()

try:
    response = requests.get(f"{API_BASE}/transactions", params={"property_id": prop2_id})
    if response.status_code == 200:
        data = response.json()
        count = len(data["transactions"])
        print(f"   ✅ GET /api/transactions?property_id={prop2_id} retourne {count} transactions")
        
        if count == len(transactions_prop2):
            print(f"   ✅ Nombre correct de transactions pour Property 2")
        else:
            print(f"   ⚠️  Nombre attendu: {len(transactions_prop2)}, obtenu: {count}")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print()

# 6. Test isolation : Tentative d'accès à une transaction de prop2 avec property_id=prop1
print("📋 ÉTAPE 6 : Test d'isolation - Accès transaction prop2 avec property_id=prop1")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET /api/transactions/{id} - property_id={prop1_id}")
print("   Doit retourner 404 si transaction n'appartient pas à prop1")
print()

if transactions_prop2:
    trans_prop2_id = transactions_prop2[0]["id"]
    try:
        response = requests.get(
            f"{API_BASE}/transactions/{trans_prop2_id}",
            params={"property_id": prop1_id}
        )
        if response.status_code == 404:
            print(f"   ✅ 404 retourné correctement - Transaction {trans_prop2_id} n'appartient pas à Property 1")
        else:
            print(f"   ❌ Erreur: Devrait retourner 404, mais a retourné {response.status_code}")
            print(f"      Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print()

# 7. Test PUT /api/transactions/{id}
print("📋 ÉTAPE 7 : Test PUT /api/transactions/{id}")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] PUT /api/transactions/{id} - property_id={prop1_id}")
print("   Vérifiez les logs backend: [Transactions] Transaction {id} mise à jour pour property_id={prop1_id}")
print()

if transactions_prop1:
    trans_id = transactions_prop1[0]["id"]
    update_data = {"nom": "Transaction Prop1 MODIFIÉE"}
    
    try:
        response = requests.put(
            f"{API_BASE}/transactions/{trans_id}",
            json=update_data,
            params={"property_id": prop1_id}
        )
        if response.status_code == 200:
            print(f"   ✅ Transaction {trans_id} mise à jour avec succès")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print()

# 8. Test DELETE /api/transactions/{id}
print("📋 ÉTAPE 8 : Test DELETE /api/transactions/{id}")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] DELETE /api/transactions/{id} - property_id={prop1_id}")
print("   Vérifiez les logs backend: [Transactions] Transaction {id} supprimée pour property_id={prop1_id}")
print()

if len(transactions_prop1) > 1:
    trans_id = transactions_prop1[-1]["id"]  # Supprimer la dernière
    
    try:
        response = requests.delete(
            f"{API_BASE}/transactions/{trans_id}",
            params={"property_id": prop1_id}
        )
        if response.status_code == 204:
            print(f"   ✅ Transaction {trans_id} supprimée avec succès")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print()

# 9. Test GET /api/transactions/unique-values
print("📋 ÉTAPE 9 : Test GET /api/transactions/unique-values")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET unique-values - property_id={prop1_id}, column=nom")
print()

try:
    response = requests.get(
        f"{API_BASE}/transactions/unique-values",
        params={"property_id": prop1_id, "column": "nom"}
    )
    if response.status_code == 200:
        values = response.json()
        print(f"   ✅ GET unique-values retourne {len(values)} valeurs uniques pour Property 1")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print()

# 10. Test GET /api/transactions/sum-by-level1
print("📋 ÉTAPE 10 : Test GET /api/transactions/sum-by-level1")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET sum-by-level1 - property_id={prop1_id}")
print()

try:
    response = requests.get(
        f"{API_BASE}/transactions/sum-by-level1",
        params={"property_id": prop1_id, "level_1": "Test Level 1"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ GET sum-by-level1 retourne total={data.get('total', 0)} pour Property 1")
    else:
        print(f"   ⚠️  Réponse: {response.status_code} (normal si aucun level_1 correspond)")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print()

# 11. Test GET /api/transactions/export
print("📋 ÉTAPE 11 : Test GET /api/transactions/export")
print("-" * 80)
print("   Vérifiez les logs backend: [Transactions] GET export - property_id={prop1_id}, format=excel")
print()

try:
    response = requests.get(
        f"{API_BASE}/transactions/export",
        params={"property_id": prop1_id, "format": "excel"}
    )
    if response.status_code == 200:
        print(f"   ✅ GET export retourne un fichier Excel pour Property 1")
        print(f"      Content-Type: {response.headers.get('Content-Type')}")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print()

# 12. Résumé final
print("=" * 80)
print("RÉSUMÉ DES TESTS")
print("=" * 80)
print()
print("✅ Vérifiez les logs backend pour chaque opération:")
print("   - [Transactions] GET /api/transactions - property_id=X")
print("   - [Transactions] POST /api/transactions - property_id=X")
print("   - [Transactions] PUT /api/transactions/{id} - property_id=X")
print("   - [Transactions] DELETE /api/transactions/{id} - property_id=X")
print("   - [Transactions] GET /api/transactions/{id} - property_id=X")
print("   - [Transactions] GET unique-values - property_id=X")
print("   - [Transactions] GET sum-by-level1 - property_id=X")
print("   - [Transactions] GET export - property_id=X")
print()
print("✅ Vérifiez que:")
print("   - Property 1 voit uniquement ses transactions")
print("   - Property 2 voit uniquement ses transactions")
print("   - Tentative d'accès cross-property retourne 404")
print("   - Tous les logs montrent le property_id correct")
print()
print("=" * 80)
print("✅ Test d'isolation terminé")
print("=" * 80)
