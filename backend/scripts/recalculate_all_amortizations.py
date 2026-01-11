#!/usr/bin/env python3
"""
Script pour forcer le recalcul complet de tous les amortissements.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.api.services.amortization_service import recalculate_all_amortizations

init_database()
db = SessionLocal()

print('🔄 Recalcul complet de tous les amortissements...')
count = recalculate_all_amortizations(db)
print(f'✅ {count} AmortizationResult créés/mis à jour')

db.close()

