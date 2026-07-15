from datetime import date
from backend.database.models import Property, BankAccount, Transaction
from backend.api.services import banking_service as bs


def _seed(db_session):
    prop = Property(name="EB-Sync"); db_session.add(prop); db_session.flush()
    acc = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-1", bank_name="Mock", currency="EUR")
    db_session.add(acc); db_session.commit()
    return prop, acc


def test_sync_inserts_booked_ignores_pending(db_session):
    prop, acc = _seed(db_session)
    res = bs.sync_account(db_session, acc)
    txs = db_session.query(Transaction).filter(Transaction.property_id == prop.id).all()
    noms = {t.nom for t in txs}
    assert "LOYER MOCK" in noms
    assert "PENDING MOCK" not in noms          # pending filtré
    assert all(t.source == "api" for t in txs)


def test_sync_is_incremental_no_dup_on_second_run(db_session):
    prop, acc = _seed(db_session)
    bs.sync_account(db_session, acc)
    n1 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    bs.sync_account(db_session, acc)           # 2e passe
    n2 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    assert n1 == n2                            # dédoublonnage (account_id, external_id)


def test_sync_fx_shared_id_scoped_by_account(db_session):
    prop, acc1 = _seed(db_session)
    acc2 = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-2", bank_name="Mock", currency="EUR")
    # note : un compte par bien en usage réel ; ici 2 comptes pour tester le scoping FX
    db_session.add(acc2); db_session.commit()
    bs.sync_account(db_session, acc1)
    bs.sync_account(db_session, acc2)
    fx = db_session.query(Transaction).filter(Transaction.nom == "FX MOCK").all()
    assert len(fx) == 2                        # même external_id mais 2 account_id → 2 lignes distinctes
