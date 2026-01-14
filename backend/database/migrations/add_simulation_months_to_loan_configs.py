"""
Migration: Add simulation_months column to loan_configs table.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add simulation_months column to loan_configs table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(loan_configs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "simulation_months" not in columns:
            print("Adding simulation_months column...")
            cursor.execute("ALTER TABLE loan_configs ADD COLUMN simulation_months TEXT")
            conn.commit()
            print("✅ Colonne simulation_months ajoutée à loan_configs")
        else:
            print("ℹ️  Colonne simulation_months existe déjà")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Migration: Add simulation_months to loan_configs")
    migrate()
