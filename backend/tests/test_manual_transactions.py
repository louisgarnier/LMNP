from datetime import date
from backend.database.models import Property, Category, CategoryGroup, Transaction


def test_manual_create_with_category(client, db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="Manual"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/manual", json={
        "property_id": prop.id, "date": "2023-03-01", "quantite": 390.0,
        "nom": "Loyer manuel", "category_id": cat.id,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    tx = db_session.query(Transaction).get(body["id"])
    assert tx.source == "manual"
    assert tx.category_id == cat.id
    assert tx.quantite == 390.0


def test_manual_create_without_category_goes_unclassified(client, db_session):
    prop = Property(name="Manual2"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/manual", json={
        "property_id": prop.id, "date": "2023-03-02", "quantite": -50.0,
        "nom": "Inconnu", "category_id": None,
    })
    assert resp.status_code == 200
    tx = db_session.query(Transaction).get(resp.json()["id"])
    assert tx.category_id is None   # → apparaîtra dans l'inbox
