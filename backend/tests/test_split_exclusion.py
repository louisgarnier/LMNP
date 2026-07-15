from datetime import date
from backend.database.models import Property, Transaction
from backend.api.utils.balance_utils import recalculate_all_balances


def test_split_parent_excluded_from_balance(db_session):
    prop = Property(name="Excl")
    db_session.add(prop); db_session.flush()
    # parente masquée (ne doit PAS compter), 2 enfants qui la remplacent
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=280.0, nom="MATERA",
                         solde=0.0, source="csv", is_split_parent=True, category_id=None)
    c1 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=450.0, nom="loyer",
                     solde=0.0, source="manual", is_split_parent=False)
    c2 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=-170.0, nom="agence",
                     solde=0.0, source="manual", is_split_parent=False)
    db_session.add_all([parent, c1, c2]); db_session.flush()
    recalculate_all_balances(db_session, prop.id)
    db_session.refresh(c2)
    # solde final = 450 - 170 = 280 (la parente 280 n'est PAS comptée en plus)
    last = db_session.query(Transaction).filter(
        Transaction.property_id == prop.id, Transaction.is_split_parent == False
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).first()
    assert last.solde == 280.0
