"""Étape 2 Task 3 : Transaction.category_id + logique de backfill. Harnais isolé."""
from datetime import date


def _seed(db):
    from backend.database.models import (Property, Transaction, EnrichedTransaction,
                                         CategoryGroup, Category)
    p = Property(name="T")  # compléter les NOT NULL réels du modèle
    db.add(p); db.flush()
    g = CategoryGroup(label="Produits", nature="produits")
    db.add(g); db.flush()
    c = Category(label="Encaissement locataire et CAF", group_id=g.id, is_custom=False)
    db.add(c); db.flush()
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                    solde=500.0, property_id=p.id)
    db.add(t); db.flush()
    db.add(EnrichedTransaction(transaction_id=t.id, property_id=p.id, mois=1, annee=2024,
                               level_1="Encaissement locataire et CAF",
                               level_2="Produits", level_3="Produits"))
    db.flush()
    return t, c


def test_backfill_sets_category_id(db_session):
    from backend.database.migrations.backfill_transaction_categories import backfill
    t, c = _seed(db_session)
    stats = backfill(db_session)
    db_session.refresh(t)
    assert t.category_id == c.id
    assert stats == {"total": 1, "matched": 1, "unmatched": 0}
