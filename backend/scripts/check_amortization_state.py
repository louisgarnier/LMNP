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
from backend.database.models import AmortizationType, AmortizationResult, Transaction, EnrichedTransaction
from backend.api.services.amortization_service import calculate_yearly_amounts
from sqlalchemy import func, and_
from datetime import date


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
                
                # Calculer le montant d'immobilisation (somme des transactions)
                amount = 0.0
                transaction_count = 0
                if level_1_values:
                    # Montant total
                    amount_result = db.query(func.sum(Transaction.quantite)).join(
                        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
                    ).filter(
                        and_(
                            EnrichedTransaction.level_2 == t.level_2_value,
                            EnrichedTransaction.level_1.in_(level_1_values)
                        )
                    ).scalar()
                    amount = abs(amount_result) if amount_result else 0.0
                    
                    # Nombre de transactions
                    transaction_count = db.query(func.count(Transaction.id)).join(
                        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
                    ).filter(
                        and_(
                            EnrichedTransaction.level_2 == t.level_2_value,
                            EnrichedTransaction.level_1.in_(level_1_values)
                        )
                    ).scalar() or 0
                
                print(f'\nID {t.id}: {t.name}')
                print(f'  - Level 2: {t.level_2_value}')
                print(f'  - Level 1 values: {len(level_1_values)} valeur(s)')
                if level_1_values:
                    print(f'    → {level_1_str}')
                print(f'  - Start date: {t.start_date or "(null)"}')
                print(f'  - Duration: {t.duration} années')
                print(f'  - Annual amount (manuel): {t.annual_amount if t.annual_amount is not None and t.annual_amount != 0 else "(null - calcul automatique)"}')
                
                # Calculer l'annuité automatique : abs(Montant) / Durée
                calculated_annual_amount = None
                if amount != 0 and t.duration > 0:
                    calculated_annual_amount = abs(amount) / t.duration
                
                # Afficher l'annuité effective (manuelle si définie, sinon calculée)
                effective_annual_amount = t.annual_amount if t.annual_amount is not None and t.annual_amount != 0 else calculated_annual_amount
                if effective_annual_amount is not None:
                    print(f'  - Annuité effective: {effective_annual_amount:,.2f} €')
                else:
                    print(f'  - Annuité effective: (non calculable)')
                
                print(f'  - Montant d\'immobilisation: {amount:,.2f} €')
                print(f'  - Nombre de transactions: {transaction_count}')
                
                # Calculer le montant cumulé d'amortissement dynamiquement
                # (même logique que l'endpoint backend)
                cumulated_amount = 0.0
                if t.duration > 0 and level_1_values:
                    today = date.today()
                    
                    # Récupérer toutes les transactions correspondantes
                    transactions = db.query(Transaction).join(
                        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
                    ).filter(
                        and_(
                            EnrichedTransaction.level_2 == t.level_2_value,
                            EnrichedTransaction.level_1.in_(level_1_values)
                        )
                    ).all()
                    
                    # Calculer l'annuité du type (si définie)
                    annual_amount = t.annual_amount if t.annual_amount is not None and t.annual_amount != 0 else None
                    
                    # Pour chaque transaction, calculer le montant cumulé
                    for transaction in transactions:
                        # Déterminer la date de début
                        start_date = t.start_date if t.start_date else transaction.date
                        
                        # Vérifier si la date de début est dans le futur
                        if start_date > today:
                            continue
                        
                        # Montant de la transaction
                        transaction_amount = abs(transaction.quantite)
                        
                        # Calculer l'annuité pour cette transaction
                        if annual_amount is None:
                            transaction_annual_amount = transaction_amount / t.duration
                        else:
                            transaction_annual_amount = annual_amount
                        
                        # Calculer les montants par année
                        yearly_amounts = calculate_yearly_amounts(
                            start_date=start_date,
                            total_amount=-transaction_amount,
                            duration=t.duration,
                            annual_amount=transaction_annual_amount
                        )
                        
                        # Sommer les montants jusqu'à l'année en cours (incluse)
                        transaction_cumulated = 0.0
                        for year, amount in yearly_amounts.items():
                            if year <= today.year:
                                # Prendre le montant complet de l'année (pas de prorata pour l'année en cours)
                                transaction_cumulated += abs(amount)
                        
                        cumulated_amount += transaction_cumulated
                
                print(f'  - Montant cumulé d\'amortissement: {cumulated_amount:,.2f} €')
                
                # Afficher le nombre de résultats d'amortissement pour ce type
                result_count = db.query(func.count(AmortizationResult.id)).filter(
                    AmortizationResult.category == t.name
                ).scalar() or 0
                print(f'  - Nombre de résultats d\'amortissement: {result_count}')
        
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

