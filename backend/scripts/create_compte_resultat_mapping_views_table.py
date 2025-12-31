"""
Script pour créer la table compte_resultat_mapping_views.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/create_compte_resultat_mapping_views_table.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import engine, SessionLocal
from backend.database.models import Base, CompteResultatMappingView


def create_table():
    """Crée la table compte_resultat_mapping_views."""
    db = SessionLocal()
    try:
        print("🔨 Création de la table compte_resultat_mapping_views...")
        
        # Créer la table
        CompteResultatMappingView.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Table créée avec succès")
        print("\n📋 Structure de la table:")
        print("  - compte_resultat_mapping_views: id, name, view_data, created_at, updated_at")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Création de la table compte_resultat_mapping_views")
    print("=" * 60)
    print()
    
    create_table()
    
    print()
    print("=" * 60)
    print("✅ Terminé !")
    print("=" * 60)

