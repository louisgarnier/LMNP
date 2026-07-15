from backend.api.services import banking_service as bs
from backend.database.models import Property, BankAccount


def test_select_account_upserts_one_per_property(db_session):
    prop = Property(name="EB-Select"); db_session.add(prop); db_session.flush()
    acc = bs.select_account(db_session, property_id=prop.id, account_uid="mock-acc-1",
                            session_id="s1", session_valid_until="2026-12-31",
                            aspsp_name="Mock Bank FR", account_name="Courant",
                            iban_masked="FR76****0001", currency="EUR")
    assert acc.property_id == prop.id and acc.eb_account_uid == "mock-acc-1"
    # relier un AUTRE compte au même bien remplace (un compte par bien)
    acc2 = bs.select_account(db_session, property_id=prop.id, account_uid="mock-acc-2",
                             session_id="s1", session_valid_until="2026-12-31",
                             aspsp_name="Mock Bank FR", account_name="Travaux",
                             iban_masked="FR76****0002", currency="EUR")
    rows = db_session.query(BankAccount).filter(BankAccount.property_id == prop.id).all()
    assert len(rows) == 1 and rows[0].eb_account_uid == "mock-acc-2"


def test_start_auth_mock_returns_url_and_state(monkeypatch):
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)
    res = bs.start_auth(property_id=25, aspsp_name="Mock Bank FR")
    assert res["authorization_url"]
    assert res["state"]


def test_create_session_mock_returns_accounts_and_property(monkeypatch):
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)
    auth = bs.start_auth(property_id=25, aspsp_name="Mock Bank FR")
    sess = bs.create_session(code="mock-code", state=auth["state"])
    assert sess["property_id"] == 25
    assert sess["session_valid_until"]
    assert len(sess["accounts"]) >= 1
    assert "account_uid" in sess["accounts"][0]
