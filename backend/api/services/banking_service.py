"""Client Enable Banking (mock/live). Étape 5. Toute insertion passe par ingest_transactions."""
import os
import uuid
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_API_BASE = "https://api.enablebanking.com"


def _app_id() -> str:
    return os.getenv("ENABLE_BANKING_APP_ID", "")


def _key_path() -> Path:
    return Path(os.getenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "./secrets/eb_private.pem"))


def _redirect_url() -> str:
    return os.getenv(
        "ENABLE_BANKING_REDIRECT_URL",
        "http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1",
    )


def _pyjwt():
    """Import paresseux de pyjwt : l'app doit tourner sans la dépendance installée."""
    try:
        import jwt

        return jwt
    except Exception:
        return None


def is_live() -> bool:
    """Mode live seulement si app_id + fichier clé + pyjwt sont tous les trois présents."""
    return bool(_app_id()) and _key_path().is_file() and _pyjwt() is not None


def status() -> dict:
    if not _app_id():
        return {"live": False, "message": "Mode démo : ENABLE_BANKING_APP_ID manquant"}
    if not _key_path().is_file():
        return {"live": False, "message": "Mode démo : clé privée introuvable"}
    if _pyjwt() is None:
        return {"live": False, "message": "Mode démo : pyjwt non installé"}
    return {"live": True, "message": "Connexion Enable Banking active"}


_MOCK_ASPSPS = [
    {"name": "Mock Bank FR", "country": "FR"},
    {"name": "Boursorama (démo)", "country": "FR"},
]

_MOCK_ACCOUNTS = [
    {"account_uid": "mock-acc-1", "name": "Compte courant démo", "iban_masked": "FR76****0001", "currency": "EUR"},
    {"account_uid": "mock-acc-2", "name": "Compte travaux démo", "iban_masked": "FR76****0002", "currency": "EUR"},
]


def _make_jwt() -> str:
    """Forge le JWT RS256 d'authentification Enable Banking (mode live uniquement)."""
    jwt = _pyjwt()
    key = _key_path().read_text()
    now = datetime.utcnow()
    payload = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": _app_id()})


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_make_jwt()}"}


def _get(path: str, params: dict | None = None) -> dict:
    """Import paresseux de requests : l'app doit tourner sans la dépendance installée."""
    import requests

    r = requests.get(f"{_API_BASE}{path}", headers=_auth_headers(), params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, json: dict) -> dict:
    import requests

    r = requests.post(f"{_API_BASE}{path}", headers=_auth_headers(), json=json, timeout=30)
    r.raise_for_status()
    return r.json()


def list_aspsps(country: str = "FR") -> list[dict]:
    if not is_live():
        return [b for b in _MOCK_ASPSPS if b["country"] == country]
    data = _get("/aspsps", {"country": country})
    return data.get("aspsps", data.get("data", []))


def _mock_raw_transactions(account_uid: str) -> list[dict]:
    base = [
        {"external_id": f"{account_uid}-t1", "date": date(2026, 1, 5), "quantite": 390.0, "nom": "LOYER MOCK", "status": "booked"},
        {"external_id": f"{account_uid}-t2", "date": date(2026, 1, 6), "quantite": -60.0, "nom": "CHARGES MOCK", "status": "booked"},
        {"external_id": "fx-shared-777", "date": date(2026, 1, 7), "quantite": 12.5, "nom": "FX MOCK", "status": "booked"},  # partagé entre comptes
        {"external_id": f"{account_uid}-p1", "date": date(2026, 1, 8), "quantite": -9.9, "nom": "PENDING MOCK", "status": "pending"},
    ]
    return base
