"""Client Enable Banking (mock/live). Étape 5. Toute insertion passe par ingest_transactions."""
import os
import re
import uuid
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.models import BankAccount, Transaction

logger = logging.getLogger(__name__)

_API_BASE = "https://api.enablebanking.com"

# Borne basse quand un compte n'a jamais été synchronisé : on demande tout ce que
# la banque accepte de donner (voir _fetch_raw), pas une fenêtre arbitraire.
_EARLIEST_HISTORY = date(2020, 1, 1)

# Profondeur de la fenêtre glissante redemandée à CHAQUE synchro. 90 jours, car
# c'est la limite que les banques servent sans broncher (LCL refuse au-delà :
# 422 WRONG_TRANSACTIONS_PERIOD). Redemander large est sans risque — l'anti-doublon
# (account_id, external_id) écarte ce qu'on a déjà — et c'est ce qui permet à un
# trou dans l'historique de se reboucher tout seul.
_LOOKBACK_DAYS = 90


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
    # Résolu depuis la racine du projet, jamais depuis le CWD : le backend se
    # lance aussi bien depuis backend/ (cf. START_SERVERS.md) que depuis la
    # racine, et un chemin relatif au CWD faisait basculer l'app en mode démo
    # sans le dire, coupant l'ingestion réelle.
    raw = Path(os.getenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "./secrets/eb_private.pem"))
    if raw.is_absolute():
        return raw
    return (Path(__file__).resolve().parents[3] / raw).resolve()


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
    """Extrait le libellé métier d'un remittance_information Enable Banking.

    Les deux banques rangent l'information à l'INVERSE, et la forme de la donnée
    les distingue — inutile de coder le nom de la banque en dur :

    LCL — UN seul élément, bloc à retours à la ligne :
        ligne 1  = TYPE bancaire        (ex "VIREMENT INSTANTANE", "PRET IMMOBILIER ECH")
        ligne 2  = LIBELLÉ MÉTIER       (ex "VIR INST Gwenael Le Bourhis &")  <-- ce que
                                         les CSV LCL conservaient, donc ce que les règles
                                         de classement connaissent.
        lignes + = références uniques   (IPR…, DOSSIER NO…, ICS…, .RUM…, SDR…) → à jeter,
                                         car différentes à chaque transaction (sinon aucune
                                         règle ne matche et tout tombe en boîte de réception).
        → on garde la 2e ligne non vide si elle existe, sinon la 1re.

    Crédit Mutuel — PLUSIEURS éléments, champs déjà découpés :
        élément 0 = LIBELLÉ MÉTIER      (ex "VIR MATERA", "PRLV SEPA FREE TELECOM",
                                         tronqué à 31 car. par la banque — exactement
                                         ce que contiennent les exports CSV, donc les règles)
        élément 1 = référence unique    (E2EID-…, FHD-…, I0000…) → à jeter
        éléments+ = complément libre    (ex "LOYER - APPARTEMENT - ETAGE 8")
        → on garde le 1er élément.

    Un élément unique d'une seule ligne (ex "ECH PRET CAP+IN 08922 213949 04") retombe
    correctement dans les deux cas.
    """
    if isinstance(remittance, str):
        remittance = [remittance]
    parts = [str(x) for x in (remittance or [])]
    if len(parts) > 1:
        # Champs pré-découpés (Crédit Mutuel) : le libellé métier est le premier.
        lines = [p.strip() for p in parts if p.strip()]
        label = lines[0] if lines else ""
    else:
        # Bloc unique multi-lignes (LCL) : le libellé métier est la 2e ligne.
        lines = [ln.strip() for ln in "\n".join(parts).split("\n") if ln.strip()]
        if not lines:
            return ""
        label = lines[1] if len(lines) >= 2 else lines[0]
    if not label:
        return ""
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
    # La profondeur d'historique dépend de la BANQUE, pas de PSD2 : LCL refuse
    # au-delà de ~90 jours (422 WRONG_TRANSACTIONS_PERIOD) mais le Crédit Mutuel
    # sert tout. On demande donc large et on ne se plafonne à J-89 QUE sur refus —
    # plafonner d'office faisait jeter 39 des 64 transactions du compte d'Evry.
    start = since or _EARLIEST_HISTORY
    try:
        return _fetch_pages(bank_account.eb_account_uid, start)
    except Exception as exc:
        fallback = date.today() - timedelta(days=89)
        if start >= fallback:
            raise
        logger.warning(
            "⚠️ [Banking] %s refuse l'historique depuis %s (%s) — repli sur %s",
            bank_account.bank_name, start, str(exc)[:80], fallback,
        )
        return _fetch_pages(bank_account.eb_account_uid, fallback)


