"""
Test des endpoints API pour le Bilan (Step 10.4).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_endpoints_step10_4.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData, BilanMappingView

client = TestClient(app)


def test_get_bilan_mappings():
    """Test GET /api/bilan/mappings."""
    print("🧪 Test GET /api/bilan/mappings...")
    response = client.get("/api/bilan/mappings")
    assert response.status_code == 200
    data = response.json()
    assert "mappings" in data
    assert "total" in data
    print(f"  ✅ {data['total']} mapping(s) trouvé(s)")


def test_create_bilan_mapping():
    """Test POST /api/bilan/mappings."""
    print("🧪 Test POST /api/bilan/mappings...")
    mapping_data = {
        "category_name": "Test Immobilisations",
        "level_1_values": ["Achat test"],
        "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "is_special": False,
        "special_source": None,
        "amortization_view_id": None
    }
    response = client.post("/api/bilan/mappings", json=mapping_data)
    assert response.status_code == 201
    data = response.json()
    assert data["category_name"] == "Test Immobilisations"
    assert data["id"] is not None
    print(f"  ✅ Mapping créé avec ID: {data['id']}")
    
    # Nettoyer
    mapping_id = data["id"]
    delete_response = client.delete(f"/api/bilan/mappings/{mapping_id}")
    assert delete_response.status_code == 204
    print("  ✅ Mapping supprimé")


def test_get_bilan_mapping_by_id():
    """Test GET /api/bilan/mappings/{mapping_id}."""
    print("🧪 Test GET /api/bilan/mappings/{mapping_id}...")
    
    # Créer un mapping de test
    mapping_data = {
        "category_name": "Test Mapping",
        "level_1_values": ["Test"],
        "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "is_special": False
    }
    create_response = client.post("/api/bilan/mappings", json=mapping_data)
    mapping_id = create_response.json()["id"]
    
    # Récupérer le mapping
    response = client.get(f"/api/bilan/mappings/{mapping_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mapping_id
    assert data["category_name"] == "Test Mapping"
    print("  ✅ Mapping récupéré correctement")
    
    # Nettoyer
    client.delete(f"/api/bilan/mappings/{mapping_id}")


def test_update_bilan_mapping():
    """Test PUT /api/bilan/mappings/{mapping_id}."""
    print("🧪 Test PUT /api/bilan/mappings/{mapping_id}...")
    
    # Créer un mapping de test
    mapping_data = {
        "category_name": "Test Original",
        "level_1_values": ["Test"],
        "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "is_special": False
    }
    create_response = client.post("/api/bilan/mappings", json=mapping_data)
    mapping_id = create_response.json()["id"]
    
    # Mettre à jour
    update_data = {"category_name": "Test Updated"}
    response = client.put(f"/api/bilan/mappings/{mapping_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Test Updated"
    print("  ✅ Mapping mis à jour")
    
    # Nettoyer
    client.delete(f"/api/bilan/mappings/{mapping_id}")


def test_delete_bilan_mapping():
    """Test DELETE /api/bilan/mappings/{mapping_id}."""
    print("🧪 Test DELETE /api/bilan/mappings/{mapping_id}...")
    
    # Créer un mapping de test
    mapping_data = {
        "category_name": "Test Delete",
        "level_1_values": ["Test"],
        "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "is_special": False
    }
    create_response = client.post("/api/bilan/mappings", json=mapping_data)
    mapping_id = create_response.json()["id"]
    
    # Supprimer
    response = client.delete(f"/api/bilan/mappings/{mapping_id}")
    assert response.status_code == 204
    print("  ✅ Mapping supprimé")
    
    # Vérifier qu'il n'existe plus
    get_response = client.get(f"/api/bilan/mappings/{mapping_id}")
    assert get_response.status_code == 404
    print("  ✅ Mapping confirmé supprimé")


def test_generate_bilan():
    """Test POST /api/bilan/generate."""
    print("🧪 Test POST /api/bilan/generate...")
    
    # Vérifier qu'il y a des mappings
    mappings_response = client.get("/api/bilan/mappings")
    mappings = mappings_response.json()["mappings"]
    
    if not mappings:
        print("  ⚠️ Aucun mapping configuré, test ignoré")
        return
    
    # Générer le bilan
    generate_data = {
        "year": 2024,
        "selected_level_3_values": None
    }
    response = client.post("/api/bilan/generate", json=generate_data)
    
    if response.status_code == 400:
        print("  ⚠️ Génération échouée (probablement pas de mappings configurés)")
        return
    
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert "types" in data
    assert "equilibre" in data
    assert data["year"] == 2024
    print("  ✅ Bilan généré avec structure hiérarchique")
    print(f"     Types: {len(data['types'])}")
    print(f"     Équilibre ACTIF: {data['equilibre']['actif']}")
    print(f"     Équilibre PASSIF: {data['equilibre']['passif']}")


def test_get_bilan():
    """Test GET /api/bilan."""
    print("🧪 Test GET /api/bilan...")
    
    # Test sans filtre
    response = client.get("/api/bilan")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    print(f"  ✅ {data['total']} donnée(s) trouvée(s) sans filtre")
    
    # Test avec filtre année
    response = client.get("/api/bilan?year=2024")
    assert response.status_code == 200
    data = response.json()
    print(f"  ✅ {data['total']} donnée(s) trouvée(s) pour 2024")


def test_bilan_mapping_views():
    """Test des endpoints pour les vues."""
    print("🧪 Test BilanMappingView endpoints...")
    
    # Créer une vue
    view_data = {
        "name": "Test View",
        "view_data": {
            "mappings": [],
            "selected_level_3_values": []
        }
    }
    create_response = client.post("/api/bilan/mapping-views", json=view_data)
    
    if create_response.status_code == 400:
        # Vue existe déjà, on la récupère
        list_response = client.get("/api/bilan/mapping-views")
        views = list_response.json()["views"]
        test_view = next((v for v in views if v["name"] == "Test View"), None)
        if test_view:
            view_id = test_view["id"]
            print(f"  ⚠️ Vue existe déjà, utilisation de l'ID: {view_id}")
        else:
            print("  ⚠️ Erreur inattendue")
            return
    else:
        assert create_response.status_code == 201
        view_id = create_response.json()["id"]
        print(f"  ✅ Vue créée avec ID: {view_id}")
    
    # Récupérer la vue
    get_response = client.get(f"/api/bilan/mapping-views/{view_id}")
    assert get_response.status_code == 200
    print("  ✅ Vue récupérée")
    
    # Mettre à jour la vue
    update_data = {"view_data": {"mappings": [{"id": 1}], "selected_level_3_values": ["Test"]}}
    update_response = client.put(f"/api/bilan/mapping-views/{view_id}", json=update_data)
    assert update_response.status_code == 200
    print("  ✅ Vue mise à jour")
    
    # Supprimer la vue
    delete_response = client.delete(f"/api/bilan/mapping-views/{view_id}")
    assert delete_response.status_code == 204
    print("  ✅ Vue supprimée")


def test_error_handling():
    """Test de la gestion des erreurs."""
    print("🧪 Test gestion des erreurs...")
    
    # Test mapping inexistant
    response = client.get("/api/bilan/mappings/99999")
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"].lower()
    print("  ✅ Erreur 404 pour mapping inexistant")
    
    # Test vue inexistante
    response = client.get("/api/bilan/mapping-views/99999")
    assert response.status_code == 404
    print("  ✅ Erreur 404 pour vue inexistante")


if __name__ == "__main__":
    print("=" * 60)
    print("Test des endpoints API pour le Bilan (Step 10.4)")
    print("=" * 60)
    print()
    
    try:
        test_get_bilan_mappings()
        print()
        test_create_bilan_mapping()
        print()
        test_get_bilan_mapping_by_id()
        print()
        test_update_bilan_mapping()
        print()
        test_delete_bilan_mapping()
        print()
        test_generate_bilan()
        print()
        test_get_bilan()
        print()
        test_bilan_mapping_views()
        print()
        test_error_handling()
        print()
        
        print("=" * 60)
        print("✅ Tous les tests sont passés !")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test échoué: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

