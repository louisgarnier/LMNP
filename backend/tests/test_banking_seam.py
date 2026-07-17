import os
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def test_clean_remittance_credit_mutuel_champs_pre_decoupes():
    """Crédit Mutuel envoie des champs DÉJÀ découpés : le libellé métier est le 1er.

    Régression : l'heuristique « ligne 2 » est propre à LCL, qui envoie UN seul
    élément multi-lignes (ligne 1 = type, ligne 2 = libellé). Le Crédit Mutuel
    envoie PLUSIEURS éléments (élément 0 = libellé, élément 1 = référence unique
    E2EID/FHD/I…). Prendre la ligne 2 y ramenait la référence — différente à
    chaque transaction — donc plus aucune règle ne matchait (3/25 classées).
    """
    # Loyer Matera : le libellé est l'élément 0, pas la référence E2EID.
    assert bs._clean_remittance(
        ["VIR MATERA", "E2EID-25602760", "LOYER - APPARTEMENT - ETAGE 8 - 110", " PLACE DES MIROIRS"]
    ) == "VIR MATERA"
    # Prélèvements : le libellé (tronqué à 31 car. par la banque) matche les
    # règles historiques bâties sur les exports CSV.
    assert bs._clean_remittance(
        ["PRLV SEPA FREE TELECOM", "FHD-1484243903", "FREE HAUTDEBIT 1484243903"]
    ) == "PRLV SEPA FREE TELECOM"
    assert bs._clean_remittance(
        ["PRLV SEPA MACIF PRODUCTION-MACI", "I0000714951398014477067076", "-PRELEV 0306072026  01447706707"]
    ) == "PRLV SEPA MACIF PRODUCTION-MACI"
    # Virement interne : 2 éléments, le 2e est une référence.
    assert bs._clean_remittance(
        ["VIR C/C EUROCOMPTE CONFORT", "CH3W26180W003286"]
    ) == "VIR C/C EUROCOMPTE CONFORT"
    # Échéance de prêt : un seul élément, une seule ligne -> inchangé.
    assert bs._clean_remittance(
        ["ECH PRET CAP+IN 08922 213949 04"]
    ) == "ECH PRET CAP+IN 08922 213949 04"


def test_relative_key_path_resolves_from_repo_root_not_cwd(tmp_path, monkeypatch):
    """Le chemin relatif de la clé doit se résoudre depuis la racine du projet.

    Régression : le backend se lance depuis backend/ (cf. START_SERVERS.md), donc
    un `./secrets/eb_private.pem` relatif au CWD pointait sur backend/secrets/ —
    introuvable — et l'app basculait silencieusement en mode démo, coupant
    l'ingestion réelle Enable Banking.
    """
    repo_root = Path(bs.__file__).resolve().parents[3]
    key = repo_root / "secrets" / "eb_private.pem"
    if not key.is_file():
        pytest.skip("secrets/eb_private.pem absent de ce poste")

    monkeypatch.setenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "./secrets/eb_private.pem")
    monkeypatch.chdir(tmp_path)  # simule un lancement depuis n'importe quel dossier

    assert bs._key_path().is_file(), (
        f"clé introuvable depuis cwd={tmp_path} : "
        f"_key_path() a résolu {bs._key_path()}"
    )


def test_fetch_raw_tente_tout_l_historique_et_retombe_a_90j_si_refus(monkeypatch):
    """On demande tout l'historique ; on ne se plafonne à J-89 que si la banque refuse.

    Régression : le plafond J-89 était codé en dur à cause de LCL (422
    WRONG_TRANSACTIONS_PERIOD au-delà de ~90 jours). Le Crédit Mutuel, lui,
    accepte tout l'historique — le plafond lui faisait jeter 39 des 64
    transactions disponibles, laissant un trou de 4 mois dans le compte d'Evry.
    """
    acc = SimpleNamespace(eb_account_uid="uid-1", bank_name="Banque Test")
    monkeypatch.setattr(bs, "is_live", lambda: True)

    # Banque généreuse (Crédit Mutuel) : la date demandée est respectée.
    calls = []

    def generous(path, params):
        calls.append(params["date_from"])
        return {"transactions": [{"id": "a"}]}

    monkeypatch.setattr(bs, "_get", generous)
    bs._fetch_raw(acc, date(2026, 1, 1))
    assert calls == ["2026-01-01"], "la date demandée doit être respectée si la banque l'accepte"

    # Banque restrictive (LCL) : 422 -> on retente plafonné à J-89, sans planter.
    calls.clear()

    def restrictive(path, params):
        calls.append(params["date_from"])
        if len(calls) == 1:
            raise RuntimeError("422 Client Error: WRONG_TRANSACTIONS_PERIOD")
        return {"transactions": [{"id": "b"}]}

    monkeypatch.setattr(bs, "_get", restrictive)
    out = bs._fetch_raw(acc, date(2026, 1, 1))
    assert len(calls) == 2, "un refus doit déclencher UNE nouvelle tentative"
    assert calls[1] == (date.today() - timedelta(days=89)).isoformat()
    assert out == [{"id": "b"}], "les transactions de la tentative de repli sont retournées"