def _fetch_pages(account_uid: str, start: date) -> list[dict]:
    out, params = [], {"date_from": start.isoformat()}
    while True:
        data = _get(f"/accounts/{account_uid}/transactions", params)
        out.extend(data.get("transactions", []))
        cont = data.get("continuation_key")
        if not cont:
            break
        params["continuation_key"] = cont
    return out


def _since_for(db: Session, bank_account: BankAccount):
    """Date à partir de laquelle redemander l'historique à la banque.

    FENÊTRE GLISSANTE, jamais l'horloge de la dernière synchro.

    Historique de la décision (2026-07-17) :
    - `since = last_sync_at` rendait toute suppression IRRÉVERSIBLE : supprimer
      juin/juillet puis resynchroniser redemandait « depuis aujourd'hui » et les
      transactions ne revenaient jamais. Un demi-échec de synchro faisait avancer
      last_sync_at malgré tout — les transactions manquantes étaient perdues.
    - `since = dernière transaction en base` (1re tentative) ne règle que le trou
      en FIN d'historique. Sur un trou AU MILIEU — juin supprimé mais une écriture
      du 17/07 subsistante — la fenêtre repart du 17/07 et saute par-dessus le
      trou. Constaté en conditions réelles le 2026-07-17.

    D'où la fenêtre glissante : on redemande systématiquement les
    `_LOOKBACK_DAYS` derniers jours et on laisse l'anti-doublon
    `(account_id, external_id)` écarter ce qu'on a déjà. Un trou se rebouche
    alors où qu'il soit, sans intervention.

    Deux garde-fous :

    1. Ne JAMAIS remonter avant le dernier import CSV du bien. Les lignes CSV
       n'ont ni `account_id` ni `external_id` : l'anti-doublon est aveugle sur
       elles (bug du 19/01/2026, 347,28 € comptés deux fois). Sans ce plancher,
       une fenêtre qui les recouvre dupliquerait tout l'historique importé.
    2. Compte réellement neuf (aucune transaction) → None : première synchro, on
       prend tout l'historique disponible ; il n'y a rien à dupliquer.
    """
    a_des_donnees = (
        db.query(Transaction.id)
        .filter(Transaction.property_id == bank_account.property_id)
        .first()
        is not None
    )
    if not a_des_donnees:
        return None  # première synchro : tout l'historique

    fenetre = date.today() - timedelta(days=_LOOKBACK_DAYS)
    dernier_csv = (
        db.query(func.max(Transaction.date))
        .filter(
            Transaction.property_id == bank_account.property_id,
            Transaction.account_id.is_(None),  # lignes CSV : pas d'external_id
        )
        .scalar()
    )
    if dernier_csv is not None:
        return max(fenetre, dernier_csv)
    return fenetre


def sync_account(db: Session, bank_account: BankAccount) -> dict:
    """Synchronise UN compte bancaire : fetch → filtre pending → ingest_transactions
    (dédoublonnage + classif + recalculs). ingest_transactions committe déjà son propre
    travail atomiquement (pas de SAVEPOINT nécessaire) ; l'isolation "un compte en échec
    ne bloque pas les autres" est assurée par ce try/except par compte, appelé par
    sync_property compte par compte. Retourne {account_id, inserted, deduplicated, errors}."""
    from backend.api.services.ingestion_service import ingest_transactions

    since = _since_for(db, bank_account)
    # Trace de la fenêtre réellement demandée. Le 2026-07-17, un correctif de
    # cette fonction a été livré sans que le serveur (lancé sans --reload) ne le
    # charge : les tests étaient verts, l'app tournait sur l'ancien code, et la
    # resynchro n'a rien ramené. On journalise donc la fenêtre à chaque synchro —
    # c'est le seul moyen de vérifier après coup ce qui a VRAIMENT été demandé.
    logger.info(
        "📥 [Banking] sync compte %s (%s) — fenêtre demandée depuis %s",
        bank_account.id, bank_account.bank_name, since or "origine (première synchro)",
    )
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
