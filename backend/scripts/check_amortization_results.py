#!/usr/bin/env python3
"""
Script pour vérifier les AmortizationResult en base de données.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationResult
from datetime import date
from collections import defaultdict

init_database()
db = SessionLocal()

today = date.today()
print(f"📅 Année actuelle: {today.year}")
print()

# Récupérer tous les résultats jusqu'à l'année en cours
all_results = db.query(AmortizationResult).all()
filtered_results = db.query(AmortizationResult).filter(AmortizationResult.year <= today.year).all()

print(f"📊 Total de résultats en base (toutes années): {len(all_results)}")
print(f"📊 Total de résultats jusqu'à {today.year}: {len(filtered_results)}")
print()

# Grouper par catégorie
categories_all = defaultdict(float)
categories_filtered = defaultdict(float)

for r in all_results:
    categories_all[r.category] += r.amount

for r in filtered_results:
    categories_filtered[r.category] += r.amount

print("Catégories dans AmortizationResult (toutes années):")
for cat in sorted(categories_all.keys()):
    print(f"  - {cat}: {categories_all[cat]:,.2f} € ({len([r for r in all_results if r.category == cat])} résultats)")

print()
print(f"Catégories dans AmortizationResult (jusqu'à {today.year}):")
for cat in sorted(categories_filtered.keys()):
    print(f"  - {cat}: {categories_filtered[cat]:,.2f} € ({len([r for r in filtered_results if r.category == cat])} résultats)")

# Vérifier spécifiquement "Immobilisation Facade/Toiture"
facade_results = db.query(AmortizationResult).filter(
    AmortizationResult.category == "Immobilisation Facade/Toiture"
).all()
print()
print(f"🔍 Résultats pour 'Immobilisation Facade/Toiture': {len(facade_results)}")
if facade_results:
    years = sorted(set(r.year for r in facade_results))
    print(f"  Années: {min(years)} - {max(years)}")
    total = sum(r.amount for r in facade_results)
    print(f"  Total: {total:,.2f} €")
    filtered_facade = [r for r in facade_results if r.year <= today.year]
    if filtered_facade:
        total_filtered = sum(r.amount for r in filtered_facade)
        print(f"  Total (jusqu'à {today.year}): {total_filtered:,.2f} €")
    else:
        print(f"  ⚠️ Aucun résultat jusqu'à {today.year}")

db.close()

