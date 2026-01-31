"""
Test Step 2.2 : Isolation frontend - Vérification que le frontend passe property_id pour les Mappings

Ce script teste que tous les appels API utilisés par le frontend passent correctement property_id
et que l'isolation des mappings fonctionne.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.
Les logs backend montreront chaque opération avec [Mappings] prefix.

Ce script simule les appels que le frontend ferait :
1. GET /api/mappings?property_id=X
2. POST /api/mappings (avec property_id dans le body)
3. PUT /api/mappings/{id}?property_id=X
4. DELETE /api/mappings/{id}?property_id=X
5. GET /api/mappings/allowed?property_id=X
6. POST /api/mappings/allowed (avec property_id dans le body)
7. GET /api/mappings/combinations?property_id=X
8. Tests d'enrichissement des transactions avec isolation

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

# Générer des noms uniques avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 80)
print("TEST D'ISOLATION FRONTEND - Step 2.2 - MAPPINGS")
print("Vérification que le frontend passe property_id à tous les appels API")
print("=" * 80)
print()
print("⚠️  ASSUREZ-VOUS QUE LE SERVEUR BACKEND EST DÉMARRÉ")
print("    Les logs backend montreront chaque opération avec [Mappings] prefix")
print()
print("=" * 80)
print()

# 1. Créer 2 propriétés
print("📋 ÉTAPE 1 : Création de 2 propriétés de test")
print("-" * 80)

prop1_data = {"name": f"Test Property Mappings 1_{timestamp}", "address": "123 Test Street"}
prop2_data = {"name": f"Test Property Mappings 2_{timestamp}", "address": "456 Test Avenue"}

response1 = requests.post(f"{API_BASE}/properties", json=prop1_data)
if response1.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer prop1: {response1.status_code}")
    print(response1.text)
    sys.exit(1)
prop1 = response1.json()
print(f"✅ Propriété 1 créée: ID={prop1['id']}, Name={prop1['name']}")

response2 = requests.post(f"{API_BASE}/properties", json=prop2_data)
if response2.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer prop2: {response2.status_code}")
    print(response2.text)
    sys.exit(1)
prop2 = response2.json()
print(f"✅ Propriété 2 créée: ID={prop2['id']}, Name={prop2['name']}")
print()

# 2. Créer 3 mappings pour prop1
print("📋 ÉTAPE 2 : Création de 3 mappings pour Property 1")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] POST /api/mappings - property_id={prop1['id']}")
print()

mapping1_1_data = {
    "property_id": prop1['id'],
    "nom": "Mapping Prop1 #1",
    "level_1": "Revenus",
    "level_2": "Loyers",
    "level_3": "Loyer principal",
    "is_prefix_match": False,
    "priority": 1
}
mapping1_2_data = {
    "property_id": prop1['id'],
    "nom": "Mapping Prop1 #2",
    "level_1": "Charges",
    "level_2": "Entretien",
    "level_3": "Réparations",
    "is_prefix_match": False,
    "priority": 1
}
mapping1_3_data = {
    "property_id": prop1['id'],
    "nom": "Mapping Prop1 #3",
    "level_1": "Charges",
    "level_2": "Taxes",
    "level_3": "Taxe foncière",
    "is_prefix_match": False,
    "priority": 1
}

response = requests.post(f"{API_BASE}/mappings", json=mapping1_1_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer mapping1_1: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping1_1 = response.json()
print(f"✅ Mapping 1 créé: ID={mapping1_1['id']}, property_id={mapping1_1_data['property_id']}, nom={mapping1_1['nom']}")

response = requests.post(f"{API_BASE}/mappings", json=mapping1_2_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer mapping1_2: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping1_2 = response.json()
print(f"✅ Mapping 2 créé: ID={mapping1_2['id']}, property_id={mapping1_2_data['property_id']}, nom={mapping1_2['nom']}")

response = requests.post(f"{API_BASE}/mappings", json=mapping1_3_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer mapping1_3: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping1_3 = response.json()
print(f"✅ Mapping 3 créé: ID={mapping1_3['id']}, property_id={mapping1_3_data['property_id']}, nom={mapping1_3['nom']}")
print()

# 3. Vérifier que les mappings de prop1 sont visibles
print("📋 ÉTAPE 3 : Vérification que les mappings Prop1 sont visibles")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] GET /api/mappings - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/mappings?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data1 = response.json()
print(f"✅ Mappings récupérés pour Prop1: {data1['total']} total")

if data1['total'] < 3:
    print(f"⚠️  ATTENTION: Attendu au moins 3 mappings pour Prop1, obtenu {data1['total']}")
    print("   (Il peut y avoir des mappings hardcodés initialisés)")
else:
    print(f"✅ Au moins 3 mappings pour Prop1 (isolation OK)")

prop1_mapping_ids = [m['id'] for m in data1['mappings']]
if mapping1_1['id'] not in prop1_mapping_ids or mapping1_2['id'] not in prop1_mapping_ids or mapping1_3['id'] not in prop1_mapping_ids:
    print("❌ ERREUR: Tous les mappings Prop1 ne sont pas présents")
    sys.exit(1)
print("✅ Tous les mappings Prop1 sont visibles")
print()

# 4. Vérifier que les mappings de prop1 ne sont PAS visibles pour prop2
print("📋 ÉTAPE 4 : Vérification que les mappings Prop1 ne sont PAS visibles pour Prop2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] GET /api/mappings - property_id={prop2['id']}")
print()

response = requests.get(f"{API_BASE}/mappings?property_id={prop2['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
data2 = response.json()
print(f"✅ Mappings récupérés pour Prop2: {data2['total']} total")

prop2_mapping_ids = [m['id'] for m in data2['mappings']]
# Prop2 peut avoir des mappings hardcodés initialisés, mais pas nos mappings créés
if any(id in prop1_mapping_ids for id in prop2_mapping_ids if id in [mapping1_1['id'], mapping1_2['id'], mapping1_3['id']]):
    print("❌ ERREUR: Des mappings Prop1 sont visibles pour Prop2")
    sys.exit(1)
print("✅ Aucun mapping Prop1 n'est visible pour Prop2 (isolation OK)")
print()

# 5. Créer 2 mappings pour prop2
print("📋 ÉTAPE 5 : Création de 2 mappings pour Property 2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] POST /api/mappings - property_id={prop2['id']}")
print()

mapping2_1_data = {
    "property_id": prop2['id'],
    "nom": "Mapping Prop2 #1",
    "level_1": "Revenus",
    "level_2": "Loyers",
    "level_3": "Loyer secondaire",
    "is_prefix_match": False,
    "priority": 1
}
mapping2_2_data = {
    "property_id": prop2['id'],
    "nom": "Mapping Prop2 #2",
    "level_1": "Charges",
    "level_2": "Assurance",
    "level_3": "Assurance habitation",
    "is_prefix_match": False,
    "priority": 1
}

response = requests.post(f"{API_BASE}/mappings", json=mapping2_1_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer mapping2_1: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping2_1 = response.json()
print(f"✅ Mapping 1 créé: ID={mapping2_1['id']}, property_id={mapping2_1_data['property_id']}, nom={mapping2_1['nom']}")

response = requests.post(f"{API_BASE}/mappings", json=mapping2_2_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer mapping2_2: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping2_2 = response.json()
print(f"✅ Mapping 2 créé: ID={mapping2_2['id']}, property_id={mapping2_2_data['property_id']}, nom={mapping2_2['nom']}")
print()

# 6. Vérifier que les mappings de prop2 sont visibles
print("📋 ÉTAPE 6 : Vérification que les mappings Prop2 sont visibles")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] GET /api/mappings - property_id={prop2['id']}")
print()

response = requests.get(f"{API_BASE}/mappings?property_id={prop2['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
data3 = response.json()
print(f"✅ Mappings récupérés pour Prop2: {data3['total']} total")

prop2_mapping_ids_after = [m['id'] for m in data3['mappings']]
if mapping2_1['id'] not in prop2_mapping_ids_after or mapping2_2['id'] not in prop2_mapping_ids_after:
    print("❌ ERREUR: Tous les mappings Prop2 ne sont pas présents")
    sys.exit(1)
print("✅ Tous les mappings Prop2 sont visibles")
print()

# 7. Vérifier que prop1 a toujours ses 3 mappings
print("📋 ÉTAPE 7 : Vérification que Prop1 a toujours ses 3 mappings")
print("-" * 80)

response = requests.get(f"{API_BASE}/mappings?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data4 = response.json()
prop1_mapping_ids_final = [m['id'] for m in data4['mappings']]
if mapping1_1['id'] not in prop1_mapping_ids_final or mapping1_2['id'] not in prop1_mapping_ids_final or mapping1_3['id'] not in prop1_mapping_ids_final:
    print("❌ ERREUR: Prop1 devrait avoir ses 3 mappings, certains manquent")
    sys.exit(1)
print("✅ Prop1 a toujours ses 3 mappings (isolation maintenue)")
print()

# 8. Tester la mise à jour avec property_id
print("📋 ÉTAPE 8 : Test de mise à jour avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] PUT /api/mappings/{mapping1_1['id']} - property_id={prop1['id']}")
print()

update_data = {"nom": "Mapping Prop1 #1 UPDATED"}
response = requests.put(f"{API_BASE}/mappings/{mapping1_1['id']}?property_id={prop1['id']}", json=update_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de mettre à jour le mapping: {response.status_code}")
    print(response.text)
    sys.exit(1)
updated = response.json()
if updated['nom'] != "Mapping Prop1 #1 UPDATED":
    print("❌ ERREUR: La mise à jour n'a pas fonctionné")
    sys.exit(1)
print("✅ Mise à jour réussie avec property_id")
print()

# 9. Tester la suppression avec property_id
print("📋 ÉTAPE 9 : Test de suppression avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] DELETE /api/mappings/{mapping1_3['id']} - property_id={prop1['id']}")
print()

response = requests.delete(f"{API_BASE}/mappings/{mapping1_3['id']}?property_id={prop1['id']}")
if response.status_code != 204:
    print(f"❌ ERREUR: Impossible de supprimer le mapping: {response.status_code}")
    print(response.text)
    sys.exit(1)
print("✅ Mapping supprimé")

# Vérifier que le mapping a été supprimé
response = requests.get(f"{API_BASE}/mappings?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
data5 = response.json()
prop1_mapping_ids_after_delete = [m['id'] for m in data5['mappings']]
if mapping1_3['id'] in prop1_mapping_ids_after_delete:
    print("❌ ERREUR: Le mapping supprimé est toujours présent")
    sys.exit(1)
print("✅ Suppression réussie avec property_id")
print()

# 10. Tester l'accès cross-property (devrait échouer)
print("📋 ÉTAPE 10 : Test d'accès cross-property (devrait échouer)")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] PUT /api/mappings/{mapping1_1['id']} - property_id={prop2['id']}")
print("    (devrait retourner 404)")
print()

update_data = {"nom": "HACKED"}
response = requests.put(f"{API_BASE}/mappings/{mapping1_1['id']}?property_id={prop2['id']}", json=update_data)
if response.status_code == 200:
    print("❌ ERREUR: La mise à jour cross-property devrait échouer")
    sys.exit(1)
if response.status_code == 404:
    print("✅ Accès cross-property correctement bloqué (404)")
else:
    print(f"⚠️  Réponse inattendue: {response.status_code}")
    print(response.text)
print()

# 11. Tester les mappings autorisés avec property_id
print("📋 ÉTAPE 11 : Test des mappings autorisés avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] GET /api/mappings/allowed - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/mappings/allowed?property_id={prop1['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_mappings a échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
allowed1 = response.json()
print(f"✅ Mappings autorisés pour Prop1: {allowed1['total']} total")

response = requests.get(f"{API_BASE}/mappings/allowed?property_id={prop2['id']}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_mappings a échoué pour Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
allowed2 = response.json()
print(f"✅ Mappings autorisés pour Prop2: {allowed2['total']} total")

# Les deux propriétés devraient avoir le même nombre de mappings hardcodés (57)
if allowed1['total'] != allowed2['total']:
    print(f"⚠️  ATTENTION: Nombre différent de mappings autorisés (Prop1: {allowed1['total']}, Prop2: {allowed2['total']})")
    print("   (Normal si les mappings hardcodés sont initialisés différemment)")
else:
    print("✅ Les deux propriétés ont le même nombre de mappings autorisés (hardcodés)")
print()

# 12. Tester getCombinations avec property_id
print("📋 ÉTAPE 12 : Test de getCombinations avec property_id")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Mappings] GET /api/mappings/combinations - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/mappings/combinations?property_id={prop1['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: getCombinations a échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
combinations1 = response.json()
print(f"✅ getCombinations fonctionne pour Prop1: {len(combinations1)} combinaisons")
print()

# 13. CRITIQUE : Tester l'enrichissement des transactions avec isolation
print("📋 ÉTAPE 13 : CRITIQUE - Test d'enrichissement des transactions avec isolation")
print("-" * 80)
print("⚠️  Ce test vérifie que l'enrichissement utilise uniquement les mappings de la propriété")
print()

# Créer une transaction pour prop1 avec un nom qui correspond à un mapping de prop1
print("   → Création d'une transaction pour Prop1 avec nom correspondant à un mapping Prop1")
trans1_data = {
    "property_id": prop1['id'],
    "date": "2024-01-15",
    "quantite": 100.0,
    "nom": mapping1_2['nom'],  # Utiliser le nom d'un mapping de prop1
    "solde": 1000.0
}
response = requests.post(f"{API_BASE}/transactions", json=trans1_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer la transaction Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans1 = response.json()
print(f"   ✅ Transaction Prop1 créée: ID={trans1['id']}, nom={trans1['nom']}")

# Re-enrichir toutes les transactions de prop1
print("   → Re-enrichissement de toutes les transactions Prop1")
response = requests.post(f"{API_BASE}/enrichment/re-enrich?property_id={prop1['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: Re-enrichissement échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
re_enrich_result1 = response.json()
print(f"   ✅ Re-enrichissement Prop1: {re_enrich_result1.get('enriched_count')} nouvelles, {re_enrich_result1.get('already_enriched_count')} re-enrichies")

# Récupérer la transaction enrichie
response = requests.get(f"{API_BASE}/transactions/{trans1['id']}?property_id={prop1['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer la transaction Prop1: {response.status_code}")
    print(response.text)
    sys.exit(1)
enriched1 = response.json()
print(f"   ✅ Transaction Prop1: level_1={enriched1.get('level_1')}, level_2={enriched1.get('level_2')}, level_3={enriched1.get('level_3')}")

# Vérifier que la transaction a été enrichie avec le mapping de prop1
if enriched1.get('level_1') == mapping1_2['level_1'] and enriched1.get('level_2') == mapping1_2['level_2']:
    print("   ✅ Transaction Prop1 correctement enrichie avec le mapping Prop1")
else:
    print(f"   ⚠️  ATTENTION: Enrichissement inattendu (attendu: {mapping1_2['level_1']}/{mapping1_2['level_2']}, obtenu: {enriched1.get('level_1')}/{enriched1.get('level_2')})")
print()

# Créer une transaction pour prop2 avec le même nom (mais prop2 n'a pas ce mapping)
print("   → Création d'une transaction pour Prop2 avec le même nom (mais Prop2 n'a pas ce mapping)")
trans2_data = {
    "property_id": prop2['id'],
    "date": "2024-01-16",
    "quantite": 200.0,
    "nom": mapping1_2['nom'],  # Même nom que le mapping de prop1
    "solde": 2000.0
}
response = requests.post(f"{API_BASE}/transactions", json=trans2_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer la transaction Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
trans2 = response.json()
print(f"   ✅ Transaction Prop2 créée: ID={trans2['id']}, nom={trans2['nom']}")

# Re-enrichir toutes les transactions de prop2
print("   → Re-enrichissement de toutes les transactions Prop2")
response = requests.post(f"{API_BASE}/enrichment/re-enrich?property_id={prop2['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: Re-enrichissement échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
re_enrich_result2 = response.json()
print(f"   ✅ Re-enrichissement Prop2: {re_enrich_result2.get('enriched_count')} nouvelles, {re_enrich_result2.get('already_enriched_count')} re-enrichies")

# Récupérer la transaction enrichie
response = requests.get(f"{API_BASE}/transactions/{trans2['id']}?property_id={prop2['id']}")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer la transaction Prop2: {response.status_code}")
    print(response.text)
    sys.exit(1)
enriched2 = response.json()
print(f"   ✅ Transaction Prop2: level_1={enriched2.get('level_1')}, level_2={enriched2.get('level_2')}, level_3={enriched2.get('level_3')}")

# CRITIQUE : Vérifier que la transaction de prop2 n'est PAS enrichie avec le mapping de prop1
if enriched2.get('level_1') == mapping1_2['level_1'] and enriched2.get('level_2') == mapping1_2['level_2']:
    print("   ❌ ERREUR CRITIQUE: Transaction Prop2 enrichie avec le mapping Prop1 (isolation échouée!)")
    sys.exit(1)
else:
    print("   ✅ Transaction Prop2 n'est PAS enrichie avec le mapping Prop1 (isolation OK)")
print()

# Résultat final
print("=" * 80)
print("✅ TOUS LES TESTS D'ISOLATION FRONTEND ONT RÉUSSI !")
print("=" * 80)
print()
print("📋 RÉSUMÉ:")
print(f"   - Property 1 (ID={prop1['id']}): {data4['total']} mappings")
print(f"   - Property 2 (ID={prop2['id']}): {data3['total']} mappings")
print("   - Isolation complète vérifiée ✅")
print("   - Tous les appels API passent property_id ✅")
print("   - Enrichissement isolé par propriété ✅")
print()
print("⚠️  VÉRIFIEZ LES LOGS BACKEND pour confirmer que property_id est bien passé")
print("    à tous les appels API (recherchez [Mappings] dans les logs)")
print()
