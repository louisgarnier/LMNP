"""
Migration: Add loan_start_date and loan_end_date columns to loan_configs table.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add loan_start_date and loan_end_date columns to loan_configs table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(loan_configs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "loan_start_date" not in columns:
            print("Adding loan_start_date column...")
            cursor.execute("ALTER TABLE loan_configs ADD COLUMN loan_start_date DATE")
        else:
            print("Column loan_start_date already exists, skipping...")
        
        if "loan_end_date" not in columns:
            print("Adding loan_end_date column...")
            cursor.execute("ALTER TABLE loan_configs ADD COLUMN loan_end_date DATE")
        else:
            print("Column loan_end_date already exists, skipping...")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
