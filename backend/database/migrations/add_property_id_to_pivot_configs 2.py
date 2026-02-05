"""
Migration to add property_id to pivot_configs table.
Phase 11 - Onglet 7 (Pivot) - Multi-property support

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
    # Try different possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'lmnp.db'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lmnp.db'),
        'lmnp.db',
        'backend/database/lmnp.db',
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    
    # Default to the most likely path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))


def get_default_property_id(cursor):
    """Get the default property ID (first property)."""
    cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    if result:
        return result[0]
    return None


def run_migration():
    """Run the migration to add property_id to pivot_configs table."""
    db_path = get_db_path()
    logger.info(f"[Migration] Database path: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"[Migration] Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if property_id column already exists
        cursor.execute("PRAGMA table_info(pivot_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' in columns:
            logger.info("[Migration] Column property_id already exists in pivot_configs table")
            return True
        
        # Get default property ID
        default_property_id = get_default_property_id(cursor)
        if default_property_id is None:
            logger.warning("[Migration] No properties found. Creating default property...")
            cursor.execute(
                "INSERT INTO properties (name, address, created_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))",
                ("Default Property", "")
            )
            default_property_id = cursor.lastrowid
            logger.info(f"[Migration] Created default property with ID {default_property_id}")
        
        logger.info(f"[Migration] Using default property_id: {default_property_id}")
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM pivot_configs")
        count = cursor.fetchone()[0]
        logger.info(f"[Migration] Found {count} existing pivot_configs records")
        
        # Add property_id column
        logger.info("[Migration] Adding property_id column to pivot_configs...")
        cursor.execute(f"ALTER TABLE pivot_configs ADD COLUMN property_id INTEGER DEFAULT {default_property_id}")
        
        # Update all existing records with default property_id
        cursor.execute(f"UPDATE pivot_configs SET property_id = {default_property_id} WHERE property_id IS NULL")
        updated_count = cursor.rowcount
        logger.info(f"[Migration] Updated {updated_count} records with property_id={default_property_id}")
        
        # Create index on property_id
        logger.info("[Migration] Creating index idx_pivot_configs_property_id...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pivot_configs_property_id ON pivot_configs(property_id)")
        except sqlite3.OperationalError as e:
            logger.warning(f"[Migration] Index creation warning: {e}")
        
        # Commit changes
        conn.commit()
        logger.info("[Migration] Migration completed successfully!")
        
        # Verify migration
        cursor.execute("PRAGMA table_info(pivot_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"[Migration] pivot_configs columns after migration: {columns}")
        
        # Verify all records have property_id
        cursor.execute("SELECT COUNT(*) FROM pivot_configs WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            logger.warning(f"[Migration] WARNING: {null_count} records still have NULL property_id")
        else:
            logger.info("[Migration] All records have property_id set correctly")
        
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
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        exit(1)
