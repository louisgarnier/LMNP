"""
Script pour corriger les types d'amortissement en base de données.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script :
1. Renomme "Immobilisation agence" → "Immobilisation agencements"
2. Renomme "Part terrain" si nécessaire (déjà correct)
3. Crée les types manquants
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType

# Les 7 types attendus (template par défaut)
EXPECTED_TYPES = [
    "Part terrain",
    "Immobilisation structure/GO",
    "Immobilisation mobilier",
    "Immobilisation IGT",
    "Immobilisation agencements",
    "Immobilisation Facade/Toiture",
    "Immobilisation travaux",
]


def main():
    """Corrige les types d'amortissement en base de données."""
    print("=" * 60)
    print("Correction des types d'amortissement en BDD")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # 1. Renommer "Immobilisation agence" → "Immobilisation agencements"
        agence_type = db.query(AmortizationType).filter(
            AmortizationType.name == "Immobilisation agence"
        ).first()
        
        if agence_type:
            print("\n1. Renommage de 'Immobilisation agence' → 'Immobilisation agencements'...")
            agence_type.name = "Immobilisation agencements"
            db.commit()
            print("   ✓ Renommé avec succès")
        else:
            print("\n1. Aucun type 'Immobilisation agence' à renommer")
        
        # 2. Créer les types manquants
        print("\n2. Création des types manquants...")
        all_types = db.query(AmortizationType).all()
        existing_names = {atype.name for atype in all_types}
        
        created_count = 0
        for type_name in EXPECTED_TYPES:
            if type_name not in existing_names:
                print(f"   Création de '{type_name}'...")
                new_type = AmortizationType(
                    name=type_name,
                    level_2_value="",  # Sera défini via l'interface
                    level_1_values=json.dumps([]),
                    start_date=None,
                    duration=0.0,
                    annual_amount=None
                )
                db.add(new_type)
                created_count += 1
                print(f"   ✓ Type créé : {type_name}")
        
        if created_count > 0:
            db.commit()
            print(f"\n   ✓ {created_count} type(s) créé(s)")
        else:
            print("\n   ✓ Tous les types sont déjà présents")
        
        # 3. Vérification finale
        print("\n3. Vérification finale...")
        all_types = db.query(AmortizationType).order_by(AmortizationType.name).all()
        existing_names = {atype.name for atype in all_types}
        
        missing = [name for name in EXPECTED_TYPES if name not in existing_names]
        if missing:
            print(f"   ⚠️  Types toujours manquants : {missing}")
            return 1
        else:
            print("   ✓ Tous les 7 types sont présents !")
            print("\n   Types en BDD :")
            for atype in sorted(all_types, key=lambda x: x.name):
                if atype.name in EXPECTED_TYPES:
                    print(f"     ✓ {atype.name}")
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

