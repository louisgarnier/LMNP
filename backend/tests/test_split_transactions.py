from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup


def _seed(db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="Split"); db_session.add(prop); db_session.flush()
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 5), quantite=280.0,
                         nom="MATERA", solde=280.0, source="csv", is_split_parent=False, category_id=cat.id)
    db_session.add(parent); db_session.commit()
    return prop, cat, parent


def test_split_replaces_parent_with_children(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 450.0, "nom": "loyer", "category_id": cat.id},
        {"quantite": -170.0, "nom": "frais agence", "category_id": cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    db_session.refresh(parent)
    assert parent.is_split_parent is True
    assert parent.category_id is None            # masquée → hors CR/bilan
    children = db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).all()
    assert len(children) == 2
    assert sum(c.quantite for c in children) == 280.0


def test_split_rejects_wrong_sum(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 100.0, "nom": "x", "category_id": None},
    ]})
    assert resp.status_code == 400
    db_session.refresh(parent)
    assert parent.is_split_parent is False       # rien n'a changé
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0


def test_undo_split_restores_parent(client, db_session):
    prop, cat, parent = _seed(db_session)
    client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 280.0, "nom": "tout", "category_id": cat.id},
    ]})
    resp = client.delete(f"/api/transactions/{parent.id}/split")
    assert resp.status_code == 200
    db_session.refresh(parent)
    assert parent.is_split_parent is False
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0
