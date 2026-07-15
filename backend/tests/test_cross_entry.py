from backend.database.models import Property, Transaction, Category, CategoryGroup


def test_cross_entry_nets_to_zero(client, db_session):
    g1 = CategoryGroup(label="Frais d'acquisition", nature="charges_deductibles"); db_session.add(g1); db_session.flush()
    c_notaire = Category(label="Frais de notaire", group_id=g1.id, is_custom=False); db_session.add(c_notaire)
    g2 = CategoryGroup(label="Compte courant d'associé", nature="passif"); db_session.add(g2); db_session.flush()
    c_cc = Category(label="Compte courant d'associé", group_id=g2.id, is_custom=False); db_session.add(c_cc)
    prop = Property(name="Cross"); db_session.add(prop); db_session.commit()
    resp = client.post("/api/transactions/cross-entry", json={
        "property_id": prop.id, "date": "2023-04-01", "montant": 15000.0,
        "debit": {"nom": "Frais de notaire", "category_id": c_notaire.id},
        "credit": {"nom": "Apport compte courant", "category_id": c_cc.id},
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    debit = db_session.query(Transaction).get(body["debit_id"])
    credit = db_session.query(Transaction).get(body["credit_id"])
    assert debit.quantite == -15000.0 and credit.quantite == 15000.0
    assert debit.quantite + credit.quantite == 0.0
    assert debit.source == "manual" and credit.source == "manual"
