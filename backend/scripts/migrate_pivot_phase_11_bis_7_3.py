"""
Migration script for Pivot data - Phase 11 - Onglet 7 (Pivot)

This script assigns existing pivot configs to the default property.

⚠️ Before running, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_path():
    """Get the path to the database file."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'database', 'lmnp.db'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'lmnp.db'),
        'lmnp.db',
        'backend/database/lmnp.db',
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'lmnp.db'))


def get_default_property_id(cursor):
    """Get the default property ID (first property)."""
    cursor.execute("SELECT id, name FROM properties ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    if result:
        return result[0], result[1]
    return None, None


def run_migration():
    """Run the migration to assign pivot configs to default property."""
    db_path = get_db_path()
    logger.info(f"[Migration] Database path: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"[Migration] Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get default property
        default_property_id, default_property_name = get_default_property_id(cursor)
        if default_property_id is None:
            logger.error("[Migration] No properties found in database")
            return False
        
        logger.info(f"[Migration] Default property: {default_property_name} (ID: {default_property_id})")
        
        # Check if property_id column exists
        cursor.execute("PRAGMA table_info(pivot_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            logger.error("[Migration] Column property_id does not exist in pivot_configs table")
            logger.error("[Migration] Please run add_property_id_to_pivot_configs.py first")
            return False
        
        # Count records with NULL property_id
        cursor.execute("SELECT COUNT(*) FROM pivot_configs WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        logger.info(f"[Migration] Found {null_count} pivot configs with NULL property_id")
        
        if null_count == 0:
            logger.info("[Migration] All pivot configs already have property_id assigned")
        else:
            # Update records with NULL property_id
            cursor.execute(
                f"UPDATE pivot_configs SET property_id = ? WHERE property_id IS NULL",
                (default_property_id,)
            )
            updated_count = cursor.rowcount
            logger.info(f"[Migration] Migré {updated_count} enregistrements pour pivot_configs")
            conn.commit()
        
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM pivot_configs WHERE property_id IS NULL")
        remaining_null = cursor.fetchone()[0]
        
        if remaining_null > 0:
            logger.warning(f"[Migration] WARNING: {remaining_null} records still have NULL property_id")
            return False
        
        # Count by property
        cursor.execute("""
            SELECT p.name, COUNT(pc.id) as count
            FROM properties p
            LEFT JOIN pivot_configs pc ON pc.property_id = p.id
            GROUP BY p.id
            ORDER BY p.id
        """)
        for row in cursor.fetchall():
            logger.info(f"[Migration] Property '{row[0]}': {row[1]} pivot configs")
        
        logger.info("[Migration] Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"[Migration] Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✅ Migration des données Pivot terminée avec succès!")
    else:
        print("\n❌ Migration échouée!")
        exit(1)
