"""
Script d'analyse des calculs d'amortissement pour identifier les problèmes

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from collections import defaultdict

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
from sqlalchemy import func
from datetime import date

def analyze_amortization_calculations():
    """Analyser les calculs d'amortissement pour identifier les problèmes"""
    db = next(get_db())
    
    print("=" * 100)
    print("ANALYSE DES CALCULS D'AMORTISSEMENT")
    print("=" * 100)
    print()
    
    # Récupérer tous les résultats d'amortissement groupés par transaction
    results_by_transaction = defaultdict(list)
    
    all_results = db.query(AmortizationResult).order_by(
        AmortizationResult.transaction_id,
        AmortizationResult.year
    ).all()
    
    for result in all_results:
        results_by_transaction[result.transaction_id].append(result)
    
    print(f"Nombre de transactions avec amortissements: {len(results_by_transaction)}")
    print()
    
    # Analyser chaque transaction
    issues_found = []
    
    for transaction_id, results in results_by_transaction.items():
        # Récupérer la transaction
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            continue
        
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
            
            import json
            for atype in types:
                level_1_values = json.loads(atype.level_1_values or "[]")
                if enriched.level_1 in level_1_values:
                    amortization_type = atype
                    break
        
        # Trier les résultats par année
        results_sorted = sorted(results, key=lambda r: r.year)
        
        # Calculer les totaux
        total_calculated = sum(abs(r.amount) for r in results_sorted)
        transaction_amount = abs(transaction.quantite)
        
        # Identifier les problèmes
        issues = []
        
        # Problème 1: Dernière année plus grande que l'annuité
        if results_sorted:
            last_result = results_sorted[-1]
            last_year_amount = abs(last_result.amount)
            
            if amortization_type:
                if amortization_type.annual_amount:
                    annual_amount = abs(amortization_type.annual_amount)
                else:
                    annual_amount = transaction_amount / amortization_type.duration if amortization_type.duration > 0 else 0
                
                if last_year_amount > annual_amount * 1.1:  # Tolérance de 10%
                    issues.append(f"Dernière année ({last_result.year}) = {last_year_amount:.2f} € > Annuité = {annual_amount:.2f} €")
        
        # Problème 2: Total calculé différent du montant de la transaction
        if abs(total_calculated - transaction_amount) > 0.01:
            issues.append(f"Total calculé ({total_calculated:.2f} €) ≠ Montant transaction ({transaction_amount:.2f} €)")
        
        # Problème 3: Années manquantes ou en trop
        if amortization_type:
            start_date = amortization_type.start_date if amortization_type.start_date else transaction.date
            expected_years = amortization_type.duration
            actual_years = len(results_sorted)
            
            if actual_years != expected_years:
                issues.append(f"Nombre d'années: {actual_years} (attendu: {expected_years})")
        
        # Afficher les détails si problème trouvé
        if issues:
            issues_found.append({
                'transaction_id': transaction_id,
                'transaction': transaction,
                'enriched': enriched,
                'amortization_type': amortization_type,
                'results': results_sorted,
                'issues': issues,
                'total_calculated': total_calculated,
                'transaction_amount': transaction_amount
            })
    
    # Afficher les problèmes trouvés
    if issues_found:
        print(f"⚠️  {len(issues_found)} transaction(s) avec problème(s) détecté(s)")
        print()
        
        for idx, issue_data in enumerate(issues_found, 1):
            print(f"{'=' * 100}")
            print(f"PROBLÈME #{idx}")
            print(f"{'=' * 100}")
            
            transaction = issue_data['transaction']
            enriched = issue_data['enriched']
            amortization_type = issue_data['amortization_type']
            results = issue_data['results']
            issues = issue_data['issues']
            
            print(f"Transaction ID: {transaction.id}")
            print(f"Date: {transaction.date}")
            print(f"Montant: {transaction.quantite:.2f} €")
            print(f"Nom: {transaction.nom[:60]}")
            print()
            
            if enriched:
                print(f"Level 1: {enriched.level_1}")
                print(f"Level 2: {enriched.level_2}")
                print(f"Level 3: {enriched.level_3}")
                print()
            
            if amortization_type:
                print(f"Type d'amortissement: {amortization_type.name}")
                print(f"Durée: {amortization_type.duration} ans")
                print(f"Date de début: {amortization_type.start_date}")
                if amortization_type.annual_amount:
                    print(f"Annuité configurée: {amortization_type.annual_amount:.2f} €")
                else:
                    calculated_annual = abs(transaction.quantite) / amortization_type.duration if amortization_type.duration > 0 else 0
                    print(f"Annuité calculée: {calculated_annual:.2f} €")
                print()
            
            print("Problèmes détectés:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
            print()
            
            print("Détail des amortissements par année:")
            print(f"  {'Année':<8} {'Montant':<15} {'Montant (abs)':<15} {'Annuité attendue':<20}")
            print(f"  {'-' * 60}")
            
            if amortization_type:
                if amortization_type.annual_amount:
                    expected_annual = abs(amortization_type.annual_amount)
                else:
                    expected_annual = abs(transaction.quantite) / amortization_type.duration if amortization_type.duration > 0 else 0
            else:
                expected_annual = 0
            
            for result in results:
                abs_amount = abs(result.amount)
                status = "⚠️" if abs_amount > expected_annual * 1.1 else "✓"
                print(f"  {status} {result.year:<8} {result.amount:>12.2f} € {abs_amount:>12.2f} € {expected_annual:>18.2f} €")
            
            print()
            print(f"Total calculé: {issue_data['total_calculated']:.2f} €")
            print(f"Montant transaction: {issue_data['transaction_amount']:.2f} €")
            print(f"Différence: {abs(issue_data['total_calculated'] - issue_data['transaction_amount']):.2f} €")
            print()
    else:
        print("✅ Aucun problème détecté dans les calculs d'amortissement")
        print()
    
    # Statistiques générales
    print("=" * 100)
    print("STATISTIQUES GÉNÉRALES")
    print("=" * 100)
    print()
    
    total_transactions = len(results_by_transaction)
    total_results = len(all_results)
    
    print(f"Nombre de transactions avec amortissements: {total_transactions}")
    print(f"Nombre total de résultats d'amortissement: {total_results}")
    print(f"Moyenne de résultats par transaction: {total_results / total_transactions if total_transactions > 0 else 0:.2f}")
    print()
    
    # Distribution par année
    results_by_year = defaultdict(int)
    for result in all_results:
        results_by_year[result.year] += 1
    
    print("Distribution des résultats par année:")
    for year in sorted(results_by_year.keys()):
        print(f"  {year}: {results_by_year[year]} résultats")
    print()
    
    db.close()


if __name__ == "__main__":
    analyze_amortization_calculations()
