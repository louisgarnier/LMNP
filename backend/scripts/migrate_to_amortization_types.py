"""
Script de migration vers la nouvelle structure AmortizationType.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script migre les données de AmortizationConfig vers la nouvelle table amortization_types.
Crée les 7 types initiaux avec les noms des catégories.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database, engine
from backend.database.models import Base, AmortizationType, AmortizationConfig
from sqlalchemy import inspect


def migrate_to_amortization_types():
    """
    Migre vers la nouvelle structure AmortizationType.
    Crée les 7 types initiaux si la table est vide.
    """
    print("🔄 Migration vers la nouvelle structure AmortizationType...")
    
    # Initialiser la base de données pour créer la table si elle n'existe pas
    init_database()
    
    db = SessionLocal()
    
    try:
        # Vérifier si la table existe
        inspector = inspect(engine)
        table_exists = 'amortization_types' in inspector.get_table_names()
        
        if not table_exists:
            print("📋 Création de la table amortization_types...")
            Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables['amortization_types']])
            print("✅ Table créée")
        
        # Vérifier si des types existent déjà
        existing_types = db.query(AmortizationType).count()
        
        if existing_types > 0:
            print(f"✅ La table contient déjà {existing_types} type(s) d'amortissement")
            print("   Migration non nécessaire")
            return
        
        # Récupérer le level_2_value depuis AmortizationConfig (ou utiliser valeur par défaut)
        config = db.query(AmortizationConfig).first()
        level_2_value = "ammortissements"  # Valeur par défaut
        
        if config:
            level_2_value = config.level_2_value
            print(f"📋 Utilisation de level_2_value depuis config existante: '{level_2_value}'")
        else:
            print(f"📋 Utilisation de level_2_value par défaut: '{level_2_value}'")
        
        # Créer les 7 types initiaux
        initial_types = [
            {
                "name": "Part terrain",
                "level_1_values": []
            },
            {
                "name": "Immobilisation structure/GO",
                "level_1_values": []
            },
            {
                "name": "Immobilisation mobilier",
                "level_1_values": []
            },
            {
                "name": "Immobilisation IGT",
                "level_1_values": []
            },
            {
                "name": "Immobilisation agencements",
                "level_1_values": []
            },
            {
                "name": "Immobilisation Facade/Toiture",
                "level_1_values": []
            },
            {
                "name": "Immobilisation travaux",
                "level_1_values": []
            }
        ]
        
        print(f"📋 Création des {len(initial_types)} types initiaux...")
        
        for type_data in initial_types:
            amortization_type = AmortizationType(
                name=type_data["name"],
                level_2_value=level_2_value,
                level_1_values=type_data["level_1_values"],
                start_date=None,
                duration=0.0,
                annual_amount=None
            )
            db.add(amortization_type)
            print(f"   ✅ {type_data['name']}")
        
        db.commit()
        print(f"\n✅ Migration terminée : {len(initial_types)} types créés")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors de la migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate_to_amortization_types()
        print("\n✅ Migration terminée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

