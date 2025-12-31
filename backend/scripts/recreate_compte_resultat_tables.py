"""
Script pour recréer les tables compte_resultat_mappings et compte_resultat_data.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/recreate_compte_resultat_tables.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from backend.database import engine, SessionLocal
from backend.database.models import Base, CompteResultatMapping, CompteResultatData


def recreate_tables():
    """Supprime et recrée les tables compte_resultat."""
    db = SessionLocal()
    try:
        print("🗑️  Suppression des tables existantes...")
        
        # Supprimer les tables si elles existent
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS compte_resultat_data"))
            conn.execute(text("DROP TABLE IF EXISTS compte_resultat_mappings"))
            conn.commit()
        
        print("✅ Tables supprimées")
        
        print("🔨 Création des nouvelles tables...")
        
        # Créer les tables
        CompteResultatMapping.__table__.create(bind=engine, checkfirst=True)
        CompteResultatData.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Tables créées avec succès")
        print("\n📋 Structure des tables:")
        print("  - compte_resultat_mappings: id, category_name, level_1_values, level_2_values, level_3_values, created_at, updated_at")
        print("  - compte_resultat_data: id, annee, category_name, amount, amortization_view_id, created_at, updated_at")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Recréation des tables compte_resultat")
    print("=" * 60)
    print()
    
    recreate_tables()
    
    print()
    print("=" * 60)
    print("✅ Terminé !")
    print("=" * 60)

