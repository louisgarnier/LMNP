#!/usr/bin/env python3
"""
Script pour comparer le calcul dynamique et les résultats stockés.
"""

import sys
from pathlib import Path
import json
from datetime import date
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType, Transaction, EnrichedTransaction, AmortizationResult
from backend.api.services.amortization_service import calculate_yearly_amounts
from sqlalchemy import and_

init_database()
db = SessionLocal()

today = date.today()

# Trouver le type "Immobilisation Facade/Toiture"
atype = db.query(AmortizationType).filter(
    AmortizationType.name == "Immobilisation Facade/Toiture"
).first()

if not atype:
    print("Type non trouvé")
    db.close()
    exit(1)

print("=" * 60)
print(f"Comparaison pour: {atype.name}")
print("=" * 60)
print()

level_1_values = json.loads(atype.level_1_values or "[]")
print(f"Level 1 values: {level_1_values}")
print(f"Duration: {atype.duration} ans")
print()

# Récupérer toutes les transactions correspondantes
transactions = db.query(Transaction).join(
    EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
).filter(
    and_(
        EnrichedTransaction.level_2 == atype.level_2_value,
        EnrichedTransaction.level_1.in_(level_1_values)
    )
).all()

print(f"📊 Nombre de transactions trouvées: {len(transactions)}")
print()

# CALCUL DYNAMIQUE (comme check_amortization_state.py)
print("=" * 60)
print("CALCUL DYNAMIQUE (comme check_amortization_state.py)")
print("=" * 60)

cumulated_dynamic = 0.0
annual_amount = atype.annual_amount if atype.annual_amount is not None and atype.annual_amount != 0 else None

for transaction in transactions:
    start_date = atype.start_date if atype.start_date else transaction.date
    
    if start_date > today:
        continue
    
    transaction_amount = abs(transaction.quantite)
    
    if annual_amount is None:
        transaction_annual_amount = transaction_amount / atype.duration
    else:
        transaction_annual_amount = annual_amount
    
    yearly_amounts = calculate_yearly_amounts(
        start_date=start_date,
        total_amount=-transaction_amount,
        duration=atype.duration,
        annual_amount=transaction_annual_amount
    )
    
    transaction_cumulated = 0.0
    for year, yearly_amount in yearly_amounts.items():
        if year <= today.year:
            transaction_cumulated += abs(yearly_amount)
    
    cumulated_dynamic += transaction_cumulated
    print(f"Transaction {transaction.id} ({transaction.date}): {transaction_cumulated:,.2f} €")

print()
print(f"TOTAL CALCUL DYNAMIQUE: {cumulated_dynamic:,.2f} €")
print()

# RÉSULTATS STOCKÉS (comme display_amortization_table.py)
print("=" * 60)
print("RÉSULTATS STOCKÉS (comme display_amortization_table.py)")
print("=" * 60)

results = db.query(AmortizationResult).filter(
    AmortizationResult.category == atype.name,
    AmortizationResult.year <= today.year
).order_by(AmortizationResult.year).all()

print(f"📊 Nombre de résultats stockés (jusqu'à {today.year}): {len(results)}")
print()

# Grouper par année
by_year = defaultdict(float)
for r in results:
    by_year[r.year] += r.amount

for year in sorted(by_year.keys()):
    print(f"Année {year}: {by_year[year]:,.2f} €")

cumulated_stored = sum(r.amount for r in results)
print()
print(f"TOTAL RÉSULTATS STOCKÉS: {abs(cumulated_stored):,.2f} €")
print()

# COMPARAISON
print("=" * 60)
print("COMPARAISON")
print("=" * 60)
print(f"Calcul dynamique: {cumulated_dynamic:,.2f} €")
print(f"Résultats stockés: {abs(cumulated_stored):,.2f} €")
print(f"Différence: {abs(cumulated_dynamic - abs(cumulated_stored)):,.2f} €")

if abs(cumulated_dynamic - abs(cumulated_stored)) > 0.01:
    print()
    print("⚠️ INCOHÉRENCE DÉTECTÉE !")
    print()
    print("Vérification des transactions sans AmortizationResult:")
    transaction_ids_with_results = set(r.transaction_id for r in results)
    for transaction in transactions:
        if transaction.id not in transaction_ids_with_results:
            print(f"  - Transaction {transaction.id} ({transaction.date}): PAS de résultats stockés")
else:
    print()
    print("✅ Les deux calculs sont identiques !")

db.close()

