#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi 'Immobilisation Facade/Toiture' 
n'a pas de AmortizationResult en base.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType, Transaction, EnrichedTransaction, AmortizationResult
import json
from sqlalchemy import and_

init_database()
db = SessionLocal()

# Trouver le type 'Immobilisation Facade/Toiture'
atype = db.query(AmortizationType).filter(AmortizationType.name == 'Immobilisation Facade/Toiture').first()
if atype:
    print(f'Type trouvé: {atype.name} (ID: {atype.id})')
    print(f'Level 2: {atype.level_2_value}')
    level_1_values = json.loads(atype.level_1_values or '[]')
    print(f'Level 1 values: {level_1_values}')
    print(f'Duration: {atype.duration}')
    
    # Trouver les transactions correspondantes
    if level_1_values:
        transactions = db.query(Transaction).join(
            EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                EnrichedTransaction.level_2 == atype.level_2_value,
                EnrichedTransaction.level_1.in_(level_1_values)
            )
        ).all()
        print(f'\nNombre de transactions trouvées: {len(transactions)}')
        for t in transactions:
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == t.id
            ).first()
            print(f'  - Transaction {t.id}: {t.date}, {t.quantite} €, {t.nom}')
            print(f'    Enriched: level_1={enriched.level_1 if enriched else "N/A"}, level_2={enriched.level_2 if enriched else "N/A"}')
            
            # Vérifier si des AmortizationResult existent pour cette transaction
            results = db.query(AmortizationResult).filter(
                AmortizationResult.transaction_id == t.id
            ).all()
            print(f'    AmortizationResult pour cette transaction: {len(results)}')
    
    # Compter les AmortizationResult pour ce type
    results = db.query(AmortizationResult).filter(
        AmortizationResult.category == atype.name
    ).all()
    print(f'\nNombre total de AmortizationResult en base pour ce type: {len(results)}')
    
    # Tester le recalcul pour chaque transaction
    if level_1_values and transactions:
        print('\n🧪 Test du recalcul pour chaque transaction:')
        from backend.api.services.amortization_service import recalculate_transaction_amortization
        for t in transactions:
            print(f'\n  Transaction {t.id}:')
            count = recalculate_transaction_amortization(db, t.id)
            print(f'    → {count} AmortizationResult créés')
        
        # Vérifier après recalcul
        results_after = db.query(AmortizationResult).filter(
            AmortizationResult.category == atype.name
        ).all()
        print(f'\nNombre total de AmortizationResult après recalcul: {len(results_after)}')
else:
    print('Type non trouvé')

db.close()

