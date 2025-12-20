"""
Tests pour les endpoints historique et count mappings (Step 3.7.4).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import SessionLocal, init_database
from backend.database.models import Mapping, MappingImport

client = TestClient(app)


def setup_test_db():
    """Initialise la BDD de test."""
    init_database()
    db = SessionLocal()
    try:
        # Nettoyer les données de test
        db.query(Mapping).delete()
        db.query(MappingImport).delete()
        db.commit()
    finally:
        db.close()


def test_get_mappings_imports_history():
    """Test endpoint GET /api/mappings/imports"""
    print("\n📋 Test 1: GET /api/mappings/imports")
    
    setup_test_db()
    
    # Créer des imports de test
    db = SessionLocal()
    try:
        import1 = MappingImport(
            filename="test1.xlsx",
            imported_count=5,
            duplicates_count=1,
            errors_count=0,
            imported_at=datetime(2024, 1, 1, 10, 0, 0)
        )
        import2 = MappingImport(
            filename="test2.xlsx",
            imported_count=3,
            duplicates_count=0,
            errors_count=2,
            imported_at=datetime(2024, 1, 2, 10, 0, 0)
        )
        db.add(import1)
        db.add(import2)
        db.commit()
    finally:
        db.close()
    
    response = client.get("/api/mappings/imports")
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert isinstance(data, list), "❌ Réponse n'est pas une liste"
    assert len(data) == 2, f"❌ Nombre d'imports incorrect: {len(data)} (attendu: 2)"
    
    # Vérifier que les imports sont triés par date (plus récent en premier)
    assert data[0]["filename"] == "test2.xlsx", "❌ Tri par date incorrect (plus récent en premier)"
    assert data[1]["filename"] == "test1.xlsx", "❌ Tri par date incorrect"
    
    # Vérifier les champs
    first_import = data[0]
    assert "id" in first_import, "❌ Champ id manquant"
    assert "filename" in first_import, "❌ Champ filename manquant"
    assert "imported_at" in first_import, "❌ Champ imported_at manquant"
    assert "imported_count" in first_import, "❌ Champ imported_count manquant"
    assert "duplicates_count" in first_import, "❌ Champ duplicates_count manquant"
    assert "errors_count" in first_import, "❌ Champ errors_count manquant"
    
    assert first_import["filename"] == "test2.xlsx", "❌ Filename incorrect"
    assert first_import["imported_count"] == 3, "❌ Imported count incorrect"
    assert first_import["duplicates_count"] == 0, "❌ Duplicates count incorrect"
    assert first_import["errors_count"] == 2, "❌ Errors count incorrect"
    
    print("✅ Historique récupéré correctement")
    print(f"✅ {len(data)} imports dans l'historique")


def test_delete_mapping_import():
    """Test endpoint DELETE /api/mappings/imports/{import_id}"""
    print("\n📋 Test 2: DELETE /api/mappings/imports/{import_id}")
    
    setup_test_db()
    
    # Créer un import de test
    db = SessionLocal()
    try:
        import_test = MappingImport(
            filename="test_delete.xlsx",
            imported_count=2,
            duplicates_count=0,
            errors_count=0
        )
        db.add(import_test)
        db.commit()
        import_id = import_test.id
    finally:
        db.close()
    
    # Supprimer l'import
    response = client.delete(f"/api/mappings/imports/{import_id}")
    
    assert response.status_code == 204, f"❌ Status code attendu: 204, obtenu: {response.status_code}"
    
    # Vérifier que l'import a été supprimé
    db = SessionLocal()
    try:
        deleted_import = db.query(MappingImport).filter(MappingImport.id == import_id).first()
        assert deleted_import is None, "❌ Import non supprimé"
    finally:
        db.close()
    
    print("✅ Import supprimé correctement")


def test_delete_mapping_import_not_found():
    """Test endpoint DELETE /api/mappings/imports/{import_id} avec ID inexistant"""
    print("\n📋 Test 3: DELETE /api/mappings/imports/{import_id} (ID inexistant)")
    
    setup_test_db()
    
    response = client.delete("/api/mappings/imports/99999")
    
    assert response.status_code == 404, f"❌ Status code attendu: 404, obtenu: {response.status_code}"
    
    data = response.json()
    assert "non trouvé" in data["detail"].lower(), "❌ Message d'erreur incorrect"
    
    print("✅ Erreur 404 correcte pour ID inexistant")


def test_get_mappings_count():
    """Test endpoint GET /api/mappings/count"""
    print("\n📋 Test 4: GET /api/mappings/count")
    
    setup_test_db()
    
    # Créer des mappings de test
    db = SessionLocal()
    try:
        mapping1 = Mapping(
            nom="PRLV SEPA",
            level_1="CHARGES",
            level_2="FRAIS BANCAIRES",
            level_3="PRLV"
        )
        mapping2 = Mapping(
            nom="VIR STRIPE",
            level_1="PRODUITS",
            level_2="REVENUS LOCATIFS",
            level_3="STRIPE"
        )
        mapping3 = Mapping(
            nom="CARTE",
            level_1="CHARGES",
            level_2="FRAIS BANCAIRES",
            level_3="CARTE BLEUE"
        )
        db.add(mapping1)
        db.add(mapping2)
        db.add(mapping3)
        db.commit()
    finally:
        db.close()
    
    response = client.get("/api/mappings/count")
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert "count" in data, "❌ Champ count manquant"
    assert data["count"] == 3, f"❌ Count incorrect: {data['count']} (attendu: 3)"
    
    print(f"✅ Compteur correct: {data['count']} mappings")


def test_get_mappings_count_empty():
    """Test endpoint GET /api/mappings/count avec BDD vide"""
    print("\n📋 Test 5: GET /api/mappings/count (BDD vide)")
    
    setup_test_db()
    
    response = client.get("/api/mappings/count")
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert data["count"] == 0, f"❌ Count incorrect: {data['count']} (attendu: 0)"
    
    print("✅ Compteur correct pour BDD vide: 0 mappings")


def test_routing_conflicts():
    """Test que les routes sont bien placées (pas de conflit avec /mappings/{mapping_id})"""
    print("\n📋 Test 6: Vérification routing (pas de conflit)")
    
    setup_test_db()
    
    # Créer un mapping de test
    db = SessionLocal()
    try:
        mapping = Mapping(
            nom="TEST ROUTING",
            level_1="CHARGES",
            level_2="FRAIS BANCAIRES"
        )
        db.add(mapping)
        db.commit()
        mapping_id = mapping.id
    finally:
        db.close()
    
    # Tester que /api/mappings/count fonctionne (ne doit pas matcher /mappings/{mapping_id})
    response = client.get("/api/mappings/count")
    assert response.status_code == 200, "❌ Route /mappings/count ne fonctionne pas (conflit de routing?)"
    assert "count" in response.json(), "❌ Route /mappings/count ne retourne pas count"
    
    # Tester que /api/mappings/imports fonctionne
    response = client.get("/api/mappings/imports")
    assert response.status_code == 200, "❌ Route /mappings/imports ne fonctionne pas (conflit de routing?)"
    assert isinstance(response.json(), list), "❌ Route /mappings/imports ne retourne pas une liste"
    
    # Tester que /api/mappings/{mapping_id} fonctionne toujours
    response = client.get(f"/api/mappings/{mapping_id}")
    assert response.status_code == 200, "❌ Route /mappings/{mapping_id} ne fonctionne plus"
    assert response.json()["id"] == mapping_id, "❌ Route /mappings/{mapping_id} retourne le mauvais mapping"
    
    print("✅ Pas de conflit de routing, toutes les routes fonctionnent")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests Step 3.7.4 - Endpoints historique et count")
    print("=" * 60)
    
    try:
        test_get_mappings_imports_history()
        test_delete_mapping_import()
        test_delete_mapping_import_not_found()
        test_get_mappings_count()
        test_get_mappings_count_empty()
        test_routing_conflicts()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

