#!/usr/bin/env python3
"""
Script pour vérifier le type de la catégorie "toto" en base de données.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import CompteResultatMapping

def main():
    db = SessionLocal()
    try:
        mapping = db.query(CompteResultatMapping).filter(CompteResultatMapping.category_name == 'toto').first()
        if mapping:
            print(f'Catégorie: {mapping.category_name}')
            print(f'Type en BDD: {repr(mapping.type)}')
            print(f'ID: {mapping.id}')
            print(f'Created at: {mapping.created_at}')
            print(f'Updated at: {mapping.updated_at}')
        else:
            print('Mapping "toto" non trouvé')
    finally:
        db.close()

if __name__ == "__main__":
    main()
