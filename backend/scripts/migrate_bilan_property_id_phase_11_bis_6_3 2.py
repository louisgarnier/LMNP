"""
Migration des données Bilan existantes - Phase 11 bis
Assigne les données existantes (mappings, config, data) à une propriété par défaut.

⚠️ Before running, read: docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
import os
import sys
from pathlib import Path

# Get database path
DB_DIR = Path(__file__).parent.parent / "database"
DB_FILE = DB_DIR / "lmnp.db"


def run_migration():
    """Run migration to assign existing Bilan data to default property."""
    db_path = str(DB_FILE)
    print(f"📦 [Migration] Connexion à la base de données: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get default property ID (first property)
        cursor.execute("SELECT id, name FROM properties ORDER BY id LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("⚠️ [Migration] Aucune propriété trouvée. Migration annulée.")
            return
        
        default_property_id = result[0]
        default_property_name = result[1]
        print(f"✅ [Migration] Propriété par défaut: {default_property_name} (id={default_property_id})")
        
        # ========== bilan_mappings ==========
        print("\n📋 [Migration] Table: bilan_mappings")
        
        # Count records without property_id
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"  ➕ {null_count} mappings sans property_id à migrer...")
            cursor.execute(f"UPDATE bilan_mappings SET property_id = {default_property_id} WHERE property_id IS NULL")
            print(f"  ✅ {null_count} mappings migrés vers property_id={default_property_id}")
        else:
            print("  ⏭️ Aucun mapping à migrer (tous ont déjà un property_id)")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings WHERE property_id IS NOT NULL")
        with_pid = cursor.fetchone()[0]
        print(f"  📊 Résultat: {with_pid}/{total} mappings ont un property_id")
        
        # ========== bilan_data ==========
        print("\n📋 [Migration] Table: bilan_data")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_data WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"  ➕ {null_count} data sans property_id à migrer...")
            cursor.execute(f"UPDATE bilan_data SET property_id = {default_property_id} WHERE property_id IS NULL")
            print(f"  ✅ {null_count} data migrés vers property_id={default_property_id}")
        else:
            print("  ⏭️ Aucune data à migrer (toutes ont déjà un property_id)")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM bilan_data")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_data WHERE property_id IS NOT NULL")
        with_pid = cursor.fetchone()[0]
        print(f"  📊 Résultat: {with_pid}/{total} data ont un property_id")
        
        # ========== bilan_config ==========
        print("\n📋 [Migration] Table: bilan_config")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_config WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"  ➕ {null_count} config sans property_id à migrer...")
            cursor.execute(f"UPDATE bilan_config SET property_id = {default_property_id} WHERE property_id IS NULL")
            print(f"  ✅ {null_count} config migrés vers property_id={default_property_id}")
        else:
            print("  ⏭️ Aucune config à migrer (toutes ont déjà un property_id)")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM bilan_config")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_config WHERE property_id IS NOT NULL")
        with_pid = cursor.fetchone()[0]
        print(f"  📊 Résultat: {with_pid}/{total} config ont un property_id")
        
        conn.commit()
        print("\n✅ [Migration] Migration terminée avec succès!")
        
        # ========== VALIDATION FINALE ==========
        print("\n📊 [Validation] Résumé des données après migration:")
        
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings")
        total_mappings = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_mappings WHERE property_id IS NULL")
        null_mappings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bilan_data")
        total_data = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_data WHERE property_id IS NULL")
        null_data = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bilan_config")
        total_config = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilan_config WHERE property_id IS NULL")
        null_config = cursor.fetchone()[0]
        
        print(f"  - bilan_mappings: {total_mappings} total, {null_mappings} sans property_id")
        print(f"  - bilan_data: {total_data} total, {null_data} sans property_id")
        print(f"  - bilan_config: {total_config} total, {null_config} sans property_id")
        
        if null_mappings == 0 and null_data == 0 and null_config == 0:
            print("\n✅ [Validation] Toutes les données ont un property_id!")
        else:
            print("\n⚠️ [Validation] Certaines données n'ont pas de property_id!")
        
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
