"""
Test de non-régression (correctif revue étape 4) : `TransactionResponse` doit
exposer `parent_transaction_id`, `is_split_parent` et `source`, sinon le
frontend ne peut pas savoir qu'une ligne visible est un enfant d'éclatement
ni retrouver l'id de la parente pour proposer « défaire l'éclatement ».

⚠️ Avant de modifier ce fichier, lire : ../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup


def _seed(db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="SplitFields"); db_session.add(prop); db_session.flush()
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 5), quantite=280.0,
                         nom="MATERA", solde=280.0, source="csv", is_split_parent=False, category_id=cat.id)
    db_session.add(parent); db_session.commit()
    return prop, cat, parent


def test_transaction_list_exposes_split_fields_on_children(client, db_session):
    prop, cat, parent = _seed(db_session)

    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 450.0, "nom": "loyer", "category_id": cat.id},
        {"quantite": -170.0, "nom": "frais agence", "category_id": cat.id},
    ]})
    assert resp.status_code == 200, resp.text

    resp = client.get("/api/transactions", params={"property_id": prop.id})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # La parente éclatée reste masquée de la liste (comportement existant).
    ids = [t["id"] for t in body["transactions"]]
    assert parent.id not in ids

    # Les enfants sont bien renvoyés, avec les nouveaux champs.
    children = [t for t in body["transactions"] if t.get("parent_transaction_id") == parent.id]
    assert len(children) == 2
    for child in children:
        assert child["parent_transaction_id"] == parent.id
        assert child["source"] == "manual"
        assert child["is_split_parent"] is False


def test_transaction_detail_exposes_split_fields(client, db_session):
    prop, cat, parent = _seed(db_session)

    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 280.0, "nom": "tout", "category_id": cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    child_id = resp.json()["child_ids"][0]

    resp = client.get(f"/api/transactions/{child_id}", params={"property_id": prop.id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["parent_transaction_id"] == parent.id
    assert body["source"] == "manual"
    assert body["is_split_parent"] is False
