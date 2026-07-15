# Étape 5 — Enable Banking (mock-first) — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Porter le module Enable Banking de `~/Claude/compta_sasu` vers LMNP, mock-first, en branchant la synchro sur `ingest_transactions(source="api")` de l'étape 4, avec un onglet « Paramètres » par appartement.

**Architecture:** Un service `banking_service.py` (porté + adapté) encapsule le client PSD2 (JWT RS256, seam `is_live()` mock/live). Toute insertion passe par `ingest_transactions` (aucun calcul financier dans le service). Un onglet « Paramètres » gère, par bien, la connexion (retour auto), la sélection d'UN compte, la carte compte, la synchro manuelle et l'alerte J‑30.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, PyJWT (RS256), httpx/requests, Pytest ; frontend Next.js/React/TS. Blueprint source : `~/Claude/compta_sasu/backend/services/banking.py`, `backend/api/routes/banking.py`, `frontend/app/banking/page.tsx`.

## Global Constraints

- **Mock-first** : `is_live()` = `ENABLE_BANKING_APP_ID` non vide ET fichier clé présent ET `pyjwt` importable ; sinon **mock**. L'app démarre/teste sans credentials.
- **Secrets jamais committés** : `.env`, `secrets/`, `*.pem` dans `.gitignore` ; l'implémenteur ne crée ni ne commite AUCUN vrai secret ni PEM réel (les tests utilisent des clés jetables générées à la volée ou le chemin mock).
- **Toute insertion via `ingest_transactions(db, property_id, account_id, rows, "api")`** — `rows` = `[{"date": date, "quantite": float, "nom": str, "external_id": str}]`. Jamais d'insertion directe de `Transaction` dans le service banking.
- **Dédoublonnage composite `(account_id, external_id)`** (déjà dans `ingest_transactions` étape 4) — jamais `external_id` seul.
- **Un compte bancaire par appartement** : `select` remplace le compte lié d'un `property_id`.
- **Golden 0** sur l'existant (le mock n'écrit que dans des DB de test isolées). Non-régression 0.
- **Garde anti-pollution** : en mode mock, le bouton « Synchroniser » est **désactivé côté UI** (« mode démo ») ; le chemin mock de sync n'est exercé que par les tests isolés.
- **Montants en euros** côté service (EuroCents convertit en aval). `property_id` explicite partout. Erreurs jamais avalées. Tests en harnais isolé (`db_session`/`client`), jamais la base de prod.
- **Commits** git natifs, jamais `trades_evry_2025.csv`.

---

## File Structure

- `backend/api/services/banking_service.py` — **créé** : seam mock/live, client PSD2 (JWT, /aspsps, /auth, /sessions, /accounts), mock data, connection flow, sync → ingest_transactions.
- `backend/api/routes/banking.py` — **créé** : endpoints `/api/banking/*` property-scoped.
- `backend/api/main.py` — modifié : enregistre le router `banking`.
- `backend/database/models.py` — modifié : + `account_name`, `currency`, `bank_balance` sur `BankAccount`.
- `backend/database/migrations/add_bank_account_display_fields.py` — **créé** : migration additive.
- `.gitignore` — modifié : `.env`, `secrets/`, `*.pem`.
- `frontend/src/api/client.ts` — modifié : `bankingAPI`.
- `frontend/src/components/Navigation.tsx` — modifié : onglet « Paramètres ».
- `frontend/src/components/ParametresScreen.tsx` — **créé** : l'onglet (statut, connexion, retour auto, sélection compte, carte compte, sync, déconnexion, alerte J‑30).
- `frontend/app/dashboard/transactions/page.tsx` — modifié : rend `ParametresScreen` sur `?tab=parametres`.
- Tests : `backend/tests/test_banking_seam.py`, `test_banking_flow.py`, `test_banking_sync.py`, `test_banking_routes.py` ; `frontend/__tests__/parametres.test.tsx`.

