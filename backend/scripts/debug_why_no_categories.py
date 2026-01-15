"""Debug pourquoi le backend ne calcule plus de catégories normales."""
import sys
import json
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_produits_exploitation,
    calculate_charges_exploitation
)

db = SessionLocal()

try:
    mappings = get_mappings(db)
    level_3_values = get_level_3_values(db)
    year = 2023
    
    print(f"Level 3 configurés: {level_3_values}")
    print(f"Nombre de mappings: {len(mappings)}")
    print()
    
    # Vérifier les mappings de produits
    produits_mappings = [m for m in mappings if m.type == "Produits d'exploitation"]
    print(f"Mappings Produits: {len(produits_mappings)}")
    for m in produits_mappings:
        level_1_values = json.loads(m.level_1_values) if m.level_1_values else []
        print(f"  - {m.category_name}: {len(level_1_values)} level_1_values")
        if level_1_values:
            print(f"    Values: {level_1_values}")
    print()
    
    # Vérifier les mappings de charges
    charges_mappings = [m for m in mappings if m.type == "Charges d'exploitation"]
    print(f"Mappings Charges: {len(charges_mappings)}")
    for m in charges_mappings:
        level_1_values = json.loads(m.level_1_values) if m.level_1_values else []
        print(f"  - {m.category_name}: {len(level_1_values)} level_1_values")
        if level_1_values:
            print(f"    Values: {level_1_values}")
    print()
    
    # Vérifier les transactions
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    query = db.query(
        EnrichedTransaction.level_1,
        EnrichedTransaction.level_3,
        Transaction.quantite
    ).join(
        Transaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            EnrichedTransaction.level_1.isnot(None)
        )
    )
    
    transactions = query.all()
    print(f"Transactions filtrées pour {year}: {len(transactions)}")
    print(f"Level_1 uniques: {set(t[0] for t in transactions)}")
    print(f"Level_3 uniques: {set(t[1] for t in transactions)}")
    print()
    
    # Tester le calcul
    produits = calculate_produits_exploitation(db, year, mappings, level_3_values)
    charges = calculate_charges_exploitation(db, year, mappings, level_3_values)
    
    print(f"Produits calculés: {len(produits)} catégories")
    for cat, amount in produits.items():
        print(f"  - {cat}: {amount:,.2f} €")
    print()
    
    print(f"Charges calculées: {len(charges)} catégories")
    for cat, amount in charges.items():
        print(f"  - {cat}: {amount:,.2f} €")
    
finally:
    db.close()
