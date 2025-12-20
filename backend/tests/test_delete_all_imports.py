"""
Test pour vérifier la suppression de tous les imports (Clear logs).

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
from backend.database.models import FileImport, MappingImport

client = TestClient(app)


def setup_test_db():
    """Initialise la BDD de test."""
    init_database()
    db = SessionLocal()
    try:
        # Nettoyer les données de test
        db.query(FileImport).delete()
        db.query(MappingImport).delete()
        db.commit()
    finally:
        db.close()


def test_delete_all_transaction_imports():
    """Test endpoint DELETE /api/transactions/imports (supprimer tous)"""
    print("\n📋 Test 1: DELETE /api/transactions/imports (supprimer tous)")
    
    setup_test_db()
    
    # Créer des imports de test
    db = SessionLocal()
    try:
        import1 = FileImport(
            filename="test1.csv",
            imported_count=5,
            duplicates_count=1,
            errors_count=0
        )
        import2 = FileImport(
            filename="test2.csv",
            imported_count=3,
            duplicates_count=0,
            errors_count=2
        )
        db.add(import1)
        db.add(import2)
        db.commit()
        
        # Vérifier qu'ils existent
        count_before = db.query(FileImport).count()
        assert count_before == 2, f"❌ Nombre d'imports avant suppression incorrect: {count_before}"
        print(f"✅ {count_before} imports créés")
    finally:
        db.close()
    
    # Supprimer tous les imports
    response = client.delete("/api/transactions/imports")
    
    assert response.status_code == 204, f"❌ Status code attendu: 204, obtenu: {response.status_code}"
    
    # Vérifier qu'ils ont été supprimés
    db = SessionLocal()
    try:
        count_after = db.query(FileImport).count()
        assert count_after == 0, f"❌ Nombre d'imports après suppression incorrect: {count_after} (attendu: 0)"
        print(f"✅ Tous les imports supprimés (0 restants)")
    finally:
        db.close()


def test_delete_all_mapping_imports():
    """Test endpoint DELETE /api/mappings/imports (supprimer tous)"""
    print("\n📋 Test 2: DELETE /api/mappings/imports (supprimer tous)")
    
    setup_test_db()
    
    # Créer des imports de test
    db = SessionLocal()
    try:
        import1 = MappingImport(
            filename="test1.xlsx",
            imported_count=5,
            duplicates_count=1,
            errors_count=0
        )
        import2 = MappingImport(
            filename="test2.xlsx",
            imported_count=3,
            duplicates_count=0,
            errors_count=2
        )
        db.add(import1)
        db.add(import2)
        db.commit()
        
        # Vérifier qu'ils existent
        count_before = db.query(MappingImport).count()
        assert count_before == 2, f"❌ Nombre d'imports avant suppression incorrect: {count_before}"
        print(f"✅ {count_before} imports créés")
    finally:
        db.close()
    
    # Supprimer tous les imports
    response = client.delete("/api/mappings/imports")
    
    assert response.status_code == 204, f"❌ Status code attendu: 204, obtenu: {response.status_code}"
    
    # Vérifier qu'ils ont été supprimés
    db = SessionLocal()
    try:
        count_after = db.query(MappingImport).count()
        assert count_after == 0, f"❌ Nombre d'imports après suppression incorrect: {count_after} (attendu: 0)"
        print(f"✅ Tous les imports supprimés (0 restants)")
    finally:
        db.close()


def test_delete_all_when_empty():
    """Test suppression quand il n'y a rien à supprimer"""
    print("\n📋 Test 3: DELETE /api/transactions/imports (BDD vide)")
    
    setup_test_db()
    
    # Supprimer tous les imports (même s'il n'y en a pas)
    response = client.delete("/api/transactions/imports")
    
    assert response.status_code == 204, f"❌ Status code attendu: 204, obtenu: {response.status_code}"
    print("✅ Suppression fonctionne même avec BDD vide")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests - Suppression de tous les imports (Clear logs)")
    print("=" * 60)
    
    try:
        test_delete_all_transaction_imports()
        test_delete_all_mapping_imports()
        test_delete_all_when_empty()
        
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

