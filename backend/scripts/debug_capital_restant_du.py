"""
Script de diagnostic pour le calcul du capital restant dû (Emprunt bancaire)

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Transaction, EnrichedTransaction, LoanPayment, LoanConfig
from sqlalchemy import func, and_
from datetime import date

def analyze_capital_restant_du(year: int):
    """Analyser le calcul du capital restant dû pour une année"""
    db = next(get_db())
    
    print("=" * 80)
    print(f"ANALYSE DU CAPITAL RESTANT DÛ - ANNÉE {year}")
    print("=" * 80)
    print()
    
    end_date = date(year, 12, 31)
    level_1_value = "Dettes financières (emprunt bancaire)"
    
    # 1. Analyser les transactions "Dettes financières (emprunt bancaire)"
    print("1. TRANSACTIONS 'Dettes financières (emprunt bancaire)'")
    print("-" * 80)
    
    transactions = db.query(Transaction).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_1 == level_1_value,
            Transaction.date <= end_date
        )
    ).order_by(Transaction.date).all()
    
    print(f"Nombre de transactions jusqu'au {end_date}: {len(transactions)}")
    print()
    
    if transactions:
        print("Détail des transactions:")
        total = 0.0
        for t in transactions:
            total += t.quantite
            print(f"  {t.date} | {t.quantite:>12.2f} € | {t.nom[:60]}")
        print(f"  {'TOTAL':<12} | {total:>12.2f} €")
        print(f"  {'ABS(TOTAL)':<12} | {abs(total):>12.2f} €")
        print()
    else:
        print("Aucune transaction trouvée.")
        print()
    
    # 2. Analyser les remboursements de capital
    print("2. REMBOURSEMENTS DE CAPITAL (LoanPayment)")
    print("-" * 80)
    
    loan_payments = db.query(LoanPayment).filter(
        LoanPayment.date <= end_date
    ).order_by(LoanPayment.date, LoanPayment.loan_name).all()
    
    print(f"Nombre de remboursements jusqu'au {end_date}: {len(loan_payments)}")
    print()
    
    if loan_payments:
        print("Détail des remboursements par crédit:")
        capital_by_loan = {}
        total_capital = 0.0
        
        for payment in loan_payments:
            if payment.loan_name not in capital_by_loan:
                capital_by_loan[payment.loan_name] = 0.0
            capital_by_loan[payment.loan_name] += payment.capital
            total_capital += payment.capital
        
        for loan_name, capital in capital_by_loan.items():
            print(f"  {loan_name}: {capital:>12.2f} €")
        print(f"  {'TOTAL (tous crédits)':<30} | {total_capital:>12.2f} €")
        print()
        
        print("Détail chronologique:")
        for payment in loan_payments:
            print(f"  {payment.date} | {payment.loan_name:<30} | Capital: {payment.capital:>10.2f} € | Intérêt: {payment.interest:>10.2f} € | Total: {payment.total:>10.2f} €")
        print()
    else:
        print("Aucun remboursement trouvé.")
        print()
    
    # 3. Calculer le capital restant dû selon la logique actuelle (CORRIGÉE)
    print("3. CALCUL ACTUEL DU CAPITAL RESTANT DÛ (AVEC FALLBACK)")
    print("-" * 80)
    
    from backend.api.services.bilan_service import calculate_capital_restant_du
    
    # Utiliser la fonction corrigée
    remaining = calculate_capital_restant_du(db, year)
    
    # Recalculer manuellement pour afficher les détails
    credit_amount_from_transactions = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_1 == level_1_value,
            Transaction.date <= end_date
        )
    ).scalar()
    
    credit_amount = abs(credit_amount_from_transactions) if credit_amount_from_transactions is not None else 0.0
    
    # Si aucune transaction, utiliser LoanConfig
    if credit_amount == 0.0:
        from sqlalchemy import or_
        active_loans = db.query(LoanConfig).filter(
            or_(
                LoanConfig.loan_start_date.is_(None),
                LoanConfig.loan_start_date <= end_date
            )
        ).all()
        
        credit_amount_from_config = sum(loan.credit_amount for loan in active_loans)
        print(f"Crédit accordé (depuis transactions, ABS): {credit_amount:>12.2f} €")
        print(f"Crédit accordé (depuis LoanConfig, fallback): {credit_amount_from_config:>12.2f} €")
        credit_amount = credit_amount_from_config
    else:
        print(f"Crédit accordé (depuis transactions, ABS): {credit_amount:>12.2f} €")
    
    capital_paid = db.query(
        func.sum(LoanPayment.capital)
    ).filter(
        LoanPayment.date <= end_date
    ).scalar()
    
    capital_paid = capital_paid if capital_paid is not None else 0.0
    
    print(f"Capital remboursé (tous crédits):            {capital_paid:>12.2f} €")
    print(f"Capital restant dû (calculé):                {remaining:>12.2f} €")
    print(f"Capital restant dû (manuel):                 {max(0.0, credit_amount - capital_paid):>12.2f} €")
    print()
    
    # 4. Vérifier les configurations de crédit
    print("4. CONFIGURATIONS DE CRÉDIT (LoanConfig)")
    print("-" * 80)
    
    loan_configs = db.query(LoanConfig).all()
    
    if loan_configs:
        for config in loan_configs:
            print(f"  {config.name}:")
            print(f"    Montant crédit configuré: {config.credit_amount:>12.2f} €")
            print(f"    Date début: {config.loan_start_date}")
            print(f"    Date fin: {config.loan_end_date}")
            
            # Vérifier si le crédit a commencé avant la fin de l'année
            if config.loan_start_date and config.loan_start_date > end_date:
                print(f"    ⚠️  ATTENTION: Le crédit commence après le {end_date}")
            print()
    else:
        print("Aucune configuration de crédit trouvée.")
        print()
    
    # 5. Comparaison avec les transactions
    print("5. COMPARAISON")
    print("-" * 80)
    
    if loan_configs:
        total_configured = sum(config.credit_amount for config in loan_configs)
        print(f"Total crédit configuré (LoanConfig): {total_configured:>12.2f} €")
        print(f"Total crédit depuis transactions:     {credit_amount:>12.2f} €")
        diff = total_configured - credit_amount
        print(f"Différence:                            {diff:>12.2f} €")
        if abs(diff) > 0.01:
            print("  ⚠️  ATTENTION: Différence détectée!")
        print()
    
    db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyser le calcul du capital restant dû")
    parser.add_argument("year", type=int, nargs="?", default=2021, help="Année à analyser (défaut: 2021)")
    
    args = parser.parse_args()
    
    analyze_capital_restant_du(args.year)
