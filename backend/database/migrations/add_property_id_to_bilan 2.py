"""
Migration: Add property_id to Bilan tables (bilan_mappings, bilan_data, bilan_config)

This migration adds the property_id foreign key column to all Bilan-related tables
to support multi-property isolation.

⚠️ Before running, read: docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
import os
import sys
from pathlib import Path

# Get database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def run_migration():
    """Run migration to add property_id to Bilan tables."""
    db_path = str(DB_FILE)
    print(f"📦 [Migration] Connexion à la base de données: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Get default property ID (first property or create one)
        cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            default_property_id = result[0]
            print(f"✅ [Migration] Propriété par défaut trouvée: id={default_property_id}")
        else:
            print("⚠️ [Migration] Aucune propriété trouvée, création d'une propriété par défaut...")
            cursor.execute("""
                INSERT INTO properties (name, address, created_at, updated_at)
                VALUES ('Propriété par défaut', '', datetime('now'), datetime('now'))
            """)
            default_property_id = cursor.lastrowid
            print(f"✅ [Migration] Propriété par défaut créée: id={default_property_id}")
        
        # ========== bilan_mappings ==========
        print("\n📋 [Migration] Table: bilan_mappings")
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(bilan_mappings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            print("  ➕ Ajout de la colonne property_id...")
            cursor.execute("ALTER TABLE bilan_mappings ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE")
            
            # Update existing records
            cursor.execute(f"UPDATE bilan_mappings SET property_id = {default_property_id} WHERE property_id IS NULL")
            cursor.execute("SELECT COUNT(*) FROM bilan_mappings WHERE property_id IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"  ✅ {count} mappings mis à jour avec property_id={default_property_id}")
            
            # Create index
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilan_mapping_property_id ON bilan_mappings(property_id)")
            print("  ✅ Index idx_bilan_mapping_property_id créé")
        else:
            print("  ⏭️ Colonne property_id déjà présente")
        
        # ========== bilan_data ==========
        print("\n📋 [Migration] Table: bilan_data")
        
        cursor.execute("PRAGMA table_info(bilan_data)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            print("  ➕ Ajout de la colonne property_id...")
            cursor.execute("ALTER TABLE bilan_data ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE")
            
            # Update existing records
            cursor.execute(f"UPDATE bilan_data SET property_id = {default_property_id} WHERE property_id IS NULL")
            cursor.execute("SELECT COUNT(*) FROM bilan_data WHERE property_id IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"  ✅ {count} data mis à jour avec property_id={default_property_id}")
            
            # Create index
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilan_data_property_id ON bilan_data(property_id)")
            print("  ✅ Index idx_bilan_data_property_id créé")
        else:
            print("  ⏭️ Colonne property_id déjà présente")
        
        # ========== bilan_config ==========
        print("\n📋 [Migration] Table: bilan_config")
        
        cursor.execute("PRAGMA table_info(bilan_config)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            print("  ➕ Ajout de la colonne property_id...")
            cursor.execute("ALTER TABLE bilan_config ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE")
            
            # Update existing records
            cursor.execute(f"UPDATE bilan_config SET property_id = {default_property_id} WHERE property_id IS NULL")
            cursor.execute("SELECT COUNT(*) FROM bilan_config WHERE property_id IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"  ✅ {count} config mis à jour avec property_id={default_property_id}")
            
            # Create index
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilan_config_property_id ON bilan_config(property_id)")
            print("  ✅ Index idx_bilan_config_property_id créé")
        else:
            print("  ⏭️ Colonne property_id déjà présente")
        
        conn.commit()
        print("\n✅ [Migration] Migration terminée avec succès!")
        
        # Validation
        print("\n📊 [Validation] Vérification des données...")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"  ⚠️ {null_count} mappings sans property_id")
        else:
            print("  ✅ Tous les mappings ont un property_id")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_data WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"  ⚠️ {null_count} data sans property_id")
        else:
            print("  ✅ Toutes les data ont un property_id")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_config WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"  ⚠️ {null_count} config sans property_id")
        else:
            print("  ✅ Toutes les config ont un property_id")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ [Migration] Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
