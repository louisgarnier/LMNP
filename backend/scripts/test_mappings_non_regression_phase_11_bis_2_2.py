"""
Test Step 2.2 : Non-régression - Vérification que toutes les fonctionnalités existantes fonctionnent

Ce script teste que toutes les fonctionnalités de l'onglet Mappings fonctionnent correctement
après l'ajout de property_id.

⚠️ IMPORTANT : Ce script doit être exécuté avec le serveur backend démarré.
"""

import sys
import os
import requests
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Générer un nom unique avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 80)
print("TEST DE NON-RÉGRESSION - Step 2.2 - MAPPINGS")
print("Vérification que toutes les fonctionnalités existantes fonctionnent")
print("=" * 80)
print()
print("⚠️  ASSUREZ-VOUS QUE LE SERVEUR BACKEND EST DÉMARRÉ")
print()
print("=" * 80)
print()

# 1. Créer une propriété de test
print("📋 ÉTAPE 1 : Création d'une propriété de test")
print("-" * 80)

prop_data = {"name": f"Test Non-Regression Mappings_{timestamp}", "address": "123 Test Street"}
response = requests.post(f"{API_BASE}/properties", json=prop_data)
if response.status_code not in [200, 201]:
    print(f"❌ ERREUR: Impossible de créer la propriété: {response.status_code}")
    print(response.text)
    sys.exit(1)
prop = response.json()
property_id = prop['id']
print(f"✅ Propriété créée: ID={property_id}, Name={prop['name']}")
print()

# 2. Test : Affichage des mappings avec pagination
print("📋 ÉTAPE 2 : Test - Affichage des mappings avec pagination")
print("-" * 80)

response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de récupérer les mappings: {response.status_code}")
    print(response.text)
    sys.exit(1)
data = response.json()
print(f"✅ Mappings récupérés: {data['total']} total, {len(data['mappings'])} dans cette page")
print(f"   - Pagination fonctionne (skip=0, limit=10)")
print()

# 3. Test : Création d'un mapping
print("📋 ÉTAPE 3 : Test - Création d'un mapping")
print("-" * 80)

