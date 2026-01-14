"""
Migration script to fix compte_resultat_mappings table.

This script removes the level_2_values column from compte_resultat_mappings
if it exists, as we only use level_1_values in Phase 8.

Run with: python backend/database/migrations/fix_compte_resultat_mappings_table.py
"""

import sqlite3
import sys
from pathlib import Path

# Get database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Remove level_2_values column from compte_resultat_mappings if it exists."""
    if not DB_FILE.exists():
        print("Database file does not exist. Nothing to migrate.")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='compte_resultat_mappings'
        """)
        
        if not cursor.fetchone():
            print("Table 'compte_resultat_mappings' does not exist. Nothing to migrate.")
            return
        
        # Check if level_2_values column exists
        cursor.execute("PRAGMA table_info(compte_resultat_mappings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'level_2_values' not in columns:
            print("Column 'level_2_values' does not exist. Nothing to migrate.")
            return
        
        print("Found 'level_2_values' column. Removing it...")
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        # Step 1: Create new table without level_2_values
        cursor.execute("""
            CREATE TABLE compte_resultat_mappings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name VARCHAR(255) NOT NULL,
                level_1_values TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Step 2: Copy data (excluding level_2_values)
        cursor.execute("""
            INSERT INTO compte_resultat_mappings_new 
            (id, category_name, level_1_values, created_at, updated_at)
            SELECT id, category_name, level_1_values, created_at, updated_at
            FROM compte_resultat_mappings
        """)
        
        # Step 3: Drop old table
        cursor.execute("DROP TABLE compte_resultat_mappings")
        
        # Step 4: Rename new table
        cursor.execute("ALTER TABLE compte_resultat_mappings_new RENAME TO compte_resultat_mappings")
        
        # Step 5: Recreate indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_compte_resultat_mapping_category 
            ON compte_resultat_mappings(category_name)
        """)
        
        conn.commit()
        print("✓ Migration completed successfully. Column 'level_2_values' removed.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Fix compte_resultat_mappings table")
    print("=" * 60)
    migrate()
    print("=" * 60)
