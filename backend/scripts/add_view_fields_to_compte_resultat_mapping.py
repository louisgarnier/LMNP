"""
Script pour ajouter les champs amortization_view_id et selected_loan_ids à la table compte_resultat_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/add_view_fields_to_compte_resultat_mapping.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from backend.database import engine, SessionLocal


def add_columns():
    """Ajoute les colonnes amortization_view_id et selected_loan_ids à la table compte_resultat_mappings."""
    db = SessionLocal()
    try:
        print("🔨 Ajout des colonnes amortization_view_id et selected_loan_ids...")
        
        with engine.connect() as conn:
            # Vérifier si les colonnes existent déjà
            result = conn.execute(text("""
                PRAGMA table_info(compte_resultat_mappings)
            """))
            columns = [row[1] for row in result.fetchall()]
            
            if 'amortization_view_id' not in columns:
                conn.execute(text("""
                    ALTER TABLE compte_resultat_mappings 
                    ADD COLUMN amortization_view_id INTEGER REFERENCES amortization_views(id)
                """))
                print("✅ Colonne amortization_view_id ajoutée")
            else:
                print("ℹ️  Colonne amortization_view_id existe déjà")
            
            if 'selected_loan_ids' not in columns:
                conn.execute(text("""
                    ALTER TABLE compte_resultat_mappings 
                    ADD COLUMN selected_loan_ids TEXT
                """))
                print("✅ Colonne selected_loan_ids ajoutée")
            else:
                print("ℹ️  Colonne selected_loan_ids existe déjà")
            
            conn.commit()
        
        print("✅ Colonnes ajoutées avec succès")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Ajout des colonnes à compte_resultat_mappings")
    print("=" * 60)
    print()
    
    add_columns()
    
    print()
    print("=" * 60)
    print("✅ Terminé !")
    print("=" * 60)

