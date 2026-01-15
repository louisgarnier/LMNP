"""Vérifier les level_3 configurés."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from backend.database.connection import SessionLocal
from backend.api.services.compte_resultat_service import get_level_3_values
db = SessionLocal()
level_3 = get_level_3_values(db)
print('Level 3 configurés:', level_3)
print('Nombre:', len(level_3))
db.close()
