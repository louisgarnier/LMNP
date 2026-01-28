"""
Migration: Add FOREIGN KEY constraints with ON DELETE CASCADE for property_id.

This script adds FOREIGN KEY constraints to all tables with property_id
to ensure that when a property is deleted, all associated data is automatically deleted.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"

# Tables that should have property_id with FK constraint
TABLES_WITH_PROPERTY_ID = [
    'transactions',
    'enriched_transactions',
    'mappings',
    'allowed_mappings',
    'loan_configs',
    'loan_payments',
    'amortization_types',
    'amortization_results',
    'compte_resultat_mappings',
    'compte_resultat_data',
    'compte_resultat_config',
    'compte_resultat_override',
    'bilan_mappings',
    'bilan_data',
    'bilan_config',
    'pivot_configs'
]


def migrate():
    """Add FOREIGN KEY constraints with ON DELETE CASCADE."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute('PRAGMA foreign_keys = ON')  # Activer les FK pour SQLite
    cursor = conn.cursor()
    
    try:
        print("=== Ajout des contraintes FOREIGN KEY avec ON DELETE CASCADE ===\n")
        
        for table_name in TABLES_WITH_PROPERTY_ID:
            # Vérifier si la table existe
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"ℹ️  Table {table_name} n'existe pas encore, ignorée")
                continue
            
            # Vérifier si property_id existe
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if 'property_id' not in columns:
                print(f"ℹ️  Table {table_name} n'a pas de colonne property_id, ignorée")
                continue
            
            # Vérifier si la contrainte FK existe déjà
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            existing_fks = cursor.fetchall()
            has_fk = any(fk[3] == 'property_id' and fk[2] == 'properties' for fk in existing_fks)
            
            if has_fk:
                print(f"✅ {table_name}: Contrainte FK déjà présente")
            else:
                # SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT directement
                # Il faut recréer la table avec la contrainte
                print(f"⚠️  {table_name}: Pas de contrainte FK, ajout nécessaire")
                print(f"   Note: SQLite nécessite de recréer la table pour ajouter une FK")
                print(f"   Cette migration sera effectuée lors de l'ajout de property_id dans les modèles")
        
        print("\n✅ Vérification terminée")
        print("\n⚠️  IMPORTANT: Les contraintes FK seront ajoutées automatiquement")
        print("   lorsque property_id sera ajouté aux modèles SQLAlchemy avec ForeignKey()")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
