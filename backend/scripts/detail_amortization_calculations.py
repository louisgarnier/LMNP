"""
Script détaillé des calculs d'amortissement pour chaque transaction et chaque année

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta

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
    calculate_yearly_amounts,
    calculate_30_360_days
)
import json

def detail_amortization_calculations():
    """Détaille les calculs d'amortissement pour chaque transaction"""
    db = next(get_db())
    
    print("=" * 120)
    print("DÉTAIL DES CALCULS D'AMORTISSEMENT - CHAQUE TRANSACTION, CHAQUE ANNÉE")
    print("=" * 120)
    print()
    
    # Récupérer toutes les transactions avec amortissements
    transactions_with_amort = db.query(Transaction).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).join(
        AmortizationType, 
        AmortizationType.level_2_value == EnrichedTransaction.level_2
    ).filter(
        AmortizationType.duration > 0
    ).distinct().order_by(Transaction.id).all()
    
    print(f"Nombre de transactions avec amortissements: {len(transactions_with_amort)}")
    print()
    
    for transaction in transactions_with_amort:
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
        
        # Déterminer la date de début
        transaction_date = transaction.date
        type_start_date = matching_type.start_date
        used_start_date = type_start_date if type_start_date else transaction_date
        
        # Calculer l'annuité
        if matching_type.annual_amount and matching_type.annual_amount != 0:
            annual_amount = abs(matching_type.annual_amount)
            annual_source = "Configurée dans le type"
        else:
            annual_amount = abs(transaction.quantite) / matching_type.duration if matching_type.duration > 0 else 0
            annual_source = "Calculée (montant / durée)"
        
        # Calculer théoriquement
        theoretical_amounts = calculate_yearly_amounts(
            start_date=used_start_date,
            total_amount=transaction.quantite,
            duration=matching_type.duration,
            annual_amount=matching_type.annual_amount
        )
        
        # Récupérer les résultats en base
        db_results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).order_by(AmortizationResult.year).all()
        
        print("=" * 120)
        print(f"TRANSACTION #{transaction.id}: {transaction.nom}")
        print("=" * 120)
        print()
        
        print("📋 INFORMATIONS DE BASE:")
        print(f"  - Date transaction: {transaction_date}")
        print(f"  - Date début type (override): {type_start_date or 'Aucune (NULL)'}")
        print(f"  - Date début utilisée: {used_start_date} {'(OVERRIDE)' if type_start_date else '(date transaction)'}")
        print(f"  - Montant transaction: {transaction.quantite:.2f} €")
        print(f"  - Montant absolu: {abs(transaction.quantite):.2f} €")
        print(f"  - Type: {matching_type.name}")
        print(f"  - Durée: {matching_type.duration} ans")
        print(f"  - Annuité: {annual_amount:.2f} € ({annual_source})")
        print()
        
        # Calculer les années
        start_year = used_start_date.year
        exact_end_date = used_start_date + relativedelta(years=int(matching_type.duration))
        end_year = exact_end_date.year
        
        print("📊 CALCUL DÉTAILLÉ ANNÉE PAR ANNÉE:")
        print()
        
        # Première année (année partielle)
        if start_year == end_year:
            # Cas spécial : tout dans une année
            first_year_end = end_date
            days_first = calculate_30_360_days(used_start_date, first_year_end)
            daily_amount = annual_amount / 360
            first_year_amount = daily_amount * days_first
            print(f"  ANNÉE {start_year} (année unique):")
            print(f"    - Date début: {used_start_date}")
            print(f"    - Date fin: {first_year_end}")
            print(f"    - Jours (30/360): {days_first} jours")
            print(f"    - Montant journalier: {daily_amount:.4f} €/jour")
            print(f"    - Montant calculé: {first_year_amount:.2f} €")
            print(f"    - Montant théorique: {abs(theoretical_amounts.get(start_year, 0)):.2f} €")
            if db_results:
                db_amount = abs(next((r.amount for r in db_results if r.year == start_year), 0))
                print(f"    - Montant en base: {db_amount:.2f} €")
                if abs(first_year_amount - db_amount) > 0.01:
                    print(f"    ⚠️  DIFFÉRENCE: {abs(first_year_amount - db_amount):.2f} €")
            print()
        else:
            # Première année partielle
            first_year_end = date(start_year, 12, 31)
            days_first = calculate_30_360_days(used_start_date, first_year_end)
            daily_amount = annual_amount / 360
            first_year_amount = daily_amount * days_first
            print(f"  ANNÉE {start_year} (année d'achat - PARTIELLE):")
            print(f"    - Date début: {used_start_date}")
            print(f"    - Date fin: {first_year_end}")
            print(f"    - Jours (30/360): {days_first} jours")
            print(f"    - Montant journalier: {annual_amount:.2f} € / 360 = {daily_amount:.4f} €/jour")
            print(f"    - Montant calculé: {days_first} × {daily_amount:.4f} = {first_year_amount:.2f} €")
            print(f"    - Montant théorique: {abs(theoretical_amounts.get(start_year, 0)):.2f} €")
            if db_results:
                db_amount = abs(next((r.amount for r in db_results if r.year == start_year), 0))
                print(f"    - Montant en base: {db_amount:.2f} €")
                if abs(first_year_amount - db_amount) > 0.01:
                    print(f"    ⚠️  DIFFÉRENCE: {abs(first_year_amount - db_amount):.2f} €")
            print()
            
            # Années complètes
            full_years = list(range(start_year + 1, end_year))
            if full_years:
                print(f"  ANNÉES COMPLÈTES ({len(full_years)} années): {full_years[0]} à {full_years[-1]}")
                print(f"    - Annuité attendue: {annual_amount:.2f} € par année")
                for year in full_years:
                    theoretical = abs(theoretical_amounts.get(year, 0))
                    if db_results:
                        db_amount = abs(next((r.amount for r in db_results if r.year == year), 0))
                        status = "✓" if abs(theoretical - db_amount) <= 0.01 else "⚠️"
                        diff = abs(theoretical - db_amount)
                        print(f"    - {year}: théorique={theoretical:.2f} €, base={db_amount:.2f} € {status}", end="")
                        if diff > 0.01:
                            print(f" (diff={diff:.2f} €)")
                        else:
                            print()
                    else:
                        print(f"    - {year}: théorique={theoretical:.2f} €, base=ABSENT")
                print()
            
            # Dernière année (partielle)
            last_year_start = date(end_year, 1, 1)
            days_last = calculate_30_360_days(last_year_start, exact_end_date)
            last_year_amount_calc = (annual_amount / 360) * days_last
            
            # Calculer le total avant dernière année
            total_before_last = first_year_amount + (annual_amount * len(full_years))
            last_year_amount_remaining = abs(transaction.quantite) - total_before_last
            
            print(f"  ANNÉE {end_year} (dernière année - PARTIELLE):")
            print(f"    - Date début: {last_year_start}")
            print(f"    - Date fin exacte: {exact_end_date} (start_date + {matching_type.duration} ans)")
            print(f"    - Jours (30/360): {days_last} jours")
            print(f"    - Montant journalier: {annual_amount:.2f} € / 360 = {daily_amount:.4f} €/jour")
            print(f"    - Montant calculé (30/360): {days_last} × {daily_amount:.4f} = {last_year_amount_calc:.2f} €")
            print(f"    - Total avant dernière année: {total_before_last:.2f} €")
            print(f"    - Solde restant: {abs(transaction.quantite):.2f} - {total_before_last:.2f} = {last_year_amount_remaining:.2f} €")
            print(f"    - Montant théorique: {abs(theoretical_amounts.get(end_year, 0)):.2f} €")
            if db_results:
                db_amount = abs(next((r.amount for r in db_results if r.year == end_year), 0))
                print(f"    - Montant en base: {db_amount:.2f} €")
                if abs(last_year_amount_calc - db_amount) > 0.01:
                    print(f"    ⚠️  DIFFÉRENCE: {abs(last_year_amount_calc - db_amount):.2f} €")
            print()
        
        # Résumé
        print("📈 RÉSUMÉ:")
        total_theoretical = sum(abs(v) for v in theoretical_amounts.values())
        total_db = sum(abs(r.amount) for r in db_results) if db_results else 0
        total_expected = abs(transaction.quantite)
        
        print(f"  - Total théorique: {total_theoretical:.2f} €")
        print(f"  - Total en base: {total_db:.2f} €")
        print(f"  - Total attendu: {total_expected:.2f} €")
        print(f"  - Différence théorique vs attendu: {abs(total_theoretical - total_expected):.2f} €")
        print(f"  - Différence base vs attendu: {abs(total_db - total_expected):.2f} €")
        print()
        print()
    
    db.close()


if __name__ == "__main__":
    detail_amortization_calculations()
