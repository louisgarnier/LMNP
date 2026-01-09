"""
Script d'initialisation pour créer les 7 types d'amortissement par défaut.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script crée les 7 types initiaux si la table amortization_types est vide.

Usage:
    python backend/scripts/init_amortization_types.py
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType


# Les 7 types initiaux (template par défaut)
INITIAL_TYPES = [
    "Part terrain",
    "Immobilisation structure/GO",
    "Immobilisation mobilier",
    "Immobilisation IGT",
    "Immobilisation agencements",
    "Immobilisation Facade/Toiture",
    "Immobilisation travaux",
]


def create_initial_types(db, level_2_value: str = None):
    """
    Crée les 7 types initiaux si la table est vide.
    
    Args:
        db: Session de base de données
        level_2_value: Valeur level_2 à utiliser (optionnel, sera défini plus tard via l'interface)
    """
    # Vérifier si des types existent déjà
    existing_count = db.query(AmortizationType).count()
    
    if existing_count > 0:
        print(f"   ⚠ La table contient déjà {existing_count} type(s), aucun type initial créé")
        return 0
    
    print(f"   Création des {len(INITIAL_TYPES)} types initiaux...")
    
    created_count = 0
    for type_name in INITIAL_TYPES:
        # Vérifier si le type existe déjà (par nom)
        existing = db.query(AmortizationType).filter(AmortizationType.name == type_name).first()
        if existing:
            print(f"   ⚠ Type '{type_name}' existe déjà, ignoré")
            continue
        
        # Créer le nouveau type
        new_type = AmortizationType(
            name=type_name,
            level_2_value=level_2_value or "",  # Sera défini via l'interface
            level_1_values=json.dumps([]),  # Liste vide initialement
            start_date=None,
            duration=0.0,  # 0 = non amortissable par défaut
            annual_amount=None
        )
        
        db.add(new_type)
        created_count += 1
        print(f"   ✓ Type créé : {type_name}")
    
    if created_count > 0:
        db.commit()
        print(f"\n   ✓ {created_count} type(s) créé(s) avec succès")
    else:
        print(f"\n   ⚠ Aucun nouveau type créé (tous existent déjà)")
    
    return created_count


def main():
    """Initialise les types d'amortissement par défaut."""
    print("=" * 60)
    print("Initialisation des types d'amortissement")
    print("=" * 60)
    
    # Initialiser la base de données (créer les tables si nécessaire)
    print("\n1. Initialisation de la base de données...")
    init_database()
    print("   ✓ Base de données initialisée")
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Créer les types initiaux
        print("\n2. Création des types initiaux...")
        created_count = create_initial_types(db)
        
        if created_count > 0:
            print(f"\n✓ Initialisation terminée : {created_count} type(s) créé(s)")
            return 0
        else:
            print("\n✓ Initialisation terminée : aucun nouveau type nécessaire")
            return 0
            
    except Exception as e:
        print(f"\n✗ ERREUR lors de l'initialisation : {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

