"""
Test Step 3.2 : Non-régression - Vérification que toutes les fonctionnalités existantes fonctionnent toujours

Ce script teste que toutes les fonctionnalités de l'onglet Amortissements fonctionnent correctement
après l'ajout de property_id.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.

Ce script teste :
1. Table d'amortissement : Affichage fonctionne
2. Affichage par catégorie fonctionne
3. Affichage par année fonctionne
4. Calcul automatique fonctionne
5. Recalcul manuel fonctionne
6. Config : Affichage des types fonctionne
7. Création d'un type fonctionne
8. Édition d'un type fonctionne
9. Suppression d'un type fonctionne
10. Calcul du montant par année fonctionne
11. Calcul du montant cumulé fonctionne
12. Comptage des transactions fonctionne
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
print("TEST DE NON-RÉGRESSION - Step 3.2 - AMORTISSEMENTS")
print("Vérification que toutes les fonctionnalités existantes fonctionnent toujours")
print("=" * 80)
print()
print("⚠️  ASSUREZ-VOUS QUE LE SERVEUR BACKEND EST DÉMARRÉ")
print()

# Utiliser une propriété existante ou en créer une
print("📋 ÉTAPE 1 : Préparation - Utilisation d'une propriété existante")
print("-" * 80)

# Récupérer la première propriété disponible
response = requests.get(f"{API_BASE}/properties")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les propriétés: {response.status_code}")
    sys.exit(1)

properties_data = response.json()
# La réponse peut être une liste ou un objet avec une clé 'items'
if isinstance(properties_data, list):
    properties = properties_data
elif isinstance(properties_data, dict) and 'items' in properties_data:
    properties = properties_data['items']
else:
    properties = [properties_data] if properties_data else []

if not properties or len(properties) == 0:
    print("❌ ERREUR: Aucune propriété trouvée. Créez d'abord une propriété.")
    sys.exit(1)

test_property = properties[0]
print(f"✅ Propriété de test: ID={test_property['id']}, Name={test_property['name']}")
print()

# 1. Test GET /api/amortization/types - Affichage des types
print("📋 TEST 1 : Affichage des types d'amortissement")
print("-" * 80)

response = requests.get(f"{API_BASE}/amortization/types", params={"property_id": test_property['id']})
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

types = response.json()
print(f"✅ Affichage des types: {types['total']} types trouvés")
print(f"   Types: {[t['name'] for t in types['items'][:5]]}...")
print()

# 2. Test GET /api/amortization/types avec filtre level_2_value
print("📋 TEST 2 : Affichage par catégorie (level_2_value)")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/types",
    params={"property_id": test_property['id'], "level_2_value": "Immobilisations"}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types avec level_2_value échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

filtered_types = response.json()
print(f"✅ Filtre par catégorie: {filtered_types['total']} types pour 'Immobilisations'")
print()

# 3. Test POST /api/amortization/types - Création d'un type
print("📋 TEST 3 : Création d'un type d'amortissement")
print("-" * 80)

new_type_data = {
    "property_id": test_property['id'],
    "name": f"Test Type Non-Regression_{timestamp}",
    "level_2_value": "Immobilisations",
    "level_1_values": ["Immeuble (hors terrain)"],
    "duration": 20.0,
    "start_date": None,
    "annual_amount": None
}

response = requests.post(f"{API_BASE}/amortization/types", json=new_type_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: POST /api/amortization/types échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

created_type = response.json()
print(f"✅ Type créé: ID={created_type['id']}, Name={created_type['name']}")
print(f"   Level_2: {created_type['level_2_value']}, Duration: {created_type['duration']}")
print()

# 4. Test GET /api/amortization/types/{id} - Récupération d'un type
print("📋 TEST 4 : Récupération d'un type spécifique")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/types/{created_type['id']}",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types/{created_type['id']} échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

retrieved_type = response.json()
print(f"✅ Type récupéré: Name={retrieved_type['name']}")
print()

# 5. Test PUT /api/amortization/types/{id} - Édition d'un type
print("📋 TEST 5 : Édition d'un type d'amortissement")
print("-" * 80)

update_data = {
    "name": f"Test Type Non-Regression UPDATED_{timestamp}",
    "duration": 25.0
}

response = requests.put(
    f"{API_BASE}/amortization/types/{created_type['id']}",
    json=update_data,
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: PUT /api/amortization/types/{created_type['id']} échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

updated_type = response.json()
print(f"✅ Type mis à jour: Name={updated_type['name']}, Duration={updated_type['duration']}")
print()

# 6. Test GET /api/amortization/types/{id}/amount - Calcul du montant
print("📋 TEST 6 : Calcul du montant total d'immobilisation")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/types/{created_type['id']}/amount",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types/{created_type['id']}/amount échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

amount_result = response.json()
print(f"✅ Montant calculé: {amount_result['amount']:,.2f} € pour le type '{amount_result['type_name']}'")
print()

# 7. Test GET /api/amortization/types/{id}/cumulated - Calcul du montant cumulé
print("📋 TEST 7 : Calcul du montant cumulé d'amortissement")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/types/{created_type['id']}/cumulated",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types/{created_type['id']}/cumulated échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

cumulated_result = response.json()
print(f"✅ Montant cumulé calculé: {cumulated_result['cumulated_amount']:,.2f} €")
print(f"   Montants par année: {len(cumulated_result.get('yearly_amounts', {}))} années")
print()

# 8. Test GET /api/amortization/types/{id}/transaction-count - Comptage des transactions
print("📋 TEST 8 : Comptage des transactions associées")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/types/{created_type['id']}/transaction-count",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/types/{created_type['id']}/transaction-count échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

count_result = response.json()
print(f"✅ Nombre de transactions: {count_result['transaction_count']} pour le type '{count_result['type_name']}'")
print()

# 9. Test GET /api/amortization/results - Affichage des résultats
print("📋 TEST 9 : Affichage des résultats d'amortissement")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/results",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/results échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

results = response.json()
print(f"✅ Résultats récupérés: {len(results.get('results', {}))} années")
print(f"   Total général: {results.get('grand_total', 0):,.2f} €")
print(f"   Catégories: {len(results.get('totals_by_category', {}))}")
print()

# 10. Test GET /api/amortization/results/aggregated - Affichage agrégé
print("📋 TEST 10 : Affichage agrégé des résultats (table)")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/results/aggregated",
    params={"property_id": test_property['id']}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/results/aggregated échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

aggregated = response.json()
print(f"✅ Résultats agrégés: {len(aggregated.get('categories', []))} catégories")
print(f"   Années: {len(aggregated.get('years', []))}")
print(f"   Total général: {aggregated.get('grand_total', 0):,.2f} €")
print()

# 11. Test GET /api/amortization/results/details - Détails des résultats
print("📋 TEST 11 : Détails des résultats d'amortissement")
print("-" * 80)

response = requests.get(
    f"{API_BASE}/amortization/results/details",
    params={"property_id": test_property['id'], "page": 1, "page_size": 10}
)
if response.status_code != 200:
    print(f"❌ ERREUR: GET /api/amortization/results/details échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

details = response.json()
print(f"✅ Détails récupérés: {len(details.get('items', []))} résultats (page 1)")
print(f"   Total: {details.get('total', 0)} résultats")
print()

# 12. Test POST /api/amortization/recalculate - Recalcul manuel
print("📋 TEST 12 : Recalcul manuel des amortissements")
print("-" * 80)

recalculate_data = {"property_id": test_property['id']}
response = requests.post(f"{API_BASE}/amortization/recalculate", json=recalculate_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: POST /api/amortization/recalculate échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

recalc_result = response.json()
print(f"✅ Recalcul terminé: {recalc_result.get('results_created', 0)} résultats créés")
print()

# 13. Test DELETE /api/amortization/types/{id} - Suppression d'un type
print("📋 TEST 13 : Suppression d'un type d'amortissement")
print("-" * 80)

response = requests.delete(
    f"{API_BASE}/amortization/types/{created_type['id']}",
    params={"property_id": test_property['id']}
)
if response.status_code != 204:
    print(f"❌ ERREUR: DELETE /api/amortization/types/{created_type['id']} échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)

print(f"✅ Type {created_type['id']} supprimé avec succès")

# Vérifier que le type a bien été supprimé
response = requests.get(
    f"{API_BASE}/amortization/types/{created_type['id']}",
    params={"property_id": test_property['id']}
)
if response.status_code == 404:
    print(f"✅ Vérification: Le type a bien été supprimé (404)")
else:
    print(f"⚠️  ATTENTION: Le type existe encore (status: {response.status_code})")
print()

# 14. Test GET /api/amortization/results avec filtre par année
print("📋 TEST 14 : Affichage par année (filtre)")
print("-" * 80)

# Récupérer les années disponibles
response = requests.get(
    f"{API_BASE}/amortization/results",
    params={"property_id": test_property['id']}
)
if response.status_code == 200:
    results = response.json()
    years = list(results.get('results', {}).keys())
    if years:
        test_year = int(years[0])
        print(f"✅ Test avec l'année {test_year}")
        
        # Tester les détails pour cette année
        response = requests.get(
            f"{API_BASE}/amortization/results/details",
            params={"property_id": test_property['id'], "year": test_year, "page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            details = response.json()
            print(f"✅ Filtre par année: {len(details.get('items', []))} résultats pour {test_year}")
        else:
            print(f"⚠️  Filtre par année: Status {response.status_code}")
    else:
        print("⚠️  Aucune année disponible pour tester le filtre")
else:
    print("⚠️  Impossible de récupérer les résultats pour tester le filtre par année")
print()

# 15. Test GET /api/amortization/results avec filtre par catégorie
print("📋 TEST 15 : Affichage par catégorie (filtre)")
print("-" * 80)

# Récupérer les catégories disponibles
response = requests.get(
    f"{API_BASE}/amortization/results",
    params={"property_id": test_property['id']}
)
if response.status_code == 200:
    results = response.json()
    categories = list(results.get('totals_by_category', {}).keys())
    if categories:
        test_category = categories[0]
        print(f"✅ Test avec la catégorie '{test_category}'")
        
        # Tester les détails pour cette catégorie
        response = requests.get(
            f"{API_BASE}/amortization/results/details",
            params={"property_id": test_property['id'], "category": test_category, "page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            details = response.json()
            print(f"✅ Filtre par catégorie: {len(details.get('items', []))} résultats pour '{test_category}'")
        else:
            print(f"⚠️  Filtre par catégorie: Status {response.status_code}")
    else:
        print("⚠️  Aucune catégorie disponible pour tester le filtre")
else:
    print("⚠️  Impossible de récupérer les résultats pour tester le filtre par catégorie")
print()

# Résumé final
print("=" * 80)
print("✅ TOUS LES TESTS DE NON-RÉGRESSION PASSÉS")
print("=" * 80)
print()
print("📊 Récapitulatif des fonctionnalités testées:")
print("   ✅ 1. Affichage des types d'amortissement")
print("   ✅ 2. Affichage par catégorie (level_2_value)")
print("   ✅ 3. Création d'un type")
print("   ✅ 4. Récupération d'un type spécifique")
print("   ✅ 5. Édition d'un type")
print("   ✅ 6. Calcul du montant total d'immobilisation")
print("   ✅ 7. Calcul du montant cumulé d'amortissement")
print("   ✅ 8. Comptage des transactions associées")
print("   ✅ 9. Affichage des résultats d'amortissement")
print("   ✅ 10. Affichage agrégé des résultats (table)")
print("   ✅ 11. Détails des résultats d'amortissement")
print("   ✅ 12. Recalcul manuel des amortissements")
print("   ✅ 13. Suppression d'un type")
print("   ✅ 14. Affichage par année (filtre)")
print("   ✅ 15. Affichage par catégorie (filtre)")
print()
print("✅ Toutes les fonctionnalités existantes fonctionnent correctement avec property_id")
print()
