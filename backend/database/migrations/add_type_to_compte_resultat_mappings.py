"""
Migration: Add type column to compte_resultat_mappings table.

This script adds a 'type' column to store whether a category is
'Produits d'exploitation' or 'Charges d'exploitation'.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add type column to compte_resultat_mappings table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(compte_resultat_mappings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "type" not in columns:
            print("Adding type column...")
            cursor.execute("ALTER TABLE compte_resultat_mappings ADD COLUMN type VARCHAR(50)")
            
            # Pour les catégories existantes, déduire le type depuis le category_name
            # Catégories Produits d'exploitation
            cursor.execute("""
                UPDATE compte_resultat_mappings
                SET type = 'Produits d''exploitation'
                WHERE category_name IN (
                    'Loyers hors charge encaissés',
                    'Charges locatives payées par locataires',
                    'Autres revenus'
                )
            """)
            
            # Toutes les autres catégories sont des Charges d'exploitation par défaut
            cursor.execute("""
                UPDATE compte_resultat_mappings
                SET type = 'Charges d''exploitation'
                WHERE type IS NULL
            """)
            
            conn.commit()
            print("✅ Colonne type ajoutée à compte_resultat_mappings")
        else:
            print("ℹ️  Colonne type existe déjà")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
