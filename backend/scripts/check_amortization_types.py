"""
Script pour vérifier les types d'amortissement en base de données.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
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
    """Vérifie les types d'amortissement en base de données."""
    print("=" * 60)
    print("Vérification des types d'amortissement en BDD")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Récupérer tous les types
        all_types = db.query(AmortizationType).order_by(AmortizationType.name).all()
        
        print(f"\n📊 Types trouvés en BDD : {len(all_types)}")
        print("-" * 60)
        
        if len(all_types) == 0:
            print("⚠️  Aucun type trouvé en base de données !")
            print("\n💡 Pour créer les 7 types initiaux, exécutez :")
            print("   python3 backend/scripts/init_amortization_types.py")
            return 1
        
        # Afficher les types existants
        existing_names = []
        for atype in all_types:
            level_1_values = json.loads(atype.level_1_values or "[]")
            print(f"  {atype.id:2d}. {atype.name}")
            print(f"      - level_2_value: {atype.level_2_value or '(vide)'}")
            print(f"      - level_1_values: {len(level_1_values)} valeur(s)")
            print(f"      - duration: {atype.duration}")
            print(f"      - annual_amount: {atype.annual_amount or '(non défini)'}")
            existing_names.append(atype.name)
        
        # Comparer avec les types attendus
        print("\n" + "=" * 60)
        print("Comparaison avec les 7 types attendus")
        print("=" * 60)
        
        missing_types = []
        for expected_name in EXPECTED_TYPES:
            if expected_name not in existing_names:
                missing_types.append(expected_name)
                print(f"❌ MANQUANT : {expected_name}")
            else:
                print(f"✓  Présent  : {expected_name}")
        
        # Types supplémentaires (non attendus)
        extra_types = [name for name in existing_names if name not in EXPECTED_TYPES]
        if extra_types:
            print("\n⚠️  Types supplémentaires (non dans la liste attendue) :")
            for extra_name in extra_types:
                print(f"   - {extra_name}")
        
        # Résumé
        print("\n" + "=" * 60)
        print("Résumé")
        print("=" * 60)
        print(f"Total en BDD     : {len(all_types)}")
        print(f"Types attendus   : {len(EXPECTED_TYPES)}")
        print(f"Types présents   : {len(EXPECTED_TYPES) - len(missing_types)}")
        print(f"Types manquants  : {len(missing_types)}")
        print(f"Types supplémentaires : {len(extra_types)}")
        
        if missing_types:
            print(f"\n⚠️  {len(missing_types)} type(s) manquant(s) !")
            print("\n💡 Pour créer les types manquants, exécutez :")
            print("   python3 backend/scripts/init_amortization_types.py")
            return 1
        else:
            print("\n✓  Tous les types attendus sont présents !")
            return 0
            
    except Exception as e:
        print(f"\n✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

