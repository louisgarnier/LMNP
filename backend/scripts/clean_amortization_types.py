"""
Script pour nettoyer les types d'amortissement en base de données.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script supprime tous les types qui ne sont pas pour "Immobilisations".
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType


def main():
    """Nettoie les types d'amortissement - garde uniquement ceux pour 'Immobilisations'."""
    print("=" * 60)
    print("Nettoyage des types d'amortissement")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Récupérer tous les types
        all_types = db.query(AmortizationType).all()
        
        print(f"\n📊 Types trouvés en BDD : {len(all_types)}")
        
        # Identifier les types à supprimer (ceux qui ne sont pas pour "Immobilisations")
        types_to_delete = []
        types_to_keep = []
        
        for atype in all_types:
            if atype.level_2_value == "Immobilisations":
                types_to_keep.append(atype)
            else:
                types_to_delete.append(atype)
        
        print(f"\n✓ Types à conserver (Immobilisations) : {len(types_to_keep)}")
        print(f"✗ Types à supprimer (autres Level 2 ou vide) : {len(types_to_delete)}")
        
        if types_to_delete:
            print("\nTypes à supprimer :")
            for atype in types_to_delete:
                print(f"  - ID {atype.id}: {atype.name} (level_2_value: '{atype.level_2_value or '(vide)'}')")
            
            # Supprimer les types (non-interactif)
            print("\n⚠️  Suppression des types...")
            for atype in types_to_delete:
                db.delete(atype)
            
            db.commit()
            print(f"\n✓ {len(types_to_delete)} type(s) supprimé(s) avec succès")
        else:
            print("\n✓ Aucun type à supprimer - tous les types sont pour 'Immobilisations'")
        
        # Vérification finale
        print("\n" + "=" * 60)
        print("Vérification finale")
        print("=" * 60)
        remaining_types = db.query(AmortizationType).all()
        print(f"📊 Types restants en BDD : {len(remaining_types)}")
        
        for atype in remaining_types:
            print(f"  - ID {atype.id}: {atype.name} (level_2_value: '{atype.level_2_value}')")
        
        return 0
            
    except Exception as e:
        print(f"\n✗ ERREUR : {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