**Note portage :** pour chaque partie mécanique (JWT, helpers HTTP, structure mock), LIS le blueprint `~/Claude/compta_sasu/backend/services/banking.py` aux lignes citées et adapte. Les adaptations LMNP (property_id, ingest_transactions, incrémental, pending, un-compte-par-bien) sont détaillées ci-dessous avec code complet.

---

### Task 1 : Seam mock/live + config secrets + données mock + /status

**Files:**
- Create: `backend/api/services/banking_service.py`
- Modify: `.gitignore`
- Test: `backend/tests/test_banking_seam.py`

**Interfaces:**
- Produces : `is_live() -> bool`, `status() -> dict`, `_MOCK_ASPSPS`, `_MOCK_ACCOUNTS`, `_mock_raw_transactions(account_uid) -> list[dict]`.

**Contexte :** copie la structure de `~/Claude/compta_sasu/backend/services/banking.py` : config (l.12-17 de leur config), `_pyjwt()` (l.86-93), `_key_path()`/`_load_private_key()` (l.100-117), `is_live()` (l.120-131), `status()` (l.134-150), mock data (l.256-347). Adapte : lire les env vars directement (LMNP n'a pas de config central).

- [ ] **Step 1 : Test d'échec**
```python
# backend/tests/test_banking_seam.py
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
```

- [ ] **Step 2 : Vérifier l'échec** — `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_banking_seam.py -q` → FAIL (module absent).

- [ ] **Step 3 : Implémenter** `banking_service.py` (partie seam + mock). Lis le blueprint l.44-347 et adapte. Squelette minimal LMNP :
```python
"""Client Enable Banking (mock/live). Étape 5. Toute insertion passe par ingest_transactions."""
import os, uuid, logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
_API_BASE = "https://api.enablebanking.com"

def _app_id() -> str: return os.getenv("ENABLE_BANKING_APP_ID", "")
def _key_path() -> Path: return Path(os.getenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "./secrets/eb_private.pem"))
def _redirect_url() -> str:
    return os.getenv("ENABLE_BANKING_REDIRECT_URL",
                     "http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1")

def _pyjwt():
    try:
        import jwt; return jwt
    except Exception:
        return None

def is_live() -> bool:
    return bool(_app_id()) and _key_path().is_file() and _pyjwt() is not None

def status() -> dict:
    if not _app_id(): return {"live": False, "message": "Mode démo : ENABLE_BANKING_APP_ID manquant"}
    if not _key_path().is_file(): return {"live": False, "message": "Mode démo : clé privée introuvable"}
    if _pyjwt() is None: return {"live": False, "message": "Mode démo : pyjwt non installé"}
    return {"live": True, "message": "Connexion Enable Banking active"}

_MOCK_ASPSPS = [
    {"name": "Mock Bank FR", "country": "FR"},
    {"name": "Boursorama (démo)", "country": "FR"},
]
_MOCK_ACCOUNTS = [
    {"account_uid": "mock-acc-1", "name": "Compte courant démo", "iban_masked": "FR76****0001", "currency": "EUR"},
    {"account_uid": "mock-acc-2", "name": "Compte travaux démo", "iban_masked": "FR76****0002", "currency": "EUR"},
]
def _mock_raw_transactions(account_uid: str) -> list[dict]:
    base = [
        {"external_id": f"{account_uid}-t1", "date": date(2026, 1, 5), "quantite": 390.0, "nom": "LOYER MOCK", "status": "booked"},
        {"external_id": f"{account_uid}-t2", "date": date(2026, 1, 6), "quantite": -60.0, "nom": "CHARGES MOCK", "status": "booked"},
        {"external_id": "fx-shared-777", "date": date(2026, 1, 7), "quantite": 12.5, "nom": "FX MOCK", "status": "booked"},  # partagé entre comptes
        {"external_id": f"{account_uid}-p1", "date": date(2026, 1, 8), "quantite": -9.9, "nom": "PENDING MOCK", "status": "pending"},
    ]
    return base
```
(NB : la transaction `status="pending"` sert au test de filtrage Task 5 ; `fx-shared-777` au test de dédoublonnage composite.)

- [ ] **Step 4 : `.gitignore`** — ajoute (s'ils manquent) :
```
.env
secrets/
*.pem
```

- [ ] **Step 5 : Vérifier PASS** — `PYTHONPATH=$PWD python3 -m pytest backend/tests/test_banking_seam.py -q` → 3 passed.

- [ ] **Step 6 : Commit**
```bash
git add backend/api/services/banking_service.py backend/tests/test_banking_seam.py .gitignore
git commit -m "[REFONTE] feat(back): Enable Banking seam mock/live + données mock + status"
```

---

### Task 2 : Client PSD2 (JWT RS256 + HTTP) + list_aspsps

**Files:**
- Modify: `backend/api/services/banking_service.py`
- Test: `backend/tests/test_banking_seam.py` (ajouts)

**Interfaces:**
- Produces : `list_aspsps(country="FR") -> list[dict]`. En interne : `_make_jwt()`, `_auth_headers()`, `_get(path, params)`, `_post(path, json)`.

**Contexte :** porte `_make_jwt` (blueprint l.157-179), `_auth_headers` (l.182-183), `_get`/`_post` (l.364-379), `list_aspsps` (l.386-397). Le JWT n'est forgé qu'en live ; en mock, `list_aspsps` renvoie `_MOCK_ASPSPS` filtré par pays.

- [ ] **Step 1 : Test d'échec** — ajoute à `test_banking_seam.py` :
```python
def test_list_aspsps_mock_returns_french_banks(monkeypatch):
    monkeypatch.delenv("ENABLE_BANKING_APP_ID", raising=False)
    banks = bs.list_aspsps(country="FR")
    assert len(banks) >= 1
    assert all(b["country"] == "FR" for b in banks)
```

- [ ] **Step 2 : Vérifier l'échec** — `pytest ...::test_list_aspsps_mock_returns_french_banks` → FAIL (fonction absente).

- [ ] **Step 3 : Implémenter** (adapté du blueprint) :
```python
def _make_jwt() -> str:
    jwt = _pyjwt()
    key = _key_path().read_text()
    now = datetime.utcnow()
    payload = {"iss": "enablebanking.com", "aud": "api.enablebanking.com",
               "iat": now, "exp": now + timedelta(hours=1)}
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": _app_id()})

def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_make_jwt()}"}

def _get(path: str, params: dict | None = None) -> dict:
    import requests
    r = requests.get(f"{_API_BASE}{path}", headers=_auth_headers(), params=params or {}, timeout=30)
    r.raise_for_status(); return r.json()

def _post(path: str, json: dict) -> dict:
    import requests
    r = requests.post(f"{_API_BASE}{path}", headers=_auth_headers(), json=json, timeout=30)
    r.raise_for_status(); return r.json()

def list_aspsps(country: str = "FR") -> list[dict]:
    if not is_live():
        return [b for b in _MOCK_ASPSPS if b["country"] == country]
    data = _get("/aspsps", {"country": country})
    return data.get("aspsps", data.get("data", []))
```

- [ ] **Step 4 : Vérifier PASS** — `pytest backend/tests/test_banking_seam.py -q` → tout vert.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/services/banking_service.py backend/tests/test_banking_seam.py
git commit -m "[REFONTE] feat(back): client PSD2 (JWT RS256 + HTTP) + list_aspsps"
```

---

### Task 3 : Flux de connexion — connect (state→property_id) + create_session (preview)

**Files:**
- Modify: `backend/api/services/banking_service.py`
- Test: `backend/tests/test_banking_flow.py`

**Interfaces:**
- Produces :
  `start_auth(property_id: int, aspsp_name: str, country="FR") -> dict` → `{"authorization_url": str, "state": str}` ;
  `create_session(code: str, state: str) -> dict` → `{"session_id": str, "session_valid_until": str(YYYY-MM-DD), "property_id": int, "accounts": [{"account_uid","name","iban_masked","currency"}]}`.
- Le `state` est enregistré en mémoire, associé au `property_id`, et vérifié à `create_session`.

**Contexte :** porte `start_auth` (blueprint l.400-431), `create_session` (l.468-511), le registre de state (`_register_state`/`_verify_state` l.56-79). Adapte : associer `state -> property_id` (dict), et exposer `property_id` + `session_valid_until` dans le retour de `create_session`.

- [ ] **Step 1 : Test d'échec**
```python
# backend/tests/test_banking_flow.py
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
```

- [ ] **Step 2 : Vérifier l'échec** — `pytest backend/tests/test_banking_flow.py -q` → FAIL.

- [ ] **Step 3 : Implémenter** :
```python
_pending_states: dict[str, int] = {}  # state -> property_id (mémoire process, mono-poste)

def _register_state(state: str, property_id: int) -> None:
    if len(_pending_states) > 128: _pending_states.clear()
    _pending_states[state] = property_id

def _pop_state(state: str, strict: bool) -> Optional[int]:
    pid = _pending_states.pop(state, None)
    if pid is None and strict:
        raise ValueError("state OAuth inconnu ou expiré")
    return pid

def start_auth(property_id: int, aspsp_name: str, country: str = "FR") -> dict:
    state = str(uuid.uuid4())
    _register_state(state, property_id)
    if not is_live():
        return {"authorization_url": f"{_redirect_url()}&code=mock-code&state={state}", "state": state}
    valid_until = (datetime.utcnow() + timedelta(days=180)).replace(microsecond=0).isoformat() + "Z"
    body = {"access": {"valid_until": valid_until}, "aspsp": {"name": aspsp_name, "country": country},
            "state": state, "redirect_url": _redirect_url(), "psu_type": "personal"}
    data = _post("/auth", body)
    return {"authorization_url": data["url"], "state": state}

def create_session(code: str, state: str) -> dict:
    pid = _pop_state(state, strict=is_live())
    if pid is None: pid = _pending_states_fallback(state)  # mock tolérant
    valid_until = (date.today() + timedelta(days=180)).isoformat()
    if not is_live():
        return {"session_id": f"mock-sess-{state[:8]}", "session_valid_until": valid_until,
                "property_id": pid, "accounts": _MOCK_ACCOUNTS}
    data = _post("/sessions", {"code": code})
    accounts = [{"account_uid": a["uid"], "name": a.get("name", ""), "iban_masked": a.get("iban", ""),
                 "currency": a.get("currency", "EUR")} for a in data.get("accounts", [])]
    return {"session_id": data["session_id"], "session_valid_until": data.get("valid_until", valid_until),
            "property_id": pid, "accounts": accounts}

def _pending_states_fallback(state: str) -> int:
    # en mock, si le state a été consommé, on ne bloque pas : renvoyer un pid par défaut de test est interdit ;
    # le test passe toujours le state fraîchement créé. Lever si vraiment absent.
    raise ValueError("state introuvable")
```
(Note : en mock `_pop_state` n'est pas strict, mais le pid vient du registre ; le test crée le state juste avant.)

- [ ] **Step 4 : Vérifier PASS** — `pytest backend/tests/test_banking_flow.py -q` → 2 passed.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/services/banking_service.py backend/tests/test_banking_flow.py
git commit -m "[REFONTE] feat(back): flux connexion Enable Banking (connect + create_session)"
```

---

### Task 4 : Sélection d'un compte → upsert bank_accounts + migration champs d'affichage

**Files:**
- Modify: `backend/api/services/banking_service.py`, `backend/database/models.py`
- Create: `backend/database/migrations/add_bank_account_display_fields.py`
- Test: `backend/tests/test_banking_flow.py` (ajouts)

**Interfaces:**
- Consumes : `create_session` (Task 3).
- Produces : `select_account(db, property_id, account_uid, session_id, session_valid_until, aspsp_name, account_name, iban_masked, currency) -> BankAccount` (upsert UN compte par bien) ; `list_connections(db, property_id) -> list[BankAccount]` ; `disconnect(db, account_id) -> bool`.
- Nouveaux champs `BankAccount` : `account_name (String)`, `currency (String(3))`, `bank_balance (EuroCents nullable)`.

- [ ] **Step 1 : Test d'échec**
```python
# ajouts test_banking_flow.py
from backend.database.models import Property, BankAccount

def test_select_account_upserts_one_per_property(db_session):
    prop = Property(name="EB-Select"); db_session.add(prop); db_session.flush()
    from backend.api.services import banking_service as bs
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
```

- [ ] **Step 2 : Vérifier l'échec** — FAIL (champs + fonction absents).

- [ ] **Step 3 : Modèle + service** — dans `models.py`, classe `BankAccount`, ajoute après `iban_masked` :
```python
    account_name = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=True)
    bank_balance = Column(EuroCents, nullable=True)
```
Dans `banking_service.py` :
```python
from sqlalchemy.orm import Session
from backend.database.models import BankAccount

def select_account(db: Session, property_id: int, account_uid: str, session_id: str,
                   session_valid_until: str, aspsp_name: str, account_name: str,
                   iban_masked: str, currency: str) -> BankAccount:
    from datetime import date as _date
    existing = db.query(BankAccount).filter(BankAccount.property_id == property_id).first()
    acc = existing or BankAccount(property_id=property_id)
    acc.eb_account_uid = account_uid
    acc.eb_session_id = session_id
    acc.session_valid_until = _date.fromisoformat(session_valid_until) if session_valid_until else None
    acc.bank_name = aspsp_name
    acc.account_name = account_name
    acc.iban_masked = iban_masked
    acc.currency = currency
    if not existing: db.add(acc)
    db.commit(); db.refresh(acc)
    return acc

def list_connections(db: Session, property_id: int) -> list[BankAccount]:
    return db.query(BankAccount).filter(BankAccount.property_id == property_id).all()

def disconnect(db: Session, account_id: int) -> bool:
    acc = db.get(BankAccount, account_id)
    if not acc: return False
    db.delete(acc); db.commit(); return True  # conserve les transactions (account_id nullable)
```

- [ ] **Step 4 : Migration** — crée `backend/database/migrations/add_bank_account_display_fields.py` (modèle : `add_ingestion_fields.py`), idempotente via `PRAGMA table_info`, ajoute les 3 colonnes à `bank_accounts` (`account_name VARCHAR(255)`, `currency VARCHAR(3)`, `bank_balance INTEGER`). Backup `.db` avant, exécute sur prod.

- [ ] **Step 5 : Vérifier PASS + suite** — `pytest backend/tests/test_banking_flow.py backend/tests -q` → vert.

- [ ] **Step 6 : Commit**
```bash
git add backend/api/services/banking_service.py backend/database/models.py backend/database/migrations/add_bank_account_display_fields.py backend/tests/test_banking_flow.py
git commit -m "[REFONTE] feat(back): sélection compte (upsert 1/bien) + champs d'affichage bank_accounts"
```

---

### Task 5 : Moteur de synchro → ingest_transactions (incrémental, pending, SAVEPOINT)

**Files:**
- Modify: `backend/api/services/banking_service.py`
- Test: `backend/tests/test_banking_sync.py`

**Interfaces:**
- Consumes : `ingest_transactions(db, property_id, account_id, rows, source)` (étape 4), `_mock_raw_transactions`.
- Produces : `sync_account(db, bank_account) -> dict` et `sync_property(db, property_id) -> dict` → `{account_id: {inserted, deduplicated, errors}}`.

**Contexte :** porte l'esprit de `sync()` (blueprint l.577-685) MAIS remplace l'insertion directe + logique SASU par `ingest_transactions`. Corrige `date_from` figé → fenêtre incrémentale (`last_sync_at`) ; filtre `status == "pending"` ; SAVEPOINT par compte.

- [ ] **Step 1 : Test d'échec**
```python
# backend/tests/test_banking_sync.py
from datetime import date
from backend.database.models import Property, BankAccount, Transaction
from backend.api.services import banking_service as bs

def _seed(db_session):
    prop = Property(name="EB-Sync"); db_session.add(prop); db_session.flush()
    acc = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-1", bank_name="Mock", currency="EUR")
    db_session.add(acc); db_session.commit()
    return prop, acc

def test_sync_inserts_booked_ignores_pending(db_session):
    prop, acc = _seed(db_session)
    res = bs.sync_account(db_session, acc)
    txs = db_session.query(Transaction).filter(Transaction.property_id == prop.id).all()
    noms = {t.nom for t in txs}
    assert "LOYER MOCK" in noms
    assert "PENDING MOCK" not in noms          # pending filtré
    assert all(t.source == "api" for t in txs)

def test_sync_is_incremental_no_dup_on_second_run(db_session):
    prop, acc = _seed(db_session)
    bs.sync_account(db_session, acc)
    n1 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    bs.sync_account(db_session, acc)           # 2e passe
    n2 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    assert n1 == n2                            # dédoublonnage (account_id, external_id)

def test_sync_fx_shared_id_scoped_by_account(db_session):
    prop, acc1 = _seed(db_session)
    acc2 = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-2", bank_name="Mock", currency="EUR")
    # note : un compte par bien en usage réel ; ici 2 comptes pour tester le scoping FX
    db_session.add(acc2); db_session.commit()
    bs.sync_account(db_session, acc1)
    bs.sync_account(db_session, acc2)
    fx = db_session.query(Transaction).filter(Transaction.nom == "FX MOCK").all()
    assert len(fx) == 2                        # même external_id mais 2 account_id → 2 lignes distinctes
```

- [ ] **Step 2 : Vérifier l'échec** — FAIL.

- [ ] **Step 3 : Implémenter** :
```python
def _normalize(raw: dict) -> dict:
    return {"date": raw["date"], "quantite": float(raw["quantite"]),
            "nom": raw["nom"], "external_id": raw["external_id"]}

def _fetch_raw(bank_account, since) -> list[dict]:
    if not is_live():
        return _mock_raw_transactions(bank_account.eb_account_uid)
    # live : pagination continuation_key, fenêtre depuis `since` (last_sync_at), à implémenter au branchement réel
    out, params = [], {"date_from": since.isoformat() if since else "2020-01-01"}
    while True:
        data = _get(f"/accounts/{bank_account.eb_account_uid}/transactions", params)
        out.extend(data.get("transactions", []))
        cont = data.get("continuation_key")
        if not cont: break
        params["continuation_key"] = cont
    return out

def sync_account(db, bank_account) -> dict:
    from backend.api.services.ingestion_service import ingest_transactions
    since = bank_account.last_sync_at.date() if bank_account.last_sync_at else None
    raw = _fetch_raw(bank_account, since)
    rows = [_normalize(r) for r in raw if r.get("status") != "pending"]   # pending filtré
    try:
        with db.begin_nested():                                          # SAVEPOINT par compte
            res = ingest_transactions(db, bank_account.property_id, bank_account.id, rows, "api")
            bank_account.last_sync_at = datetime.utcnow()
        db.commit()
        return {"account_id": bank_account.id, **res, "errors": []}
    except Exception as e:
        db.rollback()
        logger.error(f"[banking] sync compte {bank_account.id} échec: {e}")
        return {"account_id": bank_account.id, "inserted": 0, "deduplicated": 0, "errors": [str(e)]}

def sync_property(db, property_id: int) -> dict:
    accounts = db.query(BankAccount).filter(BankAccount.property_id == property_id).all()
    return {a.id: sync_account(db, a) for a in accounts}
```
(Note : `ingest_transactions` commit déjà en interne — le `begin_nested`/SAVEPOINT isole le compte ; en cas d'échec on rollback et on continue. En mock, le filtrage pending et le dédoublonnage sont pleinement exercés.)

- [ ] **Step 4 : Vérifier PASS** — `pytest backend/tests/test_banking_sync.py -q` → 3 passed.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/services/banking_service.py backend/tests/test_banking_sync.py
git commit -m "[REFONTE] feat(back): synchro Enable Banking → ingest_transactions (incrémental, pending, SAVEPOINT)"
```

---

### Task 6 : Routes /api/banking (property-scoped) + enregistrement

**Files:**
- Create: `backend/api/routes/banking.py`
- Modify: `backend/api/main.py`
- Test: `backend/tests/test_banking_routes.py`

**Interfaces:**
- Consumes : toutes les fonctions du service (Tasks 1-5).
- Produces : endpoints §10 de la spec.

- [ ] **Step 1 : Test d'échec**
```python
# backend/tests/test_banking_routes.py
from backend.database.models import Property

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
```

- [ ] **Step 2 : Vérifier l'échec** — FAIL (404).

- [ ] **Step 3 : Implémenter** `backend/api/routes/banking.py` (Pydantic bodies + endpoints appelant le service ; property_id explicite ; erreurs remontées). Endpoints : `GET /status`, `GET /aspsps`, `POST /connect`, `POST /sessions`, `POST /connections/select`, `GET /connections`, `POST /sync`, `DELETE /connections/{account_id}`. Le `POST /sync` refuse proprement si `not is_live()` **côté données réelles** — mais expose le résultat mock aux tests via le service (voir garde UI). Modèles : `ConnectIn{property_id, aspsp_name}`, `SessionIn{code, state}`, `SelectIn{property_id, account_uid, session_id, session_valid_until, aspsp_name, account_name, iban_masked, currency}`, `SyncIn{property_id}`.
   Dans `main.py` : `from backend.api.routes import banking` + `app.include_router(banking.router, prefix="/api", tags=["banking"])`.

- [ ] **Step 4 : Vérifier PASS + suite** — `pytest backend/tests/test_banking_routes.py backend/tests -q` → vert ; `python3 -c "import backend.api.main"` OK.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/banking.py backend/api/main.py backend/tests/test_banking_routes.py
git commit -m "[REFONTE] feat(back): routes /api/banking (property-scoped)"
```

---

### Task 7 : Frontend — client bankingAPI + onglet Paramètres (statut, connexion, retour auto, sélection)

**Files:**
- Modify: `frontend/src/api/client.ts`, `frontend/src/components/Navigation.tsx`, `frontend/app/dashboard/transactions/page.tsx`
- Create: `frontend/src/components/ParametresScreen.tsx`
- Test: `frontend/__tests__/parametres.test.tsx`

**Interfaces:**
- Consumes : endpoints Task 6, `useProperty()`/`activeProperty`.
- Produces : `bankingAPI.status/aspsps/connect/createSession/selectAccount/connections/sync/disconnect`.

**Contexte :** lis `~/Claude/compta_sasu/frontend/app/banking/page.tsx` pour la structure (cards statut/connexion/comptes), `frontend/src/components/InboxScreen.tsx` pour le style (bannière role=alert, navy #1e3a5f), `Navigation.tsx` pour ajouter l'onglet.

- [ ] **Step 1 : Client** — dans `client.ts`, ajoute `bankingAPI` (méthodes ci-dessus, `fetchAPI`, `property_id` en query pour GET / body pour POST).
- [ ] **Step 2 : Onglet** — dans `Navigation.tsx`, ajoute `{ name: 'Paramètres', href: '/dashboard/transactions?tab=parametres' }` + la branche `tabParam === 'parametres'` dans la logique active. Dans `page.tsx`, rends `{tab==='parametres' && <ParametresScreen/>}`.
- [ ] **Step 3 : ParametresScreen** — composant, cadré par `activeProperty` :
  - Card **statut** (appelle `bankingAPI.status`, badge live/mock + message).
  - Card **connecter** : liste ASPSP (`bankingAPI.aspsps`), bouton par banque → `bankingAPI.connect({property_id, aspsp_name})` → `window.location.href = authorization_url`.
  - **Retour auto** : au montage, si l'URL contient `?eb_callback=1&code=...&state=...`, appelle `bankingAPI.createSession({code, state})`, affiche la liste des comptes (preview), l'utilisateur en **sélectionne un** → `bankingAPI.selectAccount({...})` → recharge les connexions + nettoie l'URL.
  - Erreurs en bannière `role="alert"`.
- [ ] **Step 4 : Test Jest** — `parametres.test.tsx` : mock `bankingAPI`, monte `ParametresScreen`, vérifie que `status` est appelé au montage et que cliquer une banque appelle `connect` avec le bon `property_id`. (Mock `window.location`.)
- [ ] **Step 5 : Vérifier** — `cd frontend && npm test -- --watchAll=false` + `npm run build` → verts.
- [ ] **Step 6 : Commit**
```bash
git add frontend/src/api/client.ts frontend/src/components/Navigation.tsx frontend/app/dashboard/transactions/page.tsx frontend/src/components/ParametresScreen.tsx frontend/__tests__/parametres.test.tsx
git commit -m "[REFONTE] feat(front): onglet Paramètres — connexion Enable Banking (retour auto + sélection)"
```

---

### Task 8 : Frontend — carte compte (solde/synchro/échéance + alerte J‑30), synchro, déconnexion + golden v5

**Files:**
- Modify: `frontend/src/components/ParametresScreen.tsx`
- Test: `frontend/__tests__/parametres.test.tsx` (ajouts)

**Interfaces:**
- Consumes : `bankingAPI.connections/sync/disconnect/status`.

- [ ] **Step 1 : Carte compte connecté** — pour le compte lié (`bankingAPI.connections`), affiche nom, IBAN masqué, solde banque, dernière synchro, **échéance consentement**. Si `session_valid_until` est à ≤ 30 jours, bandeau orange « consentement à renouveler » + bouton relançant `connect`.
- [ ] **Step 2 : Synchroniser** — bouton `bankingAPI.sync({property_id})` → recharge la liste des transactions + la carte ; affiche compteurs + erreurs par compte en bannière. **Désactivé si `status.live === false`** (mode démo → texte « connecte tes credentials pour synchroniser »).
- [ ] **Step 3 : Déconnecter** — bouton (avec `confirm()`) → `bankingAPI.disconnect(account_id)` → recharge (les transactions restent).
- [ ] **Step 4 : Tests Jest** — le bouton Synchroniser est **disabled** quand `status.live===false` ; l'alerte J‑30 apparaît quand `session_valid_until` est proche ; `disconnect` appelle l'API. (Valeurs de dates fixes.)
- [ ] **Step 5 : Vérifier** — `cd frontend && npm test -- --watchAll=false` + `npm run build` → verts.
- [ ] **Step 6 : Golden v5** — extraire le tag de référence AVANT tout branchement réel (backend :8000 sur code courant) :
```bash
PYTHONPATH=$PWD python3 backend/scripts/golden_master.py --extract --tag v5-avant-enable-banking
PYTHONPATH=$PWD python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel
PYTHONPATH=$PWD python3 backend/scripts/check_rules_no_regression.py
```
Attendu : extraction OK ; `v4` toujours « Aucune différence détectée. OK. » (le portage n'a rien changé aux données réelles) ; non-régression 0.
(Vérifie la syntaxe exacte d'extraction dans `golden_master.py --help` ou l'usage existant ; si le flag diffère, adapte.)
- [ ] **Step 7 : Commit**
```bash
git add frontend/src/components/ParametresScreen.tsx frontend/__tests__/parametres.test.tsx
git commit -m "[REFONTE] feat(front): carte compte + synchro + alerte J-30 (garde mock) + golden v5"
```

---

## Livrable de fin d'étape

- Service `banking_service.py` (mock/live) + routes `/api/banking` property-scoped.
- Onglet Paramètres : connexion (retour auto) + sélection d'un compte/bien + carte compte + synchro manuelle (désactivée en mock) + alerte J‑30.
- Synchro → `ingest_transactions(source="api")`, incrémentale, pending filtrées, SAVEPOINT par compte, dédoublonnage composite (FX géré).
- Secrets 100% côté Louis (`.gitignore` couvre `.env`/`secrets/`/`*.pem`) ; app en mock sans credentials.
- Tests mock verts ; golden v4 = 0 ; non-régression 0 ; tag `v5-avant-enable-banking` extrait.
- Prêt : Louis met sa clé + app_id, connecte sa vraie banque via l'onglet Paramètres, synchronise.
