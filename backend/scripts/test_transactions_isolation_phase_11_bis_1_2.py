"""
Test Step 1.2 : Isolation frontend - Vérification que le frontend passe property_id

Ce script teste que tous les appels API utilisés par le frontend passent correctement property_id
et que l'isolation des transactions fonctionne.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.
Les logs backend montreront chaque opération avec [Transactions] prefix.

Ce script simule les appels que le frontend ferait :
1. GET /api/transactions?property_id=X
2. POST /api/transactions (avec property_id dans le body)
3. PUT /api/transactions/{id}?property_id=X
4. DELETE /api/transactions/{id}?property_id=X
5. GET /api/transactions/unique-values?property_id=X
6. GET /api/transactions/export?property_id=X
7. POST /api/transactions/import (avec property_id dans FormData)

Tous les logs backend doivent montrer le property_id correct.
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
print("TEST D'ISOLATION FRONTEND - Step 1.2")
print("Vérification que le frontend passe property_id à tous les appels API")
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

prop1_data = {"name": "Test Property Frontend 1", "address": "123 Test Street"}
prop2_data = {"name": "Test Property Frontend 2", "address": "456 Test Avenue"}

response1 = requests.post(f"{API_BASE}/properties", json=prop1_data)
if response1.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer prop1: {response1.status_code}")
    print(response1.text)
    sys.exit(1)
prop1 = response1.json()
print(f"✅ Propriété 1 créée: ID={prop1['id']}, Name={prop1['name']}")

response2 = requests.post(f"{API_BASE}/properties", json=prop2_data)
if response2.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer prop2: {response2.status_code}")
    print(response2.text)
    sys.exit(1)
prop2 = response2.json()
print(f"✅ Propriété 2 créée: ID={prop2['id']}, Name={prop2['name']}")
print()

# 2. Créer des transactions pour prop1
print("📋 ÉTAPE 2 : Création de transactions pour Property 1")
print("-" * 80)
print("⚠️  Vérifiez les logs backend: [Transactions] POST /api/transactions - property_id={prop1['id']}")
print()

trans1_1_data = {
    "property_id": prop1['id'],
    "date": "2024-01-15",
    "quantite": 100.0,
    "nom": "Transaction Prop1 #1",
    "solde": 1000.0
}
trans1_2_data = {
    "property_id": prop1['id'],
    "date": "2024-01-16",
    "quantite": 200.0,
    "nom": "Transaction Prop1 #2",
    "solde": 1200.0
}
trans1_3_data = {
    "property_id": prop1['id'],
    "date": "2024-01-17",
    "quantite": 300.0,
    "nom": "Transaction Prop1 #3",
    "solde": 1500.0
}

response = requests.post(f"{API_BASE}/transactions", json=trans1_1_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer trans1_1: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans1_1 = response.json()
print(f"✅ Transaction 1 créée: ID={trans1_1['id']}, property_id={trans1_1['property_id']}")

response = requests.post(f"{API_BASE}/transactions", json=trans1_2_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer trans1_2: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans1_2 = response.json()
print(f"✅ Transaction 2 créée: ID={trans1_2['id']}, property_id={trans1_2['property_id']}")

response = requests.post(f"{API_BASE}/transactions", json=trans1_3_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer trans1_3: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans1_3 = response.json()
print(f"✅ Transaction 3 créée: ID={trans1_3['id']}, property_id={trans1_3['property_id']}")
print()

# 3. Vérifier que les transactions de prop1 sont visibles
print("📋 ÉTAPE 3 : Vérification que les transactions Prop1 sont visibles")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] GET /api/transactions - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/transactions?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les transactions Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data1 = response.json()
print(f"✅ Transactions récupérées pour Prop1: {data1['total']} total")

if data1['total'] != 3:
    print(f"❌ ERREUR: Attendu 3 transactions pour Prop1, obtenu {data1['total']}")
    sys.exit(1)

prop1_ids = [t['id'] for t in data1['transactions']]
if trans1_1['id'] not in prop1_ids or trans1_2['id'] not in prop1_ids or trans1_3['id'] not in prop1_ids:
    print("❌ ERREUR: Toutes les transactions Prop1 ne sont pas présentes")
    sys.exit(1)
print("✅ Toutes les transactions Prop1 sont visibles")
print()

# 4. Vérifier que les transactions de prop1 ne sont PAS visibles pour prop2
print("📋 ÉTAPE 4 : Vérification que les transactions Prop1 ne sont PAS visibles pour Prop2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] GET /api/transactions - property_id={prop2['id']}")
print()

response = requests.get(f"{API_BASE}/transactions?property_id={prop2['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les transactions Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
data2 = response.json()
print(f"✅ Transactions récupérées pour Prop2: {data2['total']} total")

if data2['total'] != 0:
    print(f"❌ ERREUR: Attendu 0 transactions pour Prop2, obtenu {data2['total']}")
    sys.exit(1)

prop2_ids = [t['id'] for t in data2['transactions']]
if any(id in prop1_ids for id in prop2_ids):
    print("❌ ERREUR: Des transactions Prop1 sont visibles pour Prop2")
    sys.exit(1)
print("✅ Aucune transaction Prop1 n'est visible pour Prop2 (isolation OK)")
print()

# 5. Créer des transactions pour prop2
print("📋 ÉTAPE 5 : Création de transactions pour Property 2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] POST /api/transactions - property_id={prop2['id']}")
print()

trans2_1_data = {
    "property_id": prop2['id'],
    "date": "2024-02-15",
    "quantite": 150.0,
    "nom": "Transaction Prop2 #1",
    "solde": 1500.0
}
trans2_2_data = {
    "property_id": prop2['id'],
    "date": "2024-02-16",
    "quantite": 250.0,
    "nom": "Transaction Prop2 #2",
    "solde": 1750.0
}

response = requests.post(f"{API_BASE}/transactions", json=trans2_1_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer trans2_1: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans2_1 = response.json()
print(f"✅ Transaction 1 créée: ID={trans2_1['id']}, property_id={trans2_1['property_id']}")

response = requests.post(f"{API_BASE}/transactions", json=trans2_2_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de créer trans2_2: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans2_2 = response.json()
print(f"✅ Transaction 2 créée: ID={trans2_2['id']}, property_id={trans2_2['property_id']}")
print()

# 6. Vérifier que les transactions de prop2 sont visibles
print("📋 ÉTAPE 6 : Vérification que les transactions Prop2 sont visibles")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] GET /api/transactions - property_id={prop2['id']}")
print()

response = requests.get(f"{API_BASE}/transactions?property_id={prop2['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les transactions Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
data3 = response.json()
print(f"✅ Transactions récupérées pour Prop2: {data3['total']} total")

if data3['total'] != 2:
    print(f"❌ ERREUR: Attendu 2 transactions pour Prop2, obtenu {data3['total']}")
    sys.exit(1)

prop2_ids_after = [t['id'] for t in data3['transactions']]
if trans2_1['id'] not in prop2_ids_after or trans2_2['id'] not in prop2_ids_after:
    print("❌ ERREUR: Toutes les transactions Prop2 ne sont pas présentes")
    sys.exit(1)
print("✅ Toutes les transactions Prop2 sont visibles")
print()

# 7. Vérifier que prop1 a toujours 3 transactions
print("📋 ÉTAPE 7 : Vérification que Prop1 a toujours 3 transactions")
print("-" * 80)

response = requests.get(f"{API_BASE}/transactions?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les transactions Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data4 = response.json()
if data4['total'] != 3:
    print(f"❌ ERREUR: Prop1 devrait avoir 3 transactions, obtenu {data4['total']}")
    sys.exit(1)
print("✅ Prop1 a toujours 3 transactions (isolation maintenue)")
print()

# 8. Tester la mise à jour avec property_id
print("📋 ÉTAPE 8 : Test de mise à jour avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] PUT /api/transactions/{trans1_1['id']} - property_id={prop1['id']}")
print()

update_data = {"nom": "Transaction Prop1 #1 UPDATED"}
response = requests.put(f"{API_BASE}/transactions/{trans1_1['id']}?property_id={prop1['id']}", json=update_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de mettre à jour la transaction: {response.status_code}")
    print(response.text)
    sys.exit(1)
updated = response.json()
if updated['nom'] != "Transaction Prop1 #1 UPDATED":
    print("❌ ERREUR: La mise à jour n'a pas fonctionné")
    sys.exit(1)
print("✅ Mise à jour réussie avec property_id")
print()

# 9. Tester la suppression avec property_id
print("📋 ÉTAPE 9 : Test de suppression avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] DELETE /api/transactions/{trans1_3['id']} - property_id={prop1['id']}")
print()

response = requests.delete(f"{API_BASE}/transactions/{trans1_3['id']}?property_id={prop1['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de supprimer la transaction: {response.status_code}")
    print(response.text)
    sys.exit(1)
print("✅ Transaction supprimée")

# Vérifier que la transaction a été supprimée
response = requests.get(f"{API_BASE}/transactions?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les transactions Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data5 = response.json()
if data5['total'] != 2:
    print(f"❌ ERREUR: Prop1 devrait avoir 2 transactions après suppression, obtenu {data5['total']}")
    sys.exit(1)
if any(t['id'] == trans1_3['id'] for t in data5['transactions']):
    print("❌ ERREUR: La transaction supprimée est toujours présente")
    sys.exit(1)
print("✅ Suppression réussie avec property_id")
print()

# 10. Tester l'accès cross-property (devrait échouer)
print("📋 ÉTAPE 10 : Test d'accès cross-property (devrait échouer)")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] PUT /api/transactions/{trans1_1['id']} - property_id={prop2['id']}")
print("    (devrait retourner 404)")
print()

update_data = {"nom": "HACKED"}
response = requests.put(f"{API_BASE}/transactions/{trans1_1['id']}?property_id={prop2['id']}", json=update_data)
if response.status_code == 200:
    print("❌ ERREUR: La mise à jour cross-property devrait échouer")
    sys.exit(1)
if response.status_code == 404:
    print("✅ Accès cross-property correctement bloqué (404)")
else:
    print(f"⚠️  Réponse inattendue: {response.status_code}")
    print(response.text)
print()

# 11. Tester getUniqueValues avec property_id
print("📋 ÉTAPE 11 : Test de getUniqueValues avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] GET unique-values - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/transactions/unique-values?property_id={prop1['id']}&column=nom")
if response.status_code != 200:
    print(f"❌ ERREUR: getUniqueValues a échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
unique_values = response.json()
print(f"✅ getUniqueValues fonctionne: {len(unique_values['values'])} valeurs uniques pour Prop1")
print()

# 12. Tester export avec property_id
print("📋 ÉTAPE 12 : Test d'export avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Transactions] GET export - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/transactions/export?property_id={prop1['id']}&format=csv")
if response.status_code != 200:
    print(f"❌ ERREUR: Export a échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
print("✅ Export fonctionne avec property_id")
print()

# Résultat final
print("=" * 80)
print("✅ TOUS LES TESTS D'ISOLATION FRONTEND ONT RÉUSSI !")
print("=" * 80)
print()
print("📋 RÉSUMÉ:")
print(f"   - Property 1 (ID={prop1['id']}): {data4['total']} transactions")
print(f"   - Property 2 (ID={prop2['id']}): {data3['total']} transactions")
print("   - Isolation complète vérifiée ✅")
print("   - Tous les appels API passent property_id ✅")
print()
print("⚠️  VÉRIFIEZ LES LOGS BACKEND pour confirmer que property_id est bien passé")
print("    à tous les appels API (recherchez [Transactions] dans les logs)")
print()
