"""
Script de migration pour ajouter la colonne is_hardcoded à la table allowed_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import engine


def main():
    """Ajoute la colonne is_hardcoded si elle n'existe pas."""
    print("=" * 60)
    print("Migration : Ajout de la colonne is_hardcoded")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Vérifier si la colonne existe déjà
            from sqlalchemy import inspect
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('allowed_mappings')]
            
            if 'is_hardcoded' in columns:
                print("✓ La colonne 'is_hardcoded' existe déjà")
                return 0
            
            # Ajouter la colonne
            print("Ajout de la colonne is_hardcoded...")
            conn.execute(text("ALTER TABLE allowed_mappings ADD COLUMN is_hardcoded BOOLEAN DEFAULT 0 NOT NULL"))
            conn.commit()
            print("✓ Colonne 'is_hardcoded' ajoutée avec succès")
            
            return 0
            
    except Exception as e:
        print(f"✗ ERREUR : {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

