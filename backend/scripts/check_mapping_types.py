"""Vérifier les types des mappings."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from backend.database.connection import SessionLocal
from backend.database.models import CompteResultatMapping
db = SessionLocal()
mappings = db.query(CompteResultatMapping).all()
for m in mappings:
    print(f'{m.category_name}: type={repr(m.type)}')
db.close()
