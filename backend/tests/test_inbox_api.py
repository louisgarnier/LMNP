import datetime
from backend.database.models import Category, CategoryGroup, Property, Transaction, ClassificationRule


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.commit()
    return c.id


def test_inbox_lists_unclassified_with_proposed_rule(client, db_session):
    _seed(db_session)
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0,
                               category_id=None)); db_session.commit()
    body = client.get("/api/inbox", params={"property_id": 25}).json()
    assert len(body["items"]) == 1
    it = body["items"][0]
    assert it["proposed_rule"]["pattern"] == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert it["proposed_rule"]["match_type"] == "prefix"


def test_validate_creates_rule_and_classifies(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                     nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={
        "transaction_id": tx.id, "category_id": cat_id,
        "rule": {"pattern": "VIR AIRBNB PAYMENTS LUXEMBOU", "match_type": "prefix", "property_id": 25}})
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    rule = db_session.query(ClassificationRule).filter_by(pattern="VIR AIRBNB PAYMENTS LUXEMBOU").one()
    assert rule.source == "auto_from_inbox"


def test_validate_just_this_one_no_rule(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR UNIQUE 123", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={"transaction_id": tx.id, "category_id": cat_id})
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    assert db_session.query(ClassificationRule).count() == 0
