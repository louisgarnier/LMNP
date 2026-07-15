import io
from datetime import date
from backend.database.models import Property, Transaction
from backend.api.services.ingestion_service import ingest_transactions


def test_reimport_same_rows_is_idempotent(db_session):
    prop = Property(name="Reimport")
    db_session.add(prop); db_session.flush()
    rows = [
        {"date": date(2023, 1, 1), "quantite": 100.0, "nom": "A", "external_id": None},
        {"date": date(2023, 1, 2), "quantite": -50.0, "nom": "B", "external_id": None},
    ]
    r1 = ingest_transactions(db_session, prop.id, None, rows, "csv")
    r2 = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert r1["inserted"] == 2
    assert r2["inserted"] == 0 and r2["deduplicated"] == 2
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 2
