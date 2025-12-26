"""
Script de migration de la table amortization_config vers le nouveau schéma (7 catégories).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script met à jour la table amortization_config pour passer de 4 catégories à 7 catégories.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database.connection import engine, SessionLocal
from backend.database.models import Base


def migrate_amortization_config():
    """
    Migre la table amortization_config vers le nouveau schéma (7 catégories).
    """
    print("🔄 Migration de la table amortization_config...")
    
    with engine.connect() as conn:
        # Vérifier si la table existe
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='amortization_config'
        """))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("✅ La table n'existe pas encore, elle sera créée automatiquement au prochain démarrage")
            return
        
        # Vérifier les colonnes existantes
        result = conn.execute(text("PRAGMA table_info(amortization_config)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        # Vérifier si la migration est déjà faite
        if 'duration_part_terrain' in columns:
            print("✅ La table a déjà le nouveau schéma (7 catégories)")
            return
        
        # Vérifier si l'ancien schéma existe
        if 'duration_meubles' not in columns:
            print("⚠️ La table n'a ni l'ancien ni le nouveau schéma. Recréation...")
            conn.execute(text("DROP TABLE IF EXISTS amortization_config"))
            conn.commit()
            print("✅ Table supprimée, elle sera recréée automatiquement")
            return
        
        print("📋 Ancien schéma détecté (4 catégories)")
        print("🔄 Suppression de l'ancienne table...")
        
        # Supprimer la table (les données seront perdues, mais l'utilisateur a dit qu'il peut refaire les mappings)
        conn.execute(text("DROP TABLE IF EXISTS amortization_config"))
        conn.commit()
        
        print("✅ Migration terminée - La table sera recréée avec le nouveau schéma au prochain démarrage")
    
    # Recréer la table avec le nouveau schéma
    print("🔄 Recréation de la table avec le nouveau schéma...")
    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables['amortization_config']])
    print("✅ Table recréée avec succès")


if __name__ == "__main__":
    try:
        migrate_amortization_config()
        print("\n✅ Migration terminée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

