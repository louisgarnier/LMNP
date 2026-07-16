"""Client Enable Banking (mock/live). Étape 5. Toute insertion passe par ingest_transactions."""
import os
import re
import uuid
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.database.models import BankAccount, Transaction

logger = logging.getLogger(__name__)

_API_BASE = "https://api.enablebanking.com"


def _parse_env_file(path: Path) -> dict:
    """Lit un fichier .env (KEY=value, # commentaires, quotes optionnelles) → dict.

    Fonction pure : ne touche pas os.environ. Fichier absent → dict vide.
    """
    result: dict = {}
    if not path.is_file():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _load_dotenv_once() -> None:
    """Charge le .env racine dans os.environ (sans dépendance, sans écraser l'existant).

    Idempotent : ne relit le fichier qu'une fois par process.
    """
    if getattr(_load_dotenv_once, "_done", False):
        return
    _load_dotenv_once._done = True
    # Déterminisme des tests : sous pytest, on n'injecte JAMAIS le .env du poste
    # (sinon is_live() deviendrait vrai et les tests « mock » taperaient l'API réelle).
    import sys
    if "pytest" in sys.modules:
        return
    env_path = Path(__file__).resolve().parents[3] / ".env"
    try:
        for key, value in _parse_env_file(env_path).items():
            if key not in os.environ:
                os.environ[key] = value
    except Exception as exc:  # pragma: no cover - le mode démo reste le repli sûr
        logger.warning("⚠️ [Banking] lecture .env impossible: %s", exc)


_load_dotenv_once()


def _app_id() -> str:
    return os.getenv("ENABLE_BANKING_APP_ID", "")


def _key_path() -> Path:
    return Path(os.getenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "./secrets/eb_private.pem"))


