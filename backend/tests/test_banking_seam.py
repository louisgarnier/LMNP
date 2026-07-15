import os
from backend.api.services import banking_service as bs


def test_mock_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)
    assert bs.is_live() is False
    st = bs.status()
    assert st["live"] is False
    assert "message" in st


def test_mock_aspsps_are_french():
    banks = bs._MOCK_ASPSPS
    assert len(banks) >= 1
    assert all(b.get("country") == "FR" for b in banks)


def test_mock_transactions_include_shared_fx_id():
    # deux comptes différents partageant le même external_id (piège FX)
    a = bs._mock_raw_transactions(bs._MOCK_ACCOUNTS[0]["account_uid"])
    b = bs._mock_raw_transactions(bs._MOCK_ACCOUNTS[1]["account_uid"])
    ids_a = {t["external_id"] for t in a}
    ids_b = {t["external_id"] for t in b}
    assert ids_a & ids_b, "au moins un external_id partagé entre 2 comptes (test dédoublonnage composite)"
