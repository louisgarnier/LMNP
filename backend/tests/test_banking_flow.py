from backend.api.services import banking_service as bs


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
