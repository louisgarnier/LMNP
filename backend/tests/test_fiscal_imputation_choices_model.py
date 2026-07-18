"""La table des choix d'imputation stocke un mode unique par année."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, FiscalImputationChoice


def test_year_unique_et_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    db = S()
    db.add(FiscalImputationChoice(year=2023, mode="amort"))
    db.commit()
    got = db.query(FiscalImputationChoice).filter_by(year=2023).one()
    assert got.mode == "amort"
    db.close()
