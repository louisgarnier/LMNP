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


def test_list_aspsps_mock_returns_french_banks(monkeypatch):
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)
    banks = bs.list_aspsps(country="FR")
    assert len(banks) >= 1
    assert all(b["country"] == "FR" for b in banks)


def test_parse_env_file_reads_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "# commentaire ignoré\n"
        "\n"
        'ENABLE_BANKING_APP_ID="mon-app-id"\n'
        "ENABLE_BANKING_PRIVATE_KEY_PATH=./secrets/eb_private.pem\n"
        "LIGNE_SANS_EGAL\n",
        encoding="utf-8",
    )
    parsed = bs._parse_env_file(env)
    assert parsed["ENABLE_BANKING_APP_ID"] == "mon-app-id"  # quotes retirées
    assert parsed["ENABLE_BANKING_PRIVATE_KEY_PATH"] == "./secrets/eb_private.pem"
    assert "LIGNE_SANS_EGAL" not in parsed  # ligne sans '=' ignorée


def test_parse_env_file_missing_returns_empty(tmp_path):
    assert bs._parse_env_file(tmp_path / "absent.env") == {}


def test_env_triggers_live_mode(monkeypatch, tmp_path):
    # Un app_id + une clé présente + pyjwt dispo => is_live() True.
    key = tmp_path / "eb_private.pem"
    key.write_text("dummy", encoding="utf-8")
    monkeypatch.setenv("ENABLE_BANKING_APP_ID", "mon-app-id")
    monkeypatch.setenv("ENABLE_BANKING_PRIVATE_KEY_PATH", str(key))
    if bs._pyjwt() is None:
        import pytest

        pytest.skip("pyjwt non installé dans cet environnement")
    assert bs.is_live() is True
    assert bs.status()["live"] is True
