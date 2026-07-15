from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup, ClassificationRule
from backend.api.services.ingestion_service import ingest_transactions


def _seed_property_with_rule(db_session):
    grp = CategoryGroup(label="Produits", nature="produits")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False)
    db_session.add(cat); db_session.flush()
    prop = Property(name="Ingest-1")
    db_session.add(prop); db_session.flush()
    rule = ClassificationRule(pattern="LOYER", match_type="prefix", category_id=cat.id,
                              property_id=None, priority=0, source="manual", strict_ratio=False)
    db_session.add(rule); db_session.flush()
    return prop, cat


def test_ingest_inserts_and_classifies(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    res = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert res["inserted"] == 1
    assert res["deduplicated"] == 0
    tx = db_session.query(Transaction).filter(Transaction.property_id == prop.id).one()
    assert tx.category_id == cat.id          # classé par la règle
    assert tx.source == "csv"
    assert tx.solde == 390.0                  # solde recalculé


def test_ingest_dedup_fallback_key(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    ingest_transactions(db_session, prop.id, None, rows, "csv")
    res2 = ingest_transactions(db_session, prop.id, None, rows, "csv")   # même ligne
    assert res2["inserted"] == 0
    assert res2["deduplicated"] == 1
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 1


def test_ingest_dedup_external_id(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 2, 1), "quantite": 100.0, "nom": "VIR", "external_id": "EB-123"}]
    ingest_transactions(db_session, prop.id, None, rows, "api")
    # même external_id, nom/montant différents → toujours un doublon
    rows2 = [{"date": date(2023, 2, 2), "quantite": 999.0, "nom": "AUTRE", "external_id": "EB-123"}]
    res = ingest_transactions(db_session, prop.id, None, rows2, "api")
    assert res["inserted"] == 0 and res["deduplicated"] == 1
