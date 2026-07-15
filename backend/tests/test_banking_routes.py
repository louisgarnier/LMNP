from backend.database.models import Property


def test_sync_refused_in_mock(client, db_session, monkeypatch):
    """Finding 2 : garde serveur anti-pollution — en mode démo (mock), POST /banking/sync
    doit refuser (409) plutôt que d'insérer de fausses transactions mock dans les données réelles."""
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)  # force le mode mock
    prop = Property(name="EB-SyncGuard"); db_session.add(prop); db_session.commit()
    r = client.post("/api/banking/sync", json={"property_id": prop.id})
    assert r.status_code == 409


def test_status_and_aspsps(client):
    st = client.get("/api/banking/status"); assert st.status_code == 200 and "live" in st.json()
    banks = client.get("/api/banking/aspsps?country=FR"); assert banks.status_code == 200
    assert len(banks.json()) >= 1


def test_connect_then_session_then_select(client, db_session):
    prop = Property(name="EB-Route"); db_session.add(prop); db_session.commit()
    c = client.post("/api/banking/connect", json={"property_id": prop.id, "aspsp_name": "Mock Bank FR"})
    assert c.status_code == 200 and c.json()["state"]
    state = c.json()["state"]
    s = client.post("/api/banking/sessions", json={"code": "mock-code", "state": state})
    assert s.status_code == 200 and len(s.json()["accounts"]) >= 1
    acc = s.json()["accounts"][0]
    sel = client.post("/api/banking/connections/select", json={
        "property_id": prop.id, "account_uid": acc["account_uid"], "session_id": s.json()["session_id"],
        "session_valid_until": s.json()["session_valid_until"], "aspsp_name": "Mock Bank FR",
        "account_name": acc["name"], "iban_masked": acc["iban_masked"], "currency": acc["currency"]})
    assert sel.status_code == 200
    conns = client.get(f"/api/banking/connections?property_id={prop.id}")
    assert len(conns.json()) == 1
