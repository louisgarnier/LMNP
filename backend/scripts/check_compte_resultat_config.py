#!/usr/bin/env python3
"""
Script pour afficher le contenu de la table compte_resultat_config.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import CompteResultatConfig

def main():
    """Affiche le contenu de la table compte_resultat_config."""
    print("=" * 80)
    print("  CONTENU DE LA TABLE compte_resultat_config")
    print("=" * 80)
    print()
    
    # Initialize database to ensure tables exist
    init_database()
    
    db = SessionLocal()
    try:
        # Récupérer toutes les configurations
        configs = db.query(CompteResultatConfig).all()
        
        if not configs:
            print("❌ Aucune configuration trouvée dans la table compte_resultat_config")
            print()
            print("La table est vide.")
            return
        
        print(f"📊 Nombre de configurations trouvées: {len(configs)}")
        print()
        
        for idx, config in enumerate(configs, 1):
            print("-" * 80)
            print(f"Configuration #{idx}")
            print("-" * 80)
            print(f"  ID: {config.id}")
            print(f"  Created at: {config.created_at}")
            print(f"  Updated at: {config.updated_at}")
            print()
            
            # Afficher level_3_values
            if config.level_3_values:
                try:
                    level_3_values = json.loads(config.level_3_values)
                    print(f"  Level 3 values (JSON): {config.level_3_values}")
                    print(f"  Level 3 values (parsed): {level_3_values}")
                    print(f"  Nombre de valeurs level_3: {len(level_3_values) if isinstance(level_3_values, list) else 'N/A'}")
                except json.JSONDecodeError as e:
                    print(f"  ⚠️  Erreur de parsing JSON: {e}")
                    print(f"  Level 3 values (raw): {config.level_3_values}")
            else:
                print("  Level 3 values: NULL (aucune valeur sélectionnée)")
            
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de la table: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
