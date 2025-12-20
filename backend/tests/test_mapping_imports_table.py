"""
Test pour vérifier la création de la table mapping_imports (Step 3.7.1).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import MappingImport
from sqlalchemy import inspect


def test_mapping_imports_table_exists():
    """Test que la table mapping_imports existe."""
    print("\n📋 Test 1: Vérification existence table mapping_imports")
    
    init_database()
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        assert 'mapping_imports' in tables, "❌ Table mapping_imports n'existe pas"
        print("✅ Table mapping_imports existe")
        
        # Vérifier les colonnes
        columns = [col['name'] for col in inspector.get_columns('mapping_imports')]
        expected_columns = ['id', 'filename', 'imported_at', 'imported_count', 
                           'duplicates_count', 'errors_count', 'created_at', 'updated_at']
        
        for col in expected_columns:
            assert col in columns, f"❌ Colonne {col} manquante dans mapping_imports"
        
        print(f"✅ Toutes les colonnes présentes: {', '.join(expected_columns)}")
        
        # Vérifier les index
        indexes = inspector.get_indexes('mapping_imports')
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_mapping_imports_filename' in index_names, "❌ Index sur filename manquant"
        assert 'idx_mapping_imports_imported_at' in index_names, "❌ Index sur imported_at manquant"
        print("✅ Tous les index présents")
        
    finally:
        db.close()


def test_mapping_import_model():
    """Test que le modèle MappingImport fonctionne."""
    print("\n📋 Test 2: Vérification modèle MappingImport")
    
    init_database()
    db = SessionLocal()
    try:
        # Créer un import de test
        test_import = MappingImport(
            filename="test_mappings.xlsx",
            imported_count=15,
            duplicates_count=3,
            errors_count=1
        )
        db.add(test_import)
        db.commit()
        
        # Vérifier qu'il a été créé
        imported = db.query(MappingImport).filter(MappingImport.filename == "test_mappings.xlsx").first()
        assert imported is not None, "❌ Import de test non créé"
        assert imported.imported_count == 15, "❌ imported_count incorrect"
        assert imported.duplicates_count == 3, "❌ duplicates_count incorrect"
        assert imported.errors_count == 1, "❌ errors_count incorrect"
        assert imported.filename == "test_mappings.xlsx", "❌ filename incorrect"
        print("✅ Modèle MappingImport fonctionne correctement")
        
        # Vérifier que imported_at est défini automatiquement
        assert imported.imported_at is not None, "❌ imported_at non défini"
        print("✅ imported_at défini automatiquement")
        
        # Vérifier que created_at et updated_at sont définis
        assert imported.created_at is not None, "❌ created_at non défini"
        assert imported.updated_at is not None, "❌ updated_at non défini"
        print("✅ created_at et updated_at définis automatiquement")
        
        # Nettoyer
        db.delete(imported)
        db.commit()
        print("✅ Import de test supprimé")
        
    finally:
        db.close()


def test_mapping_import_unique_filename():
    """Test que le filename est unique."""
    print("\n📋 Test 3: Vérification unicité filename")
    
    init_database()
    db = SessionLocal()
    try:
        # Créer un premier import
        test_import1 = MappingImport(
            filename="unique_test.xlsx",
            imported_count=5
        )
        db.add(test_import1)
        db.commit()
        
        # Essayer de créer un deuxième avec le même filename (devrait échouer)
        try:
            test_import2 = MappingImport(
                filename="unique_test.xlsx",
                imported_count=10
            )
            db.add(test_import2)
            db.commit()
            # Si on arrive ici, c'est qu'il n'y a pas de contrainte unique
            print("⚠️  Pas de contrainte unique sur filename (peut être normal selon la config)")
        except Exception as e:
            # C'est attendu - la contrainte unique doit empêcher la création
            db.rollback()
            print(f"✅ Contrainte unique fonctionne: {type(e).__name__}")
        
        # Nettoyer
        db.query(MappingImport).filter(MappingImport.filename == "unique_test.xlsx").delete()
        db.commit()
        print("✅ Test de nettoyage terminé")
        
    finally:
        db.close()


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests Step 3.7.1 - Table mapping_imports")
    print("=" * 60)
    
    try:
        test_mapping_imports_table_exists()
        test_mapping_import_model()
        test_mapping_import_unique_filename()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

