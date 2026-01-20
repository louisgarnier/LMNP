"""
Script pour recalculer tous les amortissements avec la nouvelle logique corrigée

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.api.services.amortization_service import recalculate_all_amortizations

def main():
    """Recalculer tous les amortissements"""
    db = next(get_db())
    
    print("=" * 100)
    print("RECALCUL DE TOUS LES AMORTISSEMENTS")
    print("=" * 100)
    print()
    
    count = recalculate_all_amortizations(db)
    
    print(f"✅ {count} transaction(s) recalculée(s)")
    print()
    print("Les amortissements ont été recalculés avec la nouvelle logique corrigée.")
    print("La dernière année utilise maintenant le solde restant exact au lieu d'ajouter")
    print("le 'remaining' à l'annuité, ce qui évite qu'elle dépasse l'annuité normale.")
    print()
    
    db.close()


if __name__ == "__main__":
    main()
