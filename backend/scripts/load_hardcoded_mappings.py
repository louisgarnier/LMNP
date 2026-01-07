"""
Script de migration pour charger les 50 combinaisons initiales depuis le fichier Excel.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script doit être exécuté une seule fois pour hard coder les valeurs initiales
dans la table allowed_mappings.

Usage:
    python backend/scripts/load_hardcoded_mappings.py
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.api.services.mapping_obligatoire_service import load_allowed_mappings_from_excel


def main():
    """Charge les combinaisons hard codées depuis le fichier Excel."""
    print("=" * 60)
    print("Chargement des mappings autorisés depuis Excel")
    print("=" * 60)
    
    # Initialiser la base de données (créer les tables si nécessaire)
    print("\n1. Initialisation de la base de données...")
    init_database()
    print("   ✓ Base de données initialisée")
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Charger les combinaisons depuis le fichier Excel
        print("\n2. Chargement du fichier Excel...")
        excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
        
        if not excel_path.exists():
            print(f"   ✗ ERREUR : Le fichier n'existe pas : {excel_path}")
            print("   Veuillez vérifier que le fichier est présent dans scripts/")
            return 1
        
        print(f"   Fichier trouvé : {excel_path}")
        
        loaded_count = load_allowed_mappings_from_excel(db, excel_path)
        
        print(f"\n3. Résultat :")
        print(f"   ✓ {loaded_count} combinaisons chargées avec is_hardcoded = True")
        print(f"\n   Les combinaisons sont maintenant protégées et ne peuvent pas être supprimées.")
        print(f"   Le fichier Excel peut être supprimé si vous le souhaitez.")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        db.rollback()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

