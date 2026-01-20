"""
Script de test pour vérifier que les dates de début d'amortissement sont correctement prises en compte

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    AmortizationType
)
from backend.api.services.amortization_service import (
    recalculate_transaction_amortization,
    calculate_yearly_amounts
)
import json

def test_amortization_start_dates():
    """Tester que les dates de début sont correctement prises en compte"""
    db = next(get_db())
    
    print("=" * 100)
    print("TEST DES DATES DE DÉBUT D'AMORTISSEMENT")
    print("=" * 100)
    print()
    
    # Récupérer toutes les transactions avec amortissements
    transactions_with_amort = db.query(Transaction).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).join(
        AmortizationType, 
        AmortizationType.level_2_value == EnrichedTransaction.level_2
    ).filter(
        AmortizationType.duration > 0
    ).distinct().all()
    
    print(f"Nombre de transactions avec amortissements: {len(transactions_with_amort)}")
    print()
    
    issues = []
    
    for transaction in transactions_with_amort[:10]:  # Limiter à 10 pour le test
        # Récupérer l'enrichissement
        enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction.id
        ).first()
        
        if not enriched:
            continue
        
        # Trouver le type d'amortissement
        amortization_types = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == enriched.level_2
        ).all()
        
        matching_type = None
        for atype in amortization_types:
            level_1_values = json.loads(atype.level_1_values or "[]")
            if enriched.level_1 in level_1_values:
                matching_type = atype
                break
        
        if not matching_type:
            continue
        
        # Déterminer la date de début attendue
        expected_start_date = matching_type.start_date if matching_type.start_date else transaction.date
        
        # Récupérer les résultats d'amortissement
        results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).order_by(AmortizationResult.year).all()
        
        if not results:
            continue
        
        # Vérifier que la première année correspond à la date de début
        first_result = results[0]
        first_year = first_result.year
        
        # La première année devrait être l'année de start_date
        if first_year != expected_start_date.year:
            issues.append({
                'transaction_id': transaction.id,
                'transaction_date': transaction.date,
                'type_start_date': matching_type.start_date,
                'expected_start_date': expected_start_date,
                'expected_first_year': expected_start_date.year,
                'actual_first_year': first_year,
                'type_name': matching_type.name
            })
    
    if issues:
        print(f"⚠️  {len(issues)} problème(s) détecté(s):")
        print()
        for issue in issues:
            print(f"Transaction ID: {issue['transaction_id']}")
            print(f"  Date transaction: {issue['transaction_date']}")
            print(f"  Date début type (override): {issue['type_start_date']}")
            print(f"  Date début attendue: {issue['expected_start_date']} (année: {issue['expected_first_year']})")
            print(f"  Première année calculée: {issue['actual_first_year']}")
            print(f"  Type: {issue['type_name']}")
            print()
    else:
        print("✅ Toutes les dates de début sont correctement prises en compte")
        print()
    
    # Afficher le détail des calculs pour toutes les transactions
    print("=" * 100)
    print("DÉTAIL DES CALCULS POUR CHAQUE TRANSACTION")
    print("=" * 100)
    print()
    
    for transaction in transactions_with_amort:
        enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction.id
        ).first()
        
        if not enriched:
            continue
        
        amortization_types = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == enriched.level_2
        ).all()
        
        matching_type = None
        for atype in amortization_types:
            level_1_values = json.loads(atype.level_1_values or "[]")
            if enriched.level_1 in level_1_values:
                matching_type = atype
                break
        
        if not matching_type:
            continue
        
        # Déterminer la date de début utilisée
        type_start_date = matching_type.start_date
        transaction_date = transaction.date
        used_start_date = type_start_date if type_start_date else transaction_date
        
        # Calculer l'annuité
        if matching_type.annual_amount and matching_type.annual_amount != 0:
            annual_amount = abs(matching_type.annual_amount)
            annual_source = f"Configurée dans le type: {matching_type.annual_amount:.2f} €"
        else:
            annual_amount = abs(transaction.quantite) / matching_type.duration if matching_type.duration > 0 else 0
            annual_source = f"Calculée: {abs(transaction.quantite):.2f} € / {matching_type.duration} ans = {annual_amount:.2f} €"
        
        # Calculer les montants théoriques
        theoretical_amounts = calculate_yearly_amounts(
            start_date=used_start_date,
            total_amount=transaction.quantite,
            duration=matching_type.duration,
            annual_amount=matching_type.annual_amount
        )
        
        # Récupérer les résultats en base
        results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).order_by(AmortizationResult.year).all()
        
        print(f"{'=' * 100}")
        print(f"TRANSACTION #{transaction.id}: {transaction.nom}")
        print(f"{'=' * 100}")
        print()
        print(f"📅 DATES:")
        print(f"  - Date de la transaction: {transaction_date}")
        print(f"  - Date début type (override): {type_start_date or 'Aucune (NULL)'}")
        print(f"  - Date début utilisée pour le calcul: {used_start_date} {'(override)' if type_start_date else '(date transaction)'}")
        print()
        print(f"💰 MONTANT:")
        print(f"  - Montant transaction: {transaction.quantite:.2f} €")
        print(f"  - Montant absolu: {abs(transaction.quantite):.2f} €")
        print()
        print(f"⚙️  CONFIGURATION DU TYPE:")
        print(f"  - Type: {matching_type.name}")
        print(f"  - Durée: {matching_type.duration} ans")
        print(f"  - Annuité: {annual_source}")
        print()
        print(f"📊 CALCUL DES ANNÉES:")
        print(f"  - Date de début: {used_start_date}")
        print(f"  - Année de début: {used_start_date.year}")
        print(f"  - Année de fin calculée: {used_start_date.year + int(matching_type.duration) - 1}")
        print(f"  - Date de fin: {date(used_start_date.year + int(matching_type.duration) - 1, 12, 31)}")
        print()
        print(f"📈 RÉSULTATS CALCULÉS (théoriques):")
        print(f"  {'Année':<8} {'Montant':<15} {'Montant (abs)':<15} {'Annuité':<15}")
        print(f"  {'-' * 55}")
        total_theoretical = 0.0
        for year in sorted(theoretical_amounts.keys()):
            amount = theoretical_amounts[year]
            abs_amount = abs(amount)
            total_theoretical += abs_amount
            print(f"  {year:<8} {amount:>12.2f} € {abs_amount:>12.2f} € {annual_amount:>13.2f} €")
        print(f"  {'-' * 55}")
        print(f"  {'Total':<8} {'':>12} {total_theoretical:>12.2f} €")
        print()
        print(f"💾 RÉSULTATS EN BASE DE DONNÉES:")
        if results:
            print(f"  {'Année':<8} {'Montant':<15} {'Montant (abs)':<15} {'Catégorie':<30}")
            print(f"  {'-' * 70}")
            total_db = 0.0
            for result in results:
                abs_amount = abs(result.amount)
                total_db += abs_amount
                print(f"  {result.year:<8} {result.amount:>12.2f} € {abs_amount:>12.2f} € {result.category[:28]:<30}")
            print(f"  {'-' * 70}")
            print(f"  {'Total':<8} {'':>12} {total_db:>12.2f} €")
            print()
            
            # Comparer théorique vs base
            print(f"🔍 COMPARAISON THÉORIQUE vs BASE:")
            if len(theoretical_amounts) == len(results):
                all_match = True
                for year in sorted(theoretical_amounts.keys()):
                    theoretical = theoretical_amounts[year]
                    db_result = next((r for r in results if r.year == year), None)
                    if db_result:
                        db_amount = db_result.amount
                        diff = abs(theoretical - db_amount)
                        if diff > 0.01:
                            print(f"  ⚠️  {year}: théorique={theoretical:.2f} €, base={db_amount:.2f} €, diff={diff:.2f} €")
                            all_match = False
                        else:
                            print(f"  ✓  {year}: théorique={theoretical:.2f} €, base={db_amount:.2f} €")
                    else:
                        print(f"  ⚠️  {year}: présent dans théorique mais absent en base")
                        all_match = False
                
                if all_match:
                    print(f"  ✅ Tous les montants correspondent")
            else:
                print(f"  ⚠️  Nombre d'années différent: théorique={len(theoretical_amounts)}, base={len(results)}")
        else:
            print(f"  ⚠️  Aucun résultat en base de données")
        print()
        print()
    
    db.close()


if __name__ == "__main__":
    test_amortization_start_dates()
