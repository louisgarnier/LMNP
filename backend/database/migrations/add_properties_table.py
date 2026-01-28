"""
Migration: Add properties table.

This script creates the properties table to support multi-property management.
Each property represents an apartment/property that will have isolated data.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Create properties table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='properties'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table properties already exists")
        else:
            print("Creating properties table...")
            
            # Create table
            cursor.execute("""
                CREATE TABLE properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    address VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on name (unique constraint)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_property_name 
                ON properties(name)
            """)
            
            conn.commit()
            print("✅ Table properties created successfully")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
