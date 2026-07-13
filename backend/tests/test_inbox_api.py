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


def test_validate_all_groups_same_pattern_exact_and_prefix(client, db_session):
    cat_id = _seed(db_session)
    # règle existante qui suggère la même catégorie pour les deux transactions,
    # même si leurs motifs dérivés (exact vs prefix) diffèrent.
    db_session.add(ClassificationRule(pattern="VIR AIRBNB PAYMENTS LUXEMBOU", match_type="prefix",
                                      category_id=cat_id, property_id=None, priority=0,
                                      source="seed"))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=100.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU", solde=0.0, category_id=None))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 29), quantite=200.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0,
                               category_id=None))
    db_session.commit()

    r = client.post("/api/inbox/validate-all", params={"property_id": 25})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rules_created"] == 1
    assert body["transactions_validated"] == 2

    db_session.expire_all()
    new_rules = (db_session.query(ClassificationRule)
                 .filter_by(source="auto_from_inbox", pattern="VIR AIRBNB PAYMENTS LUXEMBOU").all())
    assert len(new_rules) == 1
    assert new_rules[0].match_type == "prefix"

    txs = db_session.query(Transaction).filter(Transaction.property_id == 25).all()
    assert len(txs) == 2
    assert all(t.category_id == cat_id for t in txs)


def test_validate_all_skips_none_suggestion(client, db_session):
    _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR SANS AUCUNE REGLE 999", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()

    r = client.post("/api/inbox/validate-all", params={"property_id": 25})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rules_created"] == 0
    assert body["transactions_validated"] == 0

    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id is None
    assert db_session.query(ClassificationRule).filter_by(source="auto_from_inbox").count() == 0


def test_suggestion_prefix_requires_startswith(client, db_session):
    cat_id = _seed(db_session)
    # le motif du prefix-rule apparaît au milieu du libellé, pas au début :
    # une suggestion "prefix" ne doit pas se rabattre sur un simple "contains".
    db_session.add(ClassificationRule(pattern="AIRBNB PAYMENTS", match_type="prefix",
                                      category_id=cat_id, property_id=None, priority=0,
                                      source="seed"))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=50.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU", solde=0.0, category_id=None))
    db_session.commit()

    body = client.get("/api/inbox", params={"property_id": 25}).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["suggestion"]["category_id"] is None
