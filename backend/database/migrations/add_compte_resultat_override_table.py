"""
Migration: Add compte_resultat_override table.

This script creates the compte_resultat_override table to store
manual overrides of the "Résultat de l'exercice" for each year.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Create compte_resultat_override table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='compte_resultat_override'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table compte_resultat_override already exists")
        else:
            print("Creating compte_resultat_override table...")
            
            # Create table
            cursor.execute("""
                CREATE TABLE compte_resultat_override (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL UNIQUE,
                    override_value REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_compte_resultat_override_year 
                ON compte_resultat_override(year)
            """)
            
            conn.commit()
            print("✅ Table compte_resultat_override created successfully")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
