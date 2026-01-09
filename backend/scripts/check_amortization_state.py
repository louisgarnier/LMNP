"""
Script pour vérifier l'état complet de la base de données pour les amortissements.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType, AmortizationResult


def main():
    """Vérifie l'état complet de la base de données pour les amortissements."""
    print("=" * 60)
    print("État de la base de données - Amortissements")
    print("=" * 60)
    
    init_database()
    db = SessionLocal()
    
    try:
        # Compter les types
        types_count = db.query(AmortizationType).count()
        print(f'\n📊 Types d\'amortissement : {types_count}')
        
        if types_count > 0:
            print('\nDétail des types :')
            print('-' * 60)
            types = db.query(AmortizationType).order_by(AmortizationType.level_2_value, AmortizationType.name).all()
            for t in types:
                level_1_values = json.loads(t.level_1_values or '[]')
                level_1_str = ', '.join(level_1_values[:3])
                if len(level_1_values) > 3:
                    level_1_str += '...'
                print(f'\nID {t.id}: {t.name}')
                print(f'  - Level 2: {t.level_2_value}')
                print(f'  - Level 1 values: {len(level_1_values)} valeur(s)')
                if level_1_values:
                    print(f'    → {level_1_str}')
                print(f'  - Start date: {t.start_date or "(null)"}')
                print(f'  - Duration: {t.duration} années')
                print(f'  - Annual amount: {t.annual_amount or "(null)"}')
        
        # Compter les résultats
        results_count = db.query(AmortizationResult).count()
        print(f'\n📊 Résultats d\'amortissement : {results_count}')
        
        if results_count > 0:
            print('\nDétail des résultats (premiers 10) :')
            print('-' * 60)
            results = db.query(AmortizationResult).limit(10).all()
            for r in results:
                print(f'  - Transaction {r.transaction_id}, Année {r.year}, Catégorie: {r.category}, Montant: {r.amount}')
        
        # Statistiques par Level 2
        print('\n📊 Statistiques par Level 2 :')
        print('-' * 60)
        from sqlalchemy import func
        stats = db.query(
            AmortizationType.level_2_value,
            func.count(AmortizationType.id).label('count')
        ).group_by(AmortizationType.level_2_value).all()
        for stat in stats:
            print(f'  - {stat.level_2_value}: {stat.count} type(s)')
        
        return 0
        
    except Exception as e:
        print(f'\n✗ ERREUR : {e}')
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

