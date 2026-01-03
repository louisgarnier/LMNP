"""
Script pour créer les tables du bilan (bilan_mappings, bilan_data, bilan_mapping_views).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/create_bilan_tables.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import engine, SessionLocal
from backend.database.models import Base, BilanMapping, BilanData, BilanMappingView


def create_tables():
    """Crée les tables du bilan."""
    db = SessionLocal()
    try:
        print("🔨 Création des tables du bilan...")
        
        # Créer les tables
        BilanMapping.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table bilan_mappings créée")
        
        BilanData.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table bilan_data créée")
        
        BilanMappingView.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table bilan_mapping_views créée")
        
        print("\n📋 Structure des tables:")
        print("  - bilan_mappings: id, category_name, level_1_values, type, sub_category, is_special, special_source, amortization_view_id, created_at, updated_at")
        print("  - bilan_data: id, annee, category_name, amount, created_at, updated_at")
        print("  - bilan_mapping_views: id, name, view_data, created_at, updated_at")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Création des tables du bilan")
    print("=" * 60)
    print()
    
    create_tables()
    
    print()
    print("=" * 60)
    print("✅ Terminé !")
    print("=" * 60)

