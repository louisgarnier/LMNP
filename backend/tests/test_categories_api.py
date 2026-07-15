from backend.database.models import Category, CategoryGroup


def _seed(db):
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    db.add(Category(label="Encaissement locataire et CAF", group_id=g.id)); db.commit()


def test_list_categories(client, db_session):
    _seed(db_session)
    body = client.get("/api/categories").json()
    assert any(c["label"] == "Encaissement locataire et CAF"
               and c["group_label"] == "Produits" and c["nature"] == "produits"
               for c in body["items"])
