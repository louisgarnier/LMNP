"""
Script pour créer la table allowed_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/create_allowed_mappings_table.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import engine, SessionLocal
from backend.database.models import Base, AllowedMapping


def create_table():
    """Crée la table allowed_mappings."""
    db = SessionLocal()
    try:
        print("🔨 Création de la table allowed_mappings...")
        
        # Créer la table
        AllowedMapping.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Table créée avec succès")
        print("\n📋 Structure de la table:")
        print("  - allowed_mappings: id, level_1, level_2, level_3, created_at, updated_at")
        print("  - Contrainte unique sur (level_1, level_2, level_3)")
        print("  - Index sur level_1, level_2, level_3")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Création de la table allowed_mappings")
    print("=" * 60)
    print()
    
    create_table()
    
    print()
    print("=" * 60)
    print("✅ Terminé !")
    print("=" * 60)

