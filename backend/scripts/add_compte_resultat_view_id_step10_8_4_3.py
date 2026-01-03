"""
Script de migration pour ajouter compte_resultat_view_id dans compte_resultat_data et bilan_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Step 10.8.4.3 - Ajout du champ compte_resultat_view_id pour lier les données de compte de résultat
et les mappings de bilan aux vues de compte de résultat.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, engine
from sqlalchemy import text, inspect


def add_compte_resultat_view_id_columns():
    """
    Ajoute la colonne compte_resultat_view_id dans compte_resultat_data et bilan_mappings.
    """
    print("🔄 Migration: Ajout de compte_resultat_view_id...")
    
    db = SessionLocal()
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Vérifier que les tables existent
        if 'compte_resultat_data' not in tables:
            print("❌ Table 'compte_resultat_data' n'existe pas")
            return False
        
        if 'bilan_mappings' not in tables:
            print("❌ Table 'bilan_mappings' n'existe pas")
            return False
        
        # Vérifier si la colonne existe déjà dans compte_resultat_data
        compte_resultat_data_columns = [col['name'] for col in inspector.get_columns('compte_resultat_data')]
        if 'compte_resultat_view_id' in compte_resultat_data_columns:
            print("⚠️  Colonne 'compte_resultat_view_id' existe déjà dans 'compte_resultat_data'")
        else:
            print("➕ Ajout de 'compte_resultat_view_id' dans 'compte_resultat_data'...")
            db.execute(text("""
                ALTER TABLE compte_resultat_data 
                ADD COLUMN compte_resultat_view_id INTEGER 
                REFERENCES compte_resultat_mapping_views(id)
            """))
            db.commit()
            print("✅ Colonne ajoutée dans 'compte_resultat_data'")
        
        # Vérifier si la colonne existe déjà dans bilan_mappings
        bilan_mappings_columns = [col['name'] for col in inspector.get_columns('bilan_mappings')]
        if 'compte_resultat_view_id' in bilan_mappings_columns:
            print("⚠️  Colonne 'compte_resultat_view_id' existe déjà dans 'bilan_mappings'")
        else:
            print("➕ Ajout de 'compte_resultat_view_id' dans 'bilan_mappings'...")
            db.execute(text("""
                ALTER TABLE bilan_mappings 
                ADD COLUMN compte_resultat_view_id INTEGER 
                REFERENCES compte_resultat_mapping_views(id)
            """))
            db.commit()
            print("✅ Colonne ajoutée dans 'bilan_mappings'")
        
        print("✅ Migration terminée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Migration: Ajout de compte_resultat_view_id")
    print("=" * 80)
    print()
    
    success = add_compte_resultat_view_id_columns()
    
    if success:
        print()
        print("✅ Migration réussie")
        sys.exit(0)
    else:
        print()
        print("❌ Migration échouée")
        sys.exit(1)

