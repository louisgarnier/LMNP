"""
Migration: Ajouter ON DELETE CASCADE à la ForeignKey transaction_id dans amortization_results.

Cette migration est nécessaire car SQLite ne supporte pas la modification directe
des contraintes FOREIGN KEY. On doit recréer la table.
"""

import sqlite3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def migrate():
    """Ajouter ON DELETE CASCADE à la ForeignKey transaction_id dans amortization_results."""
    db_path = project_root / "backend" / "database" / "lmnp.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print("="*80)
    print("🔄 MIGRATION: Ajouter ON DELETE CASCADE à amortization_results.transaction_id")
    print("="*80 + "\n")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Activer les foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Vérifier si la contrainte existe déjà
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='amortization_results'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("❌ Table amortization_results non trouvée")
            return False
        
        create_sql = result[0]
        
        # Vérifier si ON DELETE CASCADE est déjà présent
        if "ON DELETE CASCADE" in create_sql.upper():
            print("✅ La contrainte ON DELETE CASCADE existe déjà")
            return True
        
        print("📋 Création d'une table temporaire avec la nouvelle contrainte...")
        
        # Supprimer la table temporaire si elle existe déjà
        cursor.execute("DROP TABLE IF EXISTS amortization_results_new")
        
        # Créer une table temporaire avec la nouvelle contrainte
        cursor.execute("""
            CREATE TABLE amortization_results_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                category VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                amortization_view_id INTEGER REFERENCES amortization_views(id),
                property_id INTEGER,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
            )
        """)
        
        # Copier les données
        print("📋 Copie des données...")
        cursor.execute("""
            INSERT INTO amortization_results_new 
            SELECT * FROM amortization_results
        """)
        
        # Compter les enregistrements
        cursor.execute("SELECT COUNT(*) FROM amortization_results_new")
        count = cursor.fetchone()[0]
        print(f"   ✅ {count} enregistrements copiés")
        
        # Supprimer l'ancienne table
        print("📋 Suppression de l'ancienne table...")
        cursor.execute("DROP TABLE amortization_results")
        
        # Renommer la nouvelle table
        print("📋 Renommage de la nouvelle table...")
        cursor.execute("ALTER TABLE amortization_results_new RENAME TO amortization_results")
        
        # Recréer les index
        print("📋 Recréation des index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_amortization_result_year_category 
            ON amortization_results(year, category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_amortization_result_transaction 
            ON amortization_results(transaction_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_amortization_results_transaction_id 
            ON amortization_results(transaction_id)
        """)
        
        # Commit
        conn.commit()
        print("\n✅ Migration terminée avec succès!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
