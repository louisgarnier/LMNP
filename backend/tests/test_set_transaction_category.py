"""Cutover Task C1 (étape 3) : PATCH /api/transactions/{id}/category.

Endpoint minimal, référentiel-based : fixe directement transactions.category_id
(nouvelle classification par référentiel), sans passer par le moteur
d'enrichissement legacy (enrichment_service) ni les tables mapping. Remplace
enrichmentAPI.updateClassifications pour la reclassification manuelle depuis
le tableau principal des transactions.
"""
from datetime import date


def _seed_property_and_category(db, label="Encaissement locataire et CAF",
                                  group_label="Produits", nature="produits"):
    from backend.database.models import Property, CategoryGroup, Category

    p = Property(name="T"); db.add(p); db.flush()
    g = CategoryGroup(label=group_label, nature=nature); db.add(g); db.flush()
    c = Category(label=label, group_id=g.id); db.add(c); db.flush()
    return p, c


def test_set_category_updates(client, db_session):
    from backend.database.models import Transaction

    p, cat = _seed_property_and_category(db_session)
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                     solde=500.0, property_id=p.id)
    db_session.add(t); db_session.flush(); db_session.commit()

    response = client.patch(
        f"/api/transactions/{t.id}/category", json={"category_id": cat.id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"id": t.id, "category_id": cat.id}
    assert db_session.get(Transaction, t.id).category_id == cat.id


def test_set_null_unclassifies(client, db_session):
    from backend.database.models import Transaction

    p, cat = _seed_property_and_category(db_session)
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                     solde=500.0, property_id=p.id, category_id=cat.id)
    db_session.add(t); db_session.flush(); db_session.commit()

    response = client.patch(
        f"/api/transactions/{t.id}/category", json={"category_id": None}
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"id": t.id, "category_id": None}
    assert db_session.get(Transaction, t.id).category_id is None


def test_unknown_category_400(client, db_session):
    from backend.database.models import Transaction

    p, _cat = _seed_property_and_category(db_session)
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                     solde=500.0, property_id=p.id)
    db_session.add(t); db_session.flush(); db_session.commit()

    response = client.patch(
        f"/api/transactions/{t.id}/category", json={"category_id": 999999}
    )

    assert response.status_code == 400
    assert db_session.get(Transaction, t.id).category_id is None


def test_unknown_transaction_404(client, db_session):
    response = client.patch(
        "/api/transactions/999999/category", json={"category_id": None}
    )

    assert response.status_code == 404
