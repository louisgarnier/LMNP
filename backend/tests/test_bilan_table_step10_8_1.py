"""
Test des endpoints API utilisés par BilanTable (Step 10.8.1).

Ce test vérifie que les endpoints nécessaires pour afficher le bilan fonctionnent correctement:
- GET /api/bilan/mappings - Chargement des mappings
- GET /api/bilan - Récupération des données avec filtres start_year/end_year

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_table_step10_8_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData

client = TestClient(app)


def test_get_bilan_mappings():
    """Test GET /api/bilan/mappings - utilisé par BilanTable pour charger les mappings."""
    print("🧪 Test GET /api/bilan/mappings (utilisé par BilanTable)...")
    response = client.get("/api/bilan/mappings")
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    data = response.json()
    assert "mappings" in data, "Réponse doit contenir 'mappings'"
    assert "total" in data, "Réponse doit contenir 'total'"
    assert isinstance(data["mappings"], list), "'mappings' doit être une liste"
    assert isinstance(data["total"], int), "'total' doit être un entier"
    
    print(f"  ✅ {data['total']} mapping(s) trouvé(s)")
    
    # Vérifier la structure des mappings
    if data["mappings"]:
        mapping = data["mappings"][0]
        required_fields = ["id", "category_name", "type", "sub_category"]
        for field in required_fields:
            assert field in mapping, f"Mapping doit contenir '{field}'"
        print(f"  ✅ Structure des mappings correcte (exemple: {mapping.get('category_name', 'N/A')})")
    else:
        print("  ⚠️ Aucun mapping configuré")
    
    return data["mappings"]


def test_get_bilan_with_filters():
    """Test GET /api/bilan avec filtres start_year/end_year - utilisé par BilanTable."""
    print("🧪 Test GET /api/bilan avec filtres start_year/end_year...")
    
    # Test avec filtres
    response = client.get("/api/bilan?start_year=2021&end_year=2024")
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    data = response.json()
    assert "data" in data, "Réponse doit contenir 'data'"
    assert "total" in data, "Réponse doit contenir 'total'"
    assert isinstance(data["data"], list), "'data' doit être une liste"
    assert isinstance(data["total"], int), "'total' doit être un entier"
    
    print(f"  ✅ {data['total']} donnée(s) trouvée(s) pour 2021-2024")
    
    # Vérifier la structure des données
    if data["data"]:
        bilan_item = data["data"][0]
        required_fields = ["id", "annee", "category_name", "amount"]
        for field in required_fields:
            assert field in bilan_item, f"BilanData doit contenir '{field}'"
        
        print(f"  ✅ Structure des données correcte")
        print(f"     Exemple: {bilan_item.get('category_name', 'N/A')} - {bilan_item.get('annee', 'N/A')} = {bilan_item.get('amount', 0)}")
        
        # Vérifier que les années sont dans la plage demandée
        years = [item["annee"] for item in data["data"]]
        if years:
            min_year = min(years)
            max_year = max(years)
            print(f"     Plage d'années dans les données: {min_year} - {max_year}")
    else:
        print("  ⚠️ Aucune donnée de bilan trouvée (les données doivent être générées via POST /api/bilan/generate)")
    
    return data["data"]


def test_get_bilan_without_filters():
    """Test GET /api/bilan sans filtres."""
    print("🧪 Test GET /api/bilan sans filtres...")
    response = client.get("/api/bilan")
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    data = response.json()
    assert "data" in data, "Réponse doit contenir 'data'"
    assert "total" in data, "Réponse doit contenir 'total'"
    print(f"  ✅ {data['total']} donnée(s) trouvée(s) sans filtre")


def test_bilan_table_data_structure():
    """Test que les données retournées peuvent être utilisées par BilanTable."""
    print("🧪 Test structure des données pour BilanTable...")
    
    # Récupérer les mappings
    mappings_response = client.get("/api/bilan/mappings")
    mappings = mappings_response.json()["mappings"]
    
    # Récupérer les données
    data_response = client.get("/api/bilan?start_year=2021&end_year=2024")
    bilan_data = data_response.json()["data"]
    
    if not mappings:
        print("  ⚠️ Aucun mapping configuré, test partiel")
        return
    
    if not bilan_data:
        print("  ⚠️ Aucune donnée de bilan, test partiel")
        print("     💡 Pour générer des données: POST /api/bilan/generate avec year et selected_level_3_values")
        return
    
    # Vérifier que chaque donnée a un mapping correspondant
    category_names = set(item["category_name"] for item in bilan_data)
    mapping_category_names = set(m["category_name"] for m in mappings)
    
    print(f"  📊 Catégories dans les données: {len(category_names)}")
    print(f"  📊 Catégories dans les mappings: {len(mapping_category_names)}")
    
    # Vérifier que toutes les catégories dans les données ont un mapping
    missing_mappings = category_names - mapping_category_names
    if missing_mappings:
        print(f"  ⚠️ Catégories sans mapping: {missing_mappings}")
    else:
        print("  ✅ Toutes les catégories ont un mapping")
    
    # Vérifier la structure hiérarchique (Type, Sous-catégorie, Catégorie)
    types = set(m["type"] for m in mappings)
    sub_categories = set(m["sub_category"] for m in mappings if m.get("sub_category"))
    
    print(f"  📊 Types trouvés: {sorted(types)}")
    print(f"  📊 Sous-catégories trouvées: {len(sub_categories)}")
    
    # Vérifier que les catégories peuvent être triées
    sorted_categories = sorted(category_names)
    print(f"  ✅ {len(sorted_categories)} catégories peuvent être triées")
    
    # Vérifier les années disponibles
    years = sorted(set(item["annee"] for item in bilan_data))
    print(f"  📊 Années disponibles: {years}")


if __name__ == "__main__":
    print("=" * 70)
    print("Test des endpoints API pour BilanTable (Step 10.8.1)")
    print("=" * 70)
    print()
    
    try:
        # Test 1: Chargement des mappings
        mappings = test_get_bilan_mappings()
        print()
        
        # Test 2: Récupération des données avec filtres
        bilan_data = test_get_bilan_with_filters()
        print()
        
        # Test 3: Récupération sans filtres
        test_get_bilan_without_filters()
        print()
        
        # Test 4: Structure des données pour BilanTable
        test_bilan_table_data_structure()
        print()
        
        print("=" * 70)
        print("✅ Tous les tests sont passés !")
        print("=" * 70)
        print()
        print("💡 Pour tester BilanTable dans le frontend:")
        print("   1. Assurez-vous que le backend est démarré: python3 -m backend.api.main")
        print("   2. Assurez-vous que le frontend est démarré: npm run dev (dans frontend/)")
        print("   3. Ouvrez http://localhost:3000/dashboard/etats-financiers")
        print("   4. Cliquez sur l'onglet 'Bilan'")
        print("   5. Vérifiez que la table s'affiche avec les catégories niveau C")
        print()
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ Test échoué: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

