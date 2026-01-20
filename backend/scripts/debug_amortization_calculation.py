"""
Script de debug pour comprendre le calcul d'amortissement d'une transaction spécifique

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Transaction, EnrichedTransaction, AmortizationType, AmortizationResult
from backend.api.services.amortization_service import calculate_yearly_amounts
import json

def debug_transaction(transaction_id: int):
    """Debug une transaction spécifique"""
    db = next(get_db())
    
    # Récupérer la transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        print(f"Transaction {transaction_id} non trouvée")
        return
    
    # Récupérer l'enrichissement
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction_id
    ).first()
    
    # Trouver le type d'amortissement
    amortization_type = None
    if enriched and enriched.level_2:
        types = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == enriched.level_2
        ).all()
        
        for atype in types:
            level_1_values = json.loads(atype.level_1_values or "[]")
            if enriched.level_1 in level_1_values:
                amortization_type = atype
                break
    
    if not amortization_type:
        print(f"Type d'amortissement non trouvé pour transaction {transaction_id}")
        return
    
    print("=" * 100)
    print(f"DEBUG TRANSACTION {transaction_id}")
    print("=" * 100)
    print()
    print(f"Transaction: {transaction.nom}")
    print(f"Date: {transaction.date}")
    print(f"Montant: {transaction.quantite:.2f} €")
    print()
    print(f"Type d'amortissement: {amortization_type.name}")
    print(f"Durée: {amortization_type.duration} ans")
    print(f"Date de début: {amortization_type.start_date or transaction.date}")
    if amortization_type.annual_amount:
        print(f"Annuité configurée: {amortization_type.annual_amount:.2f} €")
    else:
        calculated_annual = abs(transaction.quantite) / amortization_type.duration if amortization_type.duration > 0 else 0
        print(f"Annuité calculée: {calculated_annual:.2f} €")
    print()
    
    # Déterminer la date de début
    start_date = amortization_type.start_date if amortization_type.start_date else transaction.date
    
    # Calculer les montants
    yearly_amounts = calculate_yearly_amounts(
        start_date=start_date,
        total_amount=transaction.quantite,
        duration=amortization_type.duration,
        annual_amount=amortization_type.annual_amount
    )
    
    print("Résultats du calcul:")
    print(f"  {'Année':<8} {'Montant':<15} {'Montant (abs)':<15}")
    print(f"  {'-' * 40}")
    
    total = 0.0
    for year in sorted(yearly_amounts.keys()):
        amount = yearly_amounts[year]
        abs_amount = abs(amount)
        total += abs_amount
        print(f"  {year:<8} {amount:>12.2f} € {abs_amount:>12.2f} €")
    
    print(f"  {'-' * 40}")
    print(f"  {'Total':<8} {'':>12} {total:>12.2f} €")
    print(f"  {'Attendu':<8} {'':>12} {abs(transaction.quantite):>12.2f} €")
    print(f"  {'Différence':<8} {'':>12} {abs(total - abs(transaction.quantite)):>12.2f} €")
    print()
    
    # Récupérer les résultats en base
    results = db.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == transaction_id
    ).order_by(AmortizationResult.year).all()
    
    print("Résultats en base de données:")
    print(f"  {'Année':<8} {'Montant':<15} {'Montant (abs)':<15}")
    print(f"  {'-' * 40}")
    
    total_db = 0.0
    for result in results:
        abs_amount = abs(result.amount)
        total_db += abs_amount
        print(f"  {result.year:<8} {result.amount:>12.2f} € {abs_amount:>12.2f} €")
    
    print(f"  {'-' * 40}")
    print(f"  {'Total':<8} {'':>12} {total_db:>12.2f} €")
    print()
    
    # Comparer
    if len(yearly_amounts) != len(results):
        print(f"⚠️  Nombre d'années différent: calcul={len(yearly_amounts)}, base={len(results)}")
    else:
        print("Comparaison calcul vs base:")
        for year in sorted(yearly_amounts.keys()):
            calculated = yearly_amounts[year]
            db_result = next((r for r in results if r.year == year), None)
            if db_result:
                db_amount = db_result.amount
                diff = abs(calculated - db_amount)
                if diff > 0.01:
                    print(f"  ⚠️  {year}: calcul={calculated:.2f} €, base={db_amount:.2f} €, diff={diff:.2f} €")
                else:
                    print(f"  ✓  {year}: calcul={calculated:.2f} €, base={db_amount:.2f} €")
    
    db.close()


if __name__ == "__main__":
    # Debug la transaction 22 (celle avec le plus gros problème)
    debug_transaction(22)
