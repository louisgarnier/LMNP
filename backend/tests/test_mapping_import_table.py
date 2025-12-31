"""
Test script for Step 3.7.1 - Vérifier la création de la table mapping_imports

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db
from database.models import MappingImport
from sqlalchemy import inspect
from datetime import datetime

def test_mapping_import_table():
    """Test que la table mapping_imports existe et fonctionne."""
    print("🧪 Test Step 3.7.1 - Table mapping_imports\n")
    
    # Initialiser la base de données
    print("1️⃣ Initialisation de la base de données...")
    init_database()
    print("✅ Base de données initialisée\n")
    
    # Vérifier que la table existe
    print("2️⃣ Vérification de l'existence de la table...")
    db = next(get_db())
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    if 'mapping_imports' not in tables:
        print("❌ ERREUR: La table 'mapping_imports' n'existe pas!")
        print(f"Tables disponibles: {tables}")
        return False
    
    print("✅ Table 'mapping_imports' existe\n")
    
    # Vérifier la structure de la table
    print("3️⃣ Vérification de la structure de la table...")
    columns = inspector.get_columns('mapping_imports')
    column_names = [col['name'] for col in columns]
    
    expected_columns = ['id', 'filename', 'imported_at', 'imported_count', 
                       'duplicates_count', 'errors_count', 'created_at', 'updated_at']
    
    missing_columns = [col for col in expected_columns if col not in column_names]
    if missing_columns:
        print(f"❌ ERREUR: Colonnes manquantes: {missing_columns}")
        print(f"Colonnes trouvées: {column_names}")
        return False
    
    print(f"✅ Toutes les colonnes sont présentes: {column_names}\n")
    
    # Vérifier les index
    print("4️⃣ Vérification des index...")
    indexes = inspector.get_indexes('mapping_imports')
    index_names = [idx['name'] for idx in indexes]
    
    expected_indexes = ['idx_mapping_imports_filename', 'idx_mapping_imports_imported_at']
    missing_indexes = [idx for idx in expected_indexes if idx not in index_names]
    
    if missing_indexes:
        print(f"⚠️  Avertissement: Index manquants: {missing_indexes}")
        print(f"Index trouvés: {index_names}")
    else:
        print(f"✅ Tous les index sont présents: {index_names}\n")
    
    # Test insertion
    print("5️⃣ Test d'insertion d'un enregistrement...")
    try:
        test_import = MappingImport(
            filename="test_mapping.xlsx",
            imported_at=datetime.utcnow(),
            imported_count=10,
            duplicates_count=2,
            errors_count=0
        )
        db.add(test_import)
        db.commit()
        print("✅ Insertion réussie\n")
        
        # Vérifier la récupération
        print("6️⃣ Test de récupération...")
        retrieved = db.query(MappingImport).filter(MappingImport.filename == "test_mapping.xlsx").first()
        if not retrieved:
            print("❌ ERREUR: Impossible de récupérer l'enregistrement")
            return False
        
        print(f"✅ Récupération réussie:")
        print(f"   - ID: {retrieved.id}")
        print(f"   - Filename: {retrieved.filename}")
        print(f"   - Imported count: {retrieved.imported_count}")
        print(f"   - Duplicates count: {retrieved.duplicates_count}")
        print(f"   - Errors count: {retrieved.errors_count}\n")
        
        # Nettoyer
        print("7️⃣ Nettoyage...")
        db.delete(retrieved)
        db.commit()
        print("✅ Nettoyage terminé\n")
        
    except Exception as e:
        print(f"❌ ERREUR lors de l'insertion: {str(e)}")
        db.rollback()
        return False
    
    print("🎉 Tous les tests sont passés avec succès!")
    return True

if __name__ == "__main__":
    success = test_mapping_import_table()
    sys.exit(0 if success else 1)





