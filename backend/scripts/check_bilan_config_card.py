"""
Script pour afficher les données de la card de configuration du bilan en base de données.

Ce script affiche:
1. La configuration (BilanConfig) - level_3_values sélectionnés
2. Tous les mappings (BilanMapping) avec leurs détails

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import BilanMapping, BilanConfig

# Initialize database
init_database()


def display_bilan_config_card():
    """Affiche les données de la card de configuration du bilan."""
    print("=" * 80)
    print("📊 DONNÉES DE LA CARD DE CONFIGURATION DU BILAN")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # 1. Afficher la configuration (Level 3 values)
        print("\n🔧 CONFIGURATION (Level 3 - Valeurs à considérer)")
        print("-" * 80)
        
        config = db.query(BilanConfig).first()
        if config:
            level_3_values = json.loads(config.level_3_values) if config.level_3_values else []
            print(f"ID Config: {config.id}")
            print(f"Level 3 values ({len(level_3_values)}):")
            if level_3_values:
                for i, value in enumerate(level_3_values, 1):
                    print(f"  {i}. {value}")
            else:
                print("  (aucune valeur sélectionnée)")
            print(f"Created at: {config.created_at}")
            print(f"Updated at: {config.updated_at}")
        else:
            print("  ⚠️  Aucune configuration trouvée (utilise les valeurs par défaut)")
        
        # 2. Afficher tous les mappings
        print("\n📋 MAPPINGS (Catégories comptables)")
        print("-" * 80)
        
        mappings = db.query(BilanMapping).order_by(
            BilanMapping.type,
            BilanMapping.sub_category,
            BilanMapping.category_name
        ).all()
        
        if not mappings:
            print("  ⚠️  Aucun mapping trouvé")
        else:
            print(f"Total: {len(mappings)} mapping(s)\n")
            
            # Grouper par type (ACTIF/PASSIF)
            actif_mappings = [m for m in mappings if m.type == "ACTIF"]
            passif_mappings = [m for m in mappings if m.type == "PASSIF"]
            
            # Afficher ACTIF
            if actif_mappings:
                print("=" * 80)
                print("📈 ACTIF")
                print("=" * 80)
                
                # Grouper par sous-catégorie
                sub_categories = {}
                for mapping in actif_mappings:
                    sub_cat = mapping.sub_category
                    if sub_cat not in sub_categories:
                        sub_categories[sub_cat] = []
                    sub_categories[sub_cat].append(mapping)
                
                for sub_cat, sub_mappings in sub_categories.items():
                    print(f"\n  📁 {sub_cat} ({len(sub_mappings)} catégorie(s))")
                    print("  " + "-" * 76)
                    
                    for mapping in sub_mappings:
                        print(f"\n    ID: {mapping.id}")
                        print(f"    Catégorie comptable: {mapping.category_name}")
                        
                        if mapping.is_special:
                            print(f"    ⚙️  Type: SPÉCIAL")
                            print(f"    Source spéciale: {mapping.special_source or 'N/A'}")
                            if mapping.compte_resultat_view_id:
                                print(f"    Vue compte de résultat ID: {mapping.compte_resultat_view_id}")
                            print(f"    Level 1 values: (aucun - catégorie spéciale)")
                        else:
                            print(f"    Type: NORMAL")
                            level_1_values = json.loads(mapping.level_1_values) if mapping.level_1_values else []
                            if level_1_values:
                                print(f"    Level 1 values ({len(level_1_values)}):")
                                for value in level_1_values:
                                    print(f"      - {value}")
                            else:
                                print(f"    Level 1 values: (aucun)")
                        
                        print(f"    Created: {mapping.created_at}")
                        print(f"    Updated: {mapping.updated_at}")
            
            # Afficher PASSIF
            if passif_mappings:
                print("\n" + "=" * 80)
                print("📉 PASSIF")
                print("=" * 80)
                
                # Grouper par sous-catégorie
                sub_categories = {}
                for mapping in passif_mappings:
                    sub_cat = mapping.sub_category
                    if sub_cat not in sub_categories:
                        sub_categories[sub_cat] = []
                    sub_categories[sub_cat].append(mapping)
                
                for sub_cat, sub_mappings in sub_categories.items():
                    print(f"\n  📁 {sub_cat} ({len(sub_mappings)} catégorie(s))")
                    print("  " + "-" * 76)
                    
                    for mapping in sub_mappings:
                        print(f"\n    ID: {mapping.id}")
                        print(f"    Catégorie comptable: {mapping.category_name}")
                        
                        if mapping.is_special:
                            print(f"    ⚙️  Type: SPÉCIAL")
                            print(f"    Source spéciale: {mapping.special_source or 'N/A'}")
                            if mapping.compte_resultat_view_id:
                                print(f"    Vue compte de résultat ID: {mapping.compte_resultat_view_id}")
                            print(f"    Level 1 values: (aucun - catégorie spéciale)")
                        else:
                            print(f"    Type: NORMAL")
                            level_1_values = json.loads(mapping.level_1_values) if mapping.level_1_values else []
                            if level_1_values:
                                print(f"    Level 1 values ({len(level_1_values)}):")
                                for value in level_1_values:
                                    print(f"      - {value}")
                            else:
                                print(f"    Level 1 values: (aucun)")
                        
                        print(f"    Created: {mapping.created_at}")
                        print(f"    Updated: {mapping.updated_at}")
            
            # Résumé
            print("\n" + "=" * 80)
            print("📊 RÉSUMÉ")
            print("=" * 80)
            print(f"Total mappings: {len(mappings)}")
            print(f"  - ACTIF: {len(actif_mappings)}")
            print(f"  - PASSIF: {len(passif_mappings)}")
            
            special_count = sum(1 for m in mappings if m.is_special)
            normal_count = len(mappings) - special_count
            print(f"  - Normaux: {normal_count}")
            print(f"  - Spéciaux: {special_count}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    display_bilan_config_card()