mapping_data = {
    "property_id": property_id,
    "nom": f"Test Mapping Non-Regression_{timestamp}",
    "level_1": "Revenus",
    "level_2": "Loyers",
    "level_3": "Loyer principal",
    "is_prefix_match": False,
    "priority": 1
}
response = requests.post(f"{API_BASE}/mappings", json=mapping_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer le mapping: {response.status_code}")
    print(response.text)
    sys.exit(1)
mapping = response.json()
mapping_id = mapping['id']
print(f"✅ Mapping créé: ID={mapping_id}, nom={mapping['nom']}")
print()

# 4. Test : Tri par colonne
print("📋 ÉTAPE 4 : Test - Tri par colonne")
print("-" * 80)

# Test tri par nom (asc)
response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&sort_by=nom&sort_direction=asc&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Tri par nom échoué: {response.status_code}")
    sys.exit(1)
print("✅ Tri par nom (asc) fonctionne")

# Test tri par level_1 (desc)
response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&sort_by=level_1&sort_direction=desc&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Tri par level_1 échoué: {response.status_code}")
    sys.exit(1)
print("✅ Tri par level_1 (desc) fonctionne")
print()

# 5. Test : Filtres
print("📋 ÉTAPE 5 : Test - Filtres")
print("-" * 80)

# Test filtre par nom
response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&filter_nom=Test&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Filtre par nom échoué: {response.status_code}")
    sys.exit(1)
filtered_data = response.json()
print(f"✅ Filtre par nom fonctionne: {filtered_data['total']} mapping(s) trouvé(s)")

# Test filtre par level_1
response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&filter_level_1=Revenus&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Filtre par level_1 échoué: {response.status_code}")
    sys.exit(1)
filtered_data = response.json()
print(f"✅ Filtre par level_1 fonctionne: {filtered_data['total']} mapping(s) trouvé(s)")

# Test filtre par level_2
response = requests.get(f"{API_BASE}/mappings?property_id={property_id}&filter_level_2=Loyers&skip=0&limit=10")
if response.status_code != 200:
    print(f"❌ ERREUR: Filtre par level_2 échoué: {response.status_code}")
    sys.exit(1)
filtered_data = response.json()
print(f"✅ Filtre par level_2 fonctionne: {filtered_data['total']} mapping(s) trouvé(s)")
print()

# 6. Test : Édition d'un mapping
print("📋 ÉTAPE 6 : Test - Édition d'un mapping")
print("-" * 80)

update_data = {"nom": f"Test Mapping Non-Regression UPDATED_{timestamp}"}
response = requests.put(f"{API_BASE}/mappings/{mapping_id}?property_id={property_id}", json=update_data)
if response.status_code != 200:
    print(f"❌ ERREUR: Impossible de mettre à jour le mapping: {response.status_code}")
    print(response.text)
    sys.exit(1)
updated = response.json()
if updated['nom'] != update_data['nom']:
    print(f"❌ ERREUR: La mise à jour n'a pas fonctionné (attendu: {update_data['nom']}, obtenu: {updated['nom']})")
    sys.exit(1)
print(f"✅ Édition fonctionne: nom mis à jour vers '{updated['nom']}'")
print()

# 7. Test : Suppression d'un mapping
print("📋 ÉTAPE 7 : Test - Suppression d'un mapping")
print("-" * 80)

# Créer un mapping à supprimer
mapping_to_delete_data = {
    "property_id": property_id,
    "nom": f"Test Mapping To Delete_{timestamp}",
    "level_1": "Charges",
    "level_2": "Entretien",
    "level_3": None,
    "is_prefix_match": False,
    "priority": 1
}
response = requests.post(f"{API_BASE}/mappings", json=mapping_to_delete_data)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer le mapping à supprimer: {response.status_code}")
    sys.exit(1)
mapping_to_delete = response.json()
delete_id = mapping_to_delete['id']

# Supprimer le mapping
response = requests.delete(f"{API_BASE}/mappings/{delete_id}?property_id={property_id}")
if response.status_code != 204:
    print(f"❌ ERREUR: Impossible de supprimer le mapping: {response.status_code}")
    print(response.text)
    sys.exit(1)

# Vérifier que le mapping a été supprimé
response = requests.get(f"{API_BASE}/mappings/{delete_id}?property_id={property_id}")
if response.status_code != 404:
    print(f"❌ ERREUR: Le mapping devrait être supprimé (attendu 404, obtenu {response.status_code})")
    sys.exit(1)
print(f"✅ Suppression fonctionne: mapping ID={delete_id} supprimé")
print()

# 8. Test : Export Excel/CSV
print("📋 ÉTAPE 8 : Test - Export Excel/CSV")
print("-" * 80)

# Test export Excel
response = requests.get(f"{API_BASE}/mappings/export?property_id={property_id}&format=excel")
if response.status_code != 200:
    print(f"❌ ERREUR: Export Excel échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers.get('content-type', ''):
    print("✅ Export Excel fonctionne (format correct)")
else:
    print(f"⚠️  Export Excel: format inattendu ({response.headers.get('content-type')})")

# Test export CSV
response = requests.get(f"{API_BASE}/mappings/export?property_id={property_id}&format=csv")
if response.status_code != 200:
    print(f"❌ ERREUR: Export CSV échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
if 'text/csv' in response.headers.get('content-type', '') or 'application/csv' in response.headers.get('content-type', ''):
    print("✅ Export CSV fonctionne (format correct)")
else:
    print(f"⚠️  Export CSV: format inattendu ({response.headers.get('content-type')})")
print()

# 9. Test : Validation des combinaisons
print("📋 ÉTAPE 9 : Test - Validation des combinaisons")
print("-" * 80)

response = requests.get(f"{API_BASE}/mappings/combinations?property_id={property_id}")
if response.status_code != 200:
    print(f"❌ ERREUR: getCombinations échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
combinations = response.json()
print(f"✅ Validation des combinaisons fonctionne: {len(combinations)} combinaison(s) trouvée(s)")
print()

# 10. Test : Mappings autorisés - Affichage
print("📋 ÉTAPE 10 : Test - Mappings autorisés (Affichage)")
print("-" * 80)

response = requests.get(f"{API_BASE}/mappings/allowed?property_id={property_id}&skip=0&limit=100")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_mappings échoué: {response.status_code}")
    print(response.text)
    sys.exit(1)
allowed = response.json()
print(f"✅ Affichage des mappings autorisés fonctionne: {allowed['total']} mapping(s) autorisé(s)")
print()

# 11. Test : Mappings autorisés - Création
print("📋 ÉTAPE 11 : Test - Mappings autorisés (Création)")
print("-" * 80)

# L'endpoint attend les paramètres en query params, pas dans le body
# level_3 doit être une valeur autorisée : Passif, Produits, Emprunt, Charges Déductibles, Actif
params = {
    "property_id": property_id,
    "level_1": "Revenus",
    "level_2": "Loyers",
    "level_3": "Produits"  # Valeur autorisée
}
response = requests.post(f"{API_BASE}/mappings/allowed", params=params)
if response.status_code != 201:
    print(f"❌ ERREUR: Impossible de créer le mapping autorisé: {response.status_code}")
    print(response.text)
    sys.exit(1)
allowed_mapping = response.json()
allowed_mapping_id = allowed_mapping['id']
print(f"✅ Création d'un mapping autorisé fonctionne: ID={allowed_mapping_id}")
print()

# 12. Test : Mappings autorisés - Suppression
print("📋 ÉTAPE 12 : Test - Mappings autorisés (Suppression)")
print("-" * 80)

response = requests.delete(f"{API_BASE}/mappings/allowed/{allowed_mapping_id}?property_id={property_id}")
if response.status_code != 204:
    print(f"❌ ERREUR: Impossible de supprimer le mapping autorisé: {response.status_code}")
    print(response.text)
    sys.exit(1)
print(f"✅ Suppression d'un mapping autorisé fonctionne: ID={allowed_mapping_id} supprimé")
print()

# 13. Test : Mappings autorisés - Réinitialisation
print("📋 ÉTAPE 13 : Test - Mappings autorisés (Réinitialisation)")
print("-" * 80)

response = requests.post(f"{API_BASE}/mappings/allowed/reset?property_id={property_id}")
if response.status_code != 200:
    print(f"❌ ERREUR: Réinitialisation échouée: {response.status_code}")
    print(response.text)
    sys.exit(1)
reset_result = response.json()
print(f"✅ Réinitialisation des mappings hardcodés fonctionne: {reset_result.get('created_count', 0)} mapping(s) créé(s)")
print()

# 14. Test : Endpoints utilitaires
print("📋 ÉTAPE 14 : Test - Endpoints utilitaires")
print("-" * 80)

# Test get_allowed_level1
response = requests.get(f"{API_BASE}/mappings/allowed-level1?property_id={property_id}")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_level1 échoué: {response.status_code}")
    sys.exit(1)
print("✅ get_allowed_level1 fonctionne")

# Test get_allowed_level2
response = requests.get(f"{API_BASE}/mappings/allowed-level2?property_id={property_id}")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_level2 échoué: {response.status_code}")
    sys.exit(1)
print("✅ get_allowed_level2 fonctionne")

# Test get_allowed_level3 (nécessite level_1 et level_2)
response = requests.get(f"{API_BASE}/mappings/allowed-level3?property_id={property_id}&level_1=Revenus&level_2=Loyers")
if response.status_code != 200:
    print(f"❌ ERREUR: get_allowed_level3 échoué: {response.status_code}")
    sys.exit(1)
print("✅ get_allowed_level3 fonctionne")
print()

# Résultat final
print("=" * 80)
print("✅ TOUS LES TESTS DE NON-RÉGRESSION ONT RÉUSSI !")
print("=" * 80)
print()
print("📋 RÉSUMÉ DES TESTS:")
print("   ✅ Affichage des mappings avec pagination")
print("   ✅ Tri par colonne")
print("   ✅ Filtres (nom, level_1, level_2)")
print("   ✅ Création d'un mapping")
print("   ✅ Édition d'un mapping")
print("   ✅ Suppression d'un mapping")
print("   ✅ Export Excel/CSV")
print("   ✅ Validation des combinaisons")
print("   ✅ Mappings autorisés (affichage, création, suppression, réinitialisation)")
print("   ✅ Endpoints utilitaires")
print()
print("⚠️  NOTE: Les tests d'upload et d'import de fichiers nécessitent")
print("    une vérification manuelle dans l'interface frontend")
print()
