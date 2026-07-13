import datetime
from backend.database.models import Category, CategoryGroup, Property, Transaction, ClassificationRule


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.commit()
    return c.id


def test_create_and_list_rule(client, db_session):
    cat_id = _seed(db_session)
    r = client.post("/api/rules", json={"pattern": "VIR LOYER", "match_type": "prefix",
                                        "category_id": cat_id, "property_id": 25, "priority": 0})
    assert r.status_code == 201, r.text
    lst = client.get("/api/rules", params={"property_id": 25}).json()
    assert any(x["pattern"] == "VIR LOYER" for x in lst["items"])


def test_preview_counts_unclassified_and_conflicts(client, db_session):
    cat_id = _seed(db_session)
    other = Category(label="Autre", group_id=db_session.query(CategoryGroup).first().id)
    db_session.add(other); db_session.flush()
    db_session.add_all([
        Transaction(property_id=25, date=datetime.date(2025, 1, 1), quantite=500.0,
                    nom="VIR LOYER A", solde=0.0, category_id=None),
        Transaction(property_id=25, date=datetime.date(2025, 2, 1), quantite=500.0,
                    nom="VIR LOYER B", solde=0.0, category_id=other.id),
    ]); db_session.commit()
    r = client.post("/api/rules/preview", json={"pattern": "VIR LOYER", "match_type": "prefix",
                                                "category_id": cat_id, "property_id": 25})
    body = r.json()
    assert body["would_classify"] == 1        # la non classée
    assert len(body["conflicts"]) == 1        # celle classée "Autre"
