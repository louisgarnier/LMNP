"""
Le TCD (`GET /api/analytics/pivot`) ne doit pas compter en double une ligne
parente éclatée (`is_split_parent=True`, `category_id=None`) : elle est
remplacée par ses enfants (déjà classés) et doit donc être exclue de
l'agrégation `func.sum(Transaction.quantite)`, exactement comme le solde
(`balance_utils.py`), `GET /transactions` et l'inbox l'excluent déjà.

⚠️ Avant de modifier ce fichier, lire : ../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import date
from backend.database.models import Property, Transaction


def _seed(db_session):
    prop = Property(name="PivotExcl")
    db_session.add(prop)
    db_session.flush()

    # parente masquée (ne doit PAS compter), remplacée par ses 2 enfants
    parent = Transaction(
        property_id=prop.id, date=date(2023, 1, 1), quantite=280.0, nom="MATERA",
        solde=0.0, source="csv", is_split_parent=True, category_id=None,
    )
    c1 = Transaction(
        property_id=prop.id, date=date(2023, 1, 1), quantite=450.0, nom="loyer",
        solde=0.0, source="manual", is_split_parent=False,
    )
    c2 = Transaction(
        property_id=prop.id, date=date(2023, 1, 1), quantite=-170.0, nom="agence",
        solde=0.0, source="manual", is_split_parent=False,
    )
    db_session.add_all([parent, c1, c2])
    db_session.flush()
    return prop


def test_pivot_total_excludes_split_parent(client, db_session):
    prop = _seed(db_session)

    resp = client.get("/api/analytics/pivot", params={"property_id": prop.id})
    assert resp.status_code == 200
    body = resp.json()

    # 450 - 170 = 280 (la parente à 280 n'est PAS ajoutée en plus)
    assert body["grand_total"] == 280.0
    assert body["data"]["total"] == 280.0


def test_pivot_grouped_excludes_split_parent(client, db_session):
    """Même vérification avec un groupby (rows=nom) : la ligne parente
    masquée ne doit apparaître dans aucun groupe ni gonfler le grand_total."""
    prop = _seed(db_session)

    resp = client.get(
        "/api/analytics/pivot",
        params={"property_id": prop.id, "rows": "nom"},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["grand_total"] == 280.0
    assert "MATERA" not in body["rows"]