def _redirect_url() -> str:
    # Chemin PROPRE sans query params : Enable Banking refuse d'enregistrer une
    # URL de retour contenant des `?param`. La banque ajoute ?code&state au
    # retour ; la page /eb-callback rebascule ensuite vers l'onglet Paramètres.
    return os.getenv(
        "ENABLE_BANKING_REDIRECT_URL",
        "http://localhost:3000/eb-callback",
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


_pending_states: dict[str, int] = {}  # state -> property_id (mémoire process, mono-poste)


def _register_state(state: str, property_id: int) -> None:
    if len(_pending_states) > 128:
        _pending_states.clear()
    _pending_states[state] = property_id


def _pop_state(state: str) -> Optional[int]:
    return _pending_states.pop(state, None)


def start_auth(property_id: int, aspsp_name: str, country: str = "FR") -> dict:
    state = str(uuid.uuid4())
    _register_state(state, property_id)
    if not is_live():
        return {"authorization_url": f"{_redirect_url()}&code=mock-code&state={state}", "state": state}
    valid_until = (datetime.utcnow() + timedelta(days=180)).replace(microsecond=0).isoformat() + "Z"
    body = {
        "access": {"valid_until": valid_until},
        "aspsp": {"name": aspsp_name, "country": country},
        "state": state,
        "redirect_url": _redirect_url(),
        "psu_type": "personal",
    }
    data = _post("/auth", body)
    return {"authorization_url": data["url"], "state": state}


def create_session(code: str, state: str) -> dict:
    pid = _pop_state(state)
    if pid is None:
        raise ValueError("state OAuth inconnu ou expiré")
    valid_until = (date.today() + timedelta(days=180)).isoformat()
    if not is_live():
        return {
            "session_id": f"mock-sess-{state[:8]}",
            "session_valid_until": valid_until,
            "property_id": pid,
            "accounts": _MOCK_ACCOUNTS,
        }
    data = _post("/sessions", {"code": code})
    accounts = [
        {
            "account_uid": a["uid"],
            "name": a.get("name", ""),
            "iban_masked": a.get("iban", ""),
            "currency": a.get("currency", "EUR"),
        }
        for a in data.get("accounts", [])
    ]
    return {
        "session_id": data["session_id"],
        "session_valid_until": data.get("valid_until", valid_until),
        "property_id": pid,
        "accounts": accounts,
    }


def select_account(db: Session, property_id: int, account_uid: str, session_id: str,
                   session_valid_until: str, aspsp_name: str, account_name: str,
                   iban_masked: str, currency: str) -> BankAccount:
    """Upsert UN compte bancaire par bien : relier un autre compte au même bien REMPLACE."""
    existing = db.query(BankAccount).filter(BankAccount.property_id == property_id).first()
    acc = existing or BankAccount(property_id=property_id)
    acc.eb_account_uid = account_uid
    acc.eb_session_id = session_id
    acc.session_valid_until = date.fromisoformat(session_valid_until) if session_valid_until else None
    acc.bank_name = aspsp_name
    acc.account_name = account_name
    acc.iban_masked = iban_masked
    acc.currency = currency
    if not existing:
        db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def list_connections(db: Session, property_id: int) -> list[BankAccount]:
    return db.query(BankAccount).filter(BankAccount.property_id == property_id).all()


def disconnect(db: Session, account_id: int) -> bool:
    """Supprime le compte bancaire mais CONSERVE les transactions déjà importées :
    on détache la FK (account_id -> NULL) avant de supprimer, sinon la contrainte
    FK (transactions.account_id -> bank_accounts.id, sans ondelete) lève une
    IntegrityError dès qu'une synchro a eu lieu avant la déconnexion."""
    acc = db.get(BankAccount, account_id)
    if not acc:
        return False
    db.query(Transaction).filter(Transaction.account_id == account_id).update(
        {Transaction.account_id: None}, synchronize_session=False
    )
    db.delete(acc)
    db.commit()
    return True  # conserve les transactions (account_id nullable)


def _clean_remittance(remittance) -> str:
    """Extrait le libellé métier d'un remittance_information Enable Banking (LCL).

    Structure LCL observée (une chaîne à retours à la ligne) :
        ligne 1  = TYPE bancaire        (ex "VIREMENT INSTANTANE", "PRET IMMOBILIER ECH")
        ligne 2  = LIBELLÉ MÉTIER       (ex "VIR INST Gwenael Le Bourhis &")  <-- ce que
                                         les CSV LCL conservaient, donc ce que les règles
                                         de classement connaissent.
        lignes + = références uniques   (IPR…, DOSSIER NO…, ICS…, .RUM…, SDR…) → à jeter,
                                         car différentes à chaque transaction (sinon aucune
                                         règle ne matche et tout tombe en boîte de réception).

    On garde donc la 2e ligne non vide si elle existe, sinon la 1re.
    """
    if isinstance(remittance, str):
        remittance = [remittance]
    text = "\n".join(str(x) for x in (remittance or []))
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    label = lines[1] if len(lines) >= 2 else lines[0]
    # Retire une date en fin de libellé (JJ/MM/AA[AA]) pour stabiliser les
    # libellés récurrents : "PRET IMMOBILIER ECH 13/07/26" -> "PRET IMMOBILIER ECH".
    # Une seule règle couvre alors tous les mois ; la date reste portée par le
    # champ `date` de la transaction.
    label = re.sub(r"\s+\d{2}/\d{2}/\d{2,4}\s*$", "", label).strip()
    return label


def _normalize(raw: dict) -> dict:
    """Convertit une transaction Enable Banking (format réel Berlin Group) vers
    le format attendu par ingest_transactions.

    Format réel : montant TOUJOURS positif dans transaction_amount.amount (chaîne),
    signe porté par credit_debit_indicator (DBIT = sortie → négatif, CRDT = entrée),
    libellé dans remittance_information (liste), date dans booking_date, identifiant
    unique dans entry_reference (transaction_id souvent null chez LCL)."""
    amt = raw.get("transaction_amount") or {}
    quantite = float(amt.get("amount") or 0)
    if raw.get("credit_debit_indicator") == "DBIT":
        quantite = -quantite

    nom = _clean_remittance(raw.get("remittance_information"))

    raw_date = raw.get("booking_date") or raw.get("value_date") or raw.get("transaction_date")
    tx_date = date.fromisoformat(raw_date) if isinstance(raw_date, str) else raw_date

    external_id = raw.get("entry_reference") or raw.get("transaction_id") or None
    return {"date": tx_date, "quantite": quantite, "nom": nom, "external_id": external_id}


def _fetch_raw(bank_account: BankAccount, since) -> list[dict]:
    if not is_live():
        return _mock_raw_transactions(bank_account.eb_account_uid)
    # PSD2 : l'accès aux transactions est limité à ~90 jours d'historique (au-delà
    # LCL renvoie 422 WRONG_TRANSACTIONS_PERIOD). On plafonne date_from à J-89.
    earliest = date.today() - timedelta(days=89)
    start = since if (since and since > earliest) else earliest
    out, params = [], {"date_from": start.isoformat()}
    while True:
        data = _get(f"/accounts/{bank_account.eb_account_uid}/transactions", params)
        out.extend(data.get("transactions", []))
        cont = data.get("continuation_key")
        if not cont:
            break
        params["continuation_key"] = cont
    return out


def sync_account(db: Session, bank_account: BankAccount) -> dict:
    """Synchronise UN compte bancaire : fetch → filtre pending → ingest_transactions
    (dédoublonnage + classif + recalculs). ingest_transactions committe déjà son propre
    travail atomiquement (pas de SAVEPOINT nécessaire) ; l'isolation "un compte en échec
    ne bloque pas les autres" est assurée par ce try/except par compte, appelé par
    sync_property compte par compte. Retourne {account_id, inserted, deduplicated, errors}."""
    from backend.api.services.ingestion_service import ingest_transactions

    since = bank_account.last_sync_at.date() if bank_account.last_sync_at else None
    try:
        raw = _fetch_raw(bank_account, since)
        # On n'importe que les écritures comptabilisées (status BOOK) ; on écarte
        # le prévisionnel/en attente (PDNG) et le rejeté (RJCT) — non définitifs.
        rows = [_normalize(r) for r in raw if r.get("status") == "BOOK"]
        res = ingest_transactions(db, bank_account.property_id, bank_account.id, rows, "api")
        bank_account.last_sync_at = datetime.utcnow()
        db.commit()                                                      # persiste last_sync_at
        return {"account_id": bank_account.id, **res, "errors": []}
    except Exception as e:
        db.rollback()
        logger.error(f"[banking] sync compte {bank_account.id} échec: {e}")
        return {"account_id": bank_account.id, "inserted": 0, "deduplicated": 0, "errors": [str(e)]}


def sync_property(db: Session, property_id: int) -> dict:
    accounts = db.query(BankAccount).filter(BankAccount.property_id == property_id).all()
    return {a.id: sync_account(db, a) for a in accounts}


def _mock_raw_transactions(account_uid: str) -> list[dict]:
    """Transactions de démo au FORMAT RÉEL Enable Banking (mêmes clés que LCL),
    pour que _normalize soit exercé de façon identique en mock et en live."""
    def tx(ref: str, day: str, amount: float, indicator: str, label: str, status: str = "BOOK") -> dict:
        return {
            "entry_reference": ref,
            "transaction_amount": {"currency": "EUR", "amount": f"{abs(amount):.2f}"},
            "credit_debit_indicator": indicator,  # CRDT = entrée (+), DBIT = sortie (-)
            "status": status,
            "booking_date": day,
            "remittance_information": [label],
        }
    return [
        tx(f"{account_uid}-t1", "2026-01-05", 390.0, "CRDT", "LOYER MOCK"),
        tx(f"{account_uid}-t2", "2026-01-06", 60.0, "DBIT", "CHARGES MOCK"),
        tx("fx-shared-777", "2026-01-07", 12.5, "CRDT", "FX MOCK"),  # external_id partagé entre comptes
        tx(f"{account_uid}-p1", "2026-01-08", 9.9, "DBIT", "PENDING MOCK", status="PDNG"),  # écarté (non BOOK)
    ]
