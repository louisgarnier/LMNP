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
    ids_a = {t["entry_reference"] for t in a}
    ids_b = {t["entry_reference"] for t in b}
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


def test_normalize_real_enable_banking_shape():
    """Format réel Berlin Group : montant positif + credit_debit_indicator pour le signe."""
    from datetime import date
    dbit = bs._normalize({
        "entry_reference": "eb-123",
        "transaction_amount": {"currency": "EUR", "amount": "128.08"},
        "credit_debit_indicator": "DBIT",
        "status": "BOOK",
        "booking_date": "2026-07-15",
        "remittance_information": ["PRELVT SEPA RECU\nCAPITAINE GALINAT"],
        "transaction_id": None,
    })
    assert dbit["quantite"] == -128.08          # DBIT = sortie → négatif
    assert dbit["date"] == date(2026, 7, 15)    # booking_date parsée en objet date
    assert dbit["external_id"] == "eb-123"      # entry_reference (transaction_id null)
    assert "\n" not in dbit["nom"] and "CAPITAINE GALINAT" in dbit["nom"]

    crdt = bs._normalize({
        "entry_reference": "eb-456",
        "transaction_amount": {"currency": "EUR", "amount": "390.00"},
        "credit_debit_indicator": "CRDT",
        "status": "BOOK",
        "booking_date": "2026-07-10",
        "remittance_information": ["VIREMENT LOYER"],
    })
    assert crdt["quantite"] == 390.0            # CRDT = entrée → positif


def test_clean_remittance_extrait_le_libelle_metier():
    """Le libellé LCL réel = ligne 2 (métier), pas la ligne 1 (type) ni les références."""
    # Loyer : doit retomber EXACTEMENT sur le libellé du CSV -> matche les règles.
    assert bs._clean_remittance(
        ["VIREMENT INSTANTANE\n\nVIR INST Gwenael Le Bourhis &\nEnvoye depuis Revolut\n\n\nIPR000313685138"]
    ) == "VIR INST Gwenael Le Bourhis &"
    # Prêt : jette DOSSIER NO / PM ET la date finale (libellé stable tous mois).
    assert bs._clean_remittance(
        ["PRET IMMOBILIER ECH\n\nPRET IMMOBILIER ECH 13/07/26\nDOSSIER NO 5008900I01QH11AH\nPM15008900I01QH11AH01130726\n\n"]
    ) == "PRET IMMOBILIER ECH"
    # SEPA : jette ICS / RUM / SDR.
    assert bs._clean_remittance(
        ["PRELVT SEPA RECU D/O CONFRERE\n\nPRLV SEPA 17D CAPITAINE GALINAT\nICS.FR63ZZZ820D90\n.RUM.W0269C000052642N00\n0010115\nSDR619498426964"]
    ) == "PRLV SEPA 17D CAPITAINE GALINAT"
    # Une seule ligne significative -> on la garde.
    assert bs._clean_remittance(["LOYER MOCK"]) == "LOYER MOCK"
    # Vide -> chaîne vide (pas d'exception).
    assert bs._clean_remittance([]) == ""
    assert bs._clean_remittance(None) == ""


def test_clean_remittance_retire_la_date_finale():
    """Les libellés récurrents avec date perdent la date finale (règle unique tous mois)."""
    assert bs._clean_remittance(
        ["PRET IMMOBILIER ECH\n\nPRET IMMOBILIER ECH 13/07/26\nDOSSIER NO 5008900\nPM150089\n\n"]
    ) == "PRET IMMOBILIER ECH"
    assert bs._clean_remittance(
        ["PRET IMMOBILIER ECH\n\nPRET IMMOBILIER ECH 04/05/26\nDOSSIER NO 5008900\n\n"]
    ) == "PRET IMMOBILIER ECH"
    # une date au MILIEU n'est pas retirée (seulement en fin)
    assert bs._clean_remittance(["X\n\nFACTURE 12/03/25 SOLDE"]) == "FACTURE 12/03/25 SOLDE"
    # pas de date -> inchangé
    assert bs._clean_remittance(["X\n\nVIR INST Gwenael Le Bourhis &"]) == "VIR INST Gwenael Le Bourhis &"
