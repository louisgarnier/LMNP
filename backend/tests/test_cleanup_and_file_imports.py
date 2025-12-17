"""
Test pour vérifier le nettoyage de la BDD et la création de la table file_imports.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, EnrichedTransaction, FileImport
from sqlalchemy import inspect


def test_file_imports_table_exists():
    """Test que la table file_imports existe."""
    print("\n📋 Test 1: Vérification existence table file_imports")
    
    init_database()
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        assert 'file_imports' in tables, "❌ Table file_imports n'existe pas"
        print("✅ Table file_imports existe")
        
        # Vérifier les colonnes
        columns = [col['name'] for col in inspector.get_columns('file_imports')]
        expected_columns = ['id', 'filename', 'imported_at', 'imported_count', 
                           'duplicates_count', 'errors_count', 'period_start', 
                           'period_end', 'created_at', 'updated_at']
        
        for col in expected_columns:
            assert col in columns, f"❌ Colonne {col} manquante dans file_imports"
        
        print(f"✅ Toutes les colonnes présentes: {', '.join(expected_columns)}")
        
    finally:
        db.close()


def test_database_is_clean():
    """Test que la BDD est propre (0 transactions)."""
    print("\n📋 Test 2: Vérification BDD propre")
    
    init_database()
    db = SessionLocal()
    try:
        # Vérifier nombre de transactions
        transaction_count = db.query(Transaction).count()
        print(f"📊 Nombre de transactions: {transaction_count}")
        
        assert transaction_count == 0, f"❌ BDD contient {transaction_count} transactions (attendu: 0)"
        print("✅ BDD contient 0 transactions")
        
        # Vérifier nombre de transactions enrichies
        enriched_count = db.query(EnrichedTransaction).count()
        print(f"📊 Nombre de transactions enrichies: {enriched_count}")
        
        assert enriched_count == 0, f"❌ BDD contient {enriched_count} transactions enrichies (attendu: 0)"
        print("✅ BDD contient 0 transactions enrichies")
        
        # Vérifier nombre d'imports
        imports_count = db.query(FileImport).count()
        print(f"📊 Nombre d'imports: {imports_count}")
        print("✅ Table file_imports est vide (normal pour le moment)")
        
    finally:
        db.close()


def test_file_import_model():
    """Test que le modèle FileImport fonctionne."""
    print("\n📋 Test 3: Vérification modèle FileImport")
    
    init_database()
    db = SessionLocal()
    try:
        # Créer un import de test
        test_import = FileImport(
            filename="test_file.csv",
            imported_count=10,
            duplicates_count=2,
            errors_count=0
        )
        db.add(test_import)
        db.commit()
        
        # Vérifier qu'il a été créé
        imported = db.query(FileImport).filter(FileImport.filename == "test_file.csv").first()
        assert imported is not None, "❌ Import de test non créé"
        assert imported.imported_count == 10, "❌ imported_count incorrect"
        assert imported.duplicates_count == 2, "❌ duplicates_count incorrect"
        print("✅ Modèle FileImport fonctionne correctement")
        
        # Nettoyer
        db.delete(imported)
        db.commit()
        print("✅ Import de test supprimé")
        
    finally:
        db.close()


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 60)
    print("🧪 Tests: Nettoyage BDD et table file_imports")
    print("=" * 60)
    
    try:
        test_file_imports_table_exists()
        test_database_is_clean()
        test_file_import_model()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés avec succès!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_tests()

