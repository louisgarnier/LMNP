from datetime import date
from backend.database.models import Transaction, BankAccount, Property


def test_transaction_has_ingestion_fields(db_session):
    prop = Property(name="T-schema")
    db_session.add(prop)
    db_session.flush()
    tx = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=10.0,
                     nom="X", solde=10.0, source="manual", is_split_parent=False)
    db_session.add(tx)
    db_session.flush()
    assert tx.source == "manual"
    assert tx.is_split_parent is False
    assert tx.account_id is None
    assert tx.external_id is None
    assert tx.parent_transaction_id is None


def test_bank_account_model(db_session):
    prop = Property(name="T-bank")
    db_session.add(prop)
    db_session.flush()
    acc = BankAccount(property_id=prop.id, bank_name="Boursorama", iban_masked="FR76****1234")
    db_session.add(acc)
    db_session.flush()
    assert acc.id is not None
    assert acc.property_id == prop.id
