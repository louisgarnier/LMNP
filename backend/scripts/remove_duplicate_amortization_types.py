"""
Script pour supprimer les doublons de types d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from collections import defaultdict

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType


def main():
    """Supprime les doublons de types d'amortissement."""
    print("=" * 60)
    print("Suppression des doublons de types d'amortissement")
    print("=" * 60)
    
    init_database()
    db = SessionLocal()
    
    try:
        # Récupérer tous les types pour Immobilisations
        types = db.query(AmortizationType).filter(AmortizationType.level_2_value == 'Immobilisations').all()
        print(f'\n📊 Types trouvés pour "Immobilisations": {len(types)}')
        
        # Grouper par nom
        by_name = defaultdict(list)
        for t in types:
            by_name[t.name].append(t)
        
        # Garder seulement le premier de chaque nom, supprimer les autres
        to_delete = []
        to_keep = []
        
        print("\nAnalyse des doublons:")
        for name, type_list in sorted(by_name.items()):
            if len(type_list) > 1:
                to_keep.append(type_list[0])
                to_delete.extend(type_list[1:])
                print(f'  ✗ {name}: {len(type_list)} occurrences')
                print(f'    → Garde ID {type_list[0].id}, supprime IDs {[t.id for t in type_list[1:]]}')
            else:
                to_keep.append(type_list[0])
                print(f'  ✓ {name}: 1 occurrence (ID {type_list[0].id})')
        
        if to_delete:
            print(f'\n⚠️  Suppression de {len(to_delete)} doublon(s)...')
            for t in to_delete:
                db.delete(t)
            
            db.commit()
            print(f'✓ {len(to_delete)} doublon(s) supprimé(s)')
            print(f'✓ {len(to_keep)} type(s) conservé(s)')
        else:
            print('\n✓ Aucun doublon trouvé')
        
        # Vérification finale
        print("\n" + "=" * 60)
        print("Vérification finale")
        print("=" * 60)
        remaining_types = db.query(AmortizationType).filter(AmortizationType.level_2_value == 'Immobilisations').all()
        print(f'📊 Types restants pour "Immobilisations": {len(remaining_types)}')
        for t in sorted(remaining_types, key=lambda x: x.name):
            print(f'  - ID {t.id}: {t.name}')
        
        return 0
        
    except Exception as e:
        print(f'\n✗ ERREUR : {e}')
        db.rollback()
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

