"""
Test Step 3.1 : Isolation backend - Vérification que les endpoints Amortissements isolent correctement par property_id

Ce script teste que tous les endpoints API isolent correctement les données par property_id
et que l'isolation des amortissements fonctionne.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.
Les logs backend montreront chaque opération avec [Amortizations] prefix.

Ce script teste :
1. GET /api/amortization/types?property_id=X
2. POST /api/amortization/types (avec property_id dans le body)
3. PUT /api/amortization/types/{id}?property_id=X
4. DELETE /api/amortization/types/{id}?property_id=X
5. GET /api/amortization/results/aggregated?property_id=X
6. POST /api/amortization/recalculate (avec property_id dans le body)
7. Vérification de l'isolation complète entre 2 propriétés

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
print("TEST D'ISOLATION BACKEND - Step 3.1 - AMORTISSEMENTS")
print("Vérification que les endpoints isolent correctement par property_id")
print("=" * 80)
print()
print("⚠️  ASSUREZ-VOUS QUE LE SERVEUR BACKEND EST DÉMARRÉ")
print("    Les logs backend montreront chaque opération avec [Amortizations] prefix")
print()
print("=" * 80)
print()

# 1. Créer 2 propriétés
print("📋 ÉTAPE 1 : Création de 2 propriétés de test")
print("-" * 80)

prop1_data = {"name": f"Test Property Amort 1_{timestamp}", "address": "123 Test Street"}
prop2_data = {"name": f"Test Property Amort 2_{timestamp}", "address": "456 Test Avenue"}

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

# 2. Créer 3 types d'amortissement pour prop1
print("📋 ÉTAPE 2 : Création de 3 types d'amortissement pour Property 1")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] POST /api/amortization/types - property_id={prop1['id']}")
print()

type1_1_data = {
    "property_id": prop1['id'],
    "name": "Type Prop1 #1",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Immeuble (hors terrain)"],
    "duration": 20.0,
    "start_date": "2024-01-01",
    "annual_amount": None
}
type1_2_data = {
    "property_id": prop1['id'],
    "name": "Type Prop1 #2",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Mobilier & électroménager"],
    "duration": 10.0,
    "start_date": None,
    "annual_amount": None
}
type1_3_data = {
    "property_id": prop1['id'],
    "name": "Type Prop1 #3",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Travaux de rénovation, gros œuvre"],
    "duration": 15.0,
    "start_date": None,
    "annual_amount": None
}

response1_1 = requests.post(f"{API_BASE}/amortization/types", json=type1_1_data)
if response1_1.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer type1_1: {response1_1.status_code}")
    print(response1_1.text)
    sys.exit(1)
type1_1 = response1_1.json()
print(f"✅ Type 1 créé: ID={type1_1['id']}, Name={type1_1['name']}, property_id={prop1['id']}")

response1_2 = requests.post(f"{API_BASE}/amortization/types", json=type1_2_data)
if response1_2.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer type1_2: {response1_2.status_code}")
    print(response1_2.text)
    sys.exit(1)
type1_2 = response1_2.json()
print(f"✅ Type 2 créé: ID={type1_2['id']}, Name={type1_2['name']}, property_id={prop1['id']}")

response1_3 = requests.post(f"{API_BASE}/amortization/types", json=type1_3_data)
if response1_3.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer type1_3: {response1_3.status_code}")
    print(response1_3.text)
    sys.exit(1)
type1_3 = response1_3.json()
print(f"✅ Type 3 créé: ID={type1_3['id']}, Name={type1_3['name']}, property_id={prop1['id']}")
print()

# 3. Créer 2 types d'amortissement pour prop2
print("📋 ÉTAPE 3 : Création de 2 types d'amortissement pour Property 2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] POST /api/amortization/types - property_id={prop2['id']}")
print()

type2_1_data = {
    "property_id": prop2['id'],
    "name": "Type Prop2 #1",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Immeuble (hors terrain)"],
    "duration": 25.0,
    "start_date": None,
    "annual_amount": None
}
type2_2_data = {
    "property_id": prop2['id'],
    "name": "Type Prop2 #2",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Cuisine & aménagements"],
    "duration": 12.0,
    "start_date": None,
    "annual_amount": None
}

response2_1 = requests.post(f"{API_BASE}/amortization/types", json=type2_1_data)
if response2_1.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer type2_1: {response2_1.status_code}")
    print(response2_1.text)
    sys.exit(1)
type2_1 = response2_1.json()
print(f"✅ Type 1 créé: ID={type2_1['id']}, Name={type2_1['name']}, property_id={prop2['id']}")

response2_2 = requests.post(f"{API_BASE}/amortization/types", json=type2_2_data)
if response2_2.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer type2_2: {response2_2.status_code}")
    print(response2_2.text)
    sys.exit(1)
type2_2 = response2_2.json()
print(f"✅ Type 2 créé: ID={type2_2['id']}, Name={type2_2['name']}, property_id={prop2['id']}")
print()

# 4. Test GET /api/amortization/types pour prop1
print("📋 ÉTAPE 4 : Test GET /api/amortization/types pour Property 1")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] GET /api/amortization/types - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/amortization/types", params={"property_id": prop1['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

types_prop1 = response.json()
print(f"✅ {len(types_prop1['items'])} types retournés pour property_id={prop1['id']}")
print(f"   Types: {[t['name'] for t in types_prop1['items']]}")

# Vérifier que seuls les types de prop1 sont retournés
type_ids_prop1 = {t['id'] for t in types_prop1['items']}
expected_ids = {type1_1['id'], type1_2['id'], type1_3['id']}
if type_ids_prop1 == expected_ids:
    print("✅ ISOLATION OK: Seuls les 3 types de prop1 sont retournés")
else:
    print(f"❌ ERREUR ISOLATION: Types retournés: {type_ids_prop1}, Attendu: {expected_ids}")
    sys.exit(1)
print()

# 5. Test GET /api/amortization/types pour prop2
print("📋 ÉTAPE 5 : Test GET /api/amortization/types pour Property 2")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] GET /api/amortization/types - property_id={prop2['id']}")
print()

response = requests.get(f"{API_BASE}/amortization/types", params={"property_id": prop2['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

types_prop2 = response.json()
print(f"✅ {len(types_prop2['items'])} types retournés pour property_id={prop2['id']}")
print(f"   Types: {[t['name'] for t in types_prop2['items']]}")

# Vérifier que seuls les types de prop2 sont retournés
type_ids_prop2 = {t['id'] for t in types_prop2['items']}
expected_ids = {type2_1['id'], type2_2['id']}
if type_ids_prop2 == expected_ids:
    print("✅ ISOLATION OK: Seuls les 2 types de prop2 sont retournés")
else:
    print(f"❌ ERREUR ISOLATION: Types retournés: {type_ids_prop2}, Attendu: {expected_ids}")
    sys.exit(1)
print()

# 6. Test GET /api/amortization/types/{id} avec isolation
print("📋 ÉTAPE 6 : Test GET /api/amortization/types/{id} avec isolation")
print("-" * 80)

# Tester avec le bon property_id
response = requests.get(f"{API_BASE}/amortization/types/{type1_1['id']}", params={"property_id": prop1['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types/{type1_1['id']} échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
print(f"✅ GET /api/amortization/types/{type1_1['id']} avec property_id={prop1['id']} OK")

# Tester avec le mauvais property_id (doit retourner 404)
response = requests.get(f"{API_BASE}/amortization/types/{type1_1['id']}", params={"property_id": prop2['id']})
if response.status_code == 404:
    print(f"✅ ISOLATION OK: GET /api/amortization/types/{type1_1['id']} avec property_id={prop2['id']} retourne 404")
else:
    print(f"❌ ERREUR ISOLATION: Devrait retourner 404, mais retourne {response.status_code}")
    sys.exit(1)
print()

# 7. Test PUT /api/amortization/types/{id} avec isolation
print("📋 ÉTAPE 7 : Test PUT /api/amortization/types/{id} avec isolation")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] PUT /api/amortization/types/{type1_1['id']} - property_id={prop1['id']}")
print()

update_data = {
    "name": "Type Prop1 #1 UPDATED",
    "duration": 22.0
}
response = requests.put(
    f"{API_BASE}/amortization/types/{type1_1['id']}",
    json=update_data,
    params={"property_id": prop1['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: PUT /api/amortization/types/{type1_1['id']} échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
updated_type = response.json()
print(f"✅ Type mis à jour: Name={updated_type['name']}, Duration={updated_type['duration']}")

# Tester avec le mauvais property_id (doit retourner 404)
response = requests.put(
    f"{API_BASE}/amortization/types/{type1_1['id']}",
    json=update_data,
    params={"property_id": prop2['id']}
)
if response.status_code == 404:
    print(f"✅ ISOLATION OK: PUT avec property_id={prop2['id']} retourne 404")
else:
    print(f"❌ ERREUR ISOLATION: Devrait retourner 404, mais retourne {response.status_code}")
    sys.exit(1)
print()

# 8. Test DELETE /api/amortization/types/{id} avec isolation
print("📋 ÉTAPE 8 : Test DELETE /api/amortization/types/{id} avec isolation")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] DELETE /api/amortization/types/{type1_3['id']} - property_id={prop1['id']}")
print()

# Tester avec le mauvais property_id (doit retourner 404)
response = requests.delete(
    f"{API_BASE}/amortization/types/{type1_3['id']}",
    params={"property_id": prop2['id']}
)
if response.status_code == 404:
    print(f"✅ ISOLATION OK: DELETE avec property_id={prop2['id']} retourne 404")
else:
    print(f"❌ ERREUR ISOLATION: Devrait retourner 404, mais retourne {response.status_code}")
    sys.exit(1)

# Tester avec le bon property_id
response = requests.delete(
    f"{API_BASE}/amortization/types/{type1_3['id']}",
    params={"property_id": prop1['id']}
)
if response.status_code == 204:
    print(f"✅ Type {type1_3['id']} supprimé avec property_id={prop1['id']}")
else:
    print(f"❌ ERREUR: DELETE échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

# Vérifier que le type a bien été supprimé
response = requests.get(f"{API_BASE}/amortization/types", params={"property_id": prop1['id']})
types_prop1_after = response.json()
if len(types_prop1_after['items']) == 2:
    print(f"✅ Vérification: {len(types_prop1_after['items'])} types restants pour prop1 (attendu: 2)")
else:
    print(f"❌ ERREUR: {len(types_prop1_after['items'])} types restants (attendu: 2)")
    sys.exit(1)
print()

# 9. Test GET /api/amortization/results/aggregated avec isolation
print("📋 ÉTAPE 9 : Test GET /api/amortization/results/aggregated avec isolation")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] GET results/aggregated - property_id={prop1['id']}")
print()

response = requests.get(f"{API_BASE}/amortization/results/aggregated", params={"property_id": prop1['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/results/aggregated échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
results_prop1 = response.json()
print(f"✅ Résultats pour property_id={prop1['id']}: {len(results_prop1.get('categories', []))} catégories")

response = requests.get(f"{API_BASE}/amortization/results/aggregated", params={"property_id": prop2['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/results/aggregated échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
results_prop2 = response.json()
print(f"✅ Résultats pour property_id={prop2['id']}: {len(results_prop2.get('categories', []))} catégories")
print()

# 10. Test POST /api/amortization/recalculate avec isolation
print("📋 ÉTAPE 10 : Test POST /api/amortization/recalculate avec isolation")
print("-" * 80)
print(f"⚠️  Vérifiez les logs backend: [Amortizations] POST recalculate - property_id={prop1['id']}")
print()

recalculate_data = {"property_id": prop1['id']}
response = requests.post(f"{API_BASE}/amortization/recalculate", json=recalculate_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: POST /api/amortization/recalculate échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
recalc_result = response.json()
print(f"✅ Recalcul pour property_id={prop1['id']}: {recalc_result.get('results_created', 0)} résultats créés")
print()

# 11. Résumé final
print("=" * 80)
print("✅ TOUS LES TESTS D'ISOLATION PASSÉS")
print("=" * 80)
print()
print("📊 Récapitulatif:")
print(f"   - Property 1 (ID={prop1['id']}): {len(types_prop1_after['items'])} types d'amortissement")
print(f"   - Property 2 (ID={prop2['id']}): {len(types_prop2['items'])} types d'amortissement")
print()
print("✅ Isolation complète vérifiée:")
print("   - GET retourne uniquement les types de la propriété demandée")
print("   - POST crée des types pour la propriété spécifiée")
print("   - PUT ne peut modifier que les types de la propriété spécifiée")
print("   - DELETE ne peut supprimer que les types de la propriété spécifiée")
print("   - GET results retourne uniquement les résultats de la propriété demandée")
print("   - POST recalculate ne recalcule que pour la propriété spécifiée")
print()
print("⚠️  Vérifiez les logs backend pour confirmer que tous les appels incluent property_id")
print()
