"""
API routes for banking (Enable Banking, property-scoped). Étape 5.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.services import banking_service

router = APIRouter()


class ConnectIn(BaseModel):
    property_id: int
    aspsp_name: str


class SessionIn(BaseModel):
    code: str
    state: str


class SelectIn(BaseModel):
    property_id: int
    account_uid: str
    session_id: str
    session_valid_until: str
    aspsp_name: str
    account_name: str
    iban_masked: str
    currency: str


class SyncIn(BaseModel):
    property_id: int


@router.get("/banking/status")
async def get_status():
    """Statut de la connexion Enable Banking (mode démo/live)."""
    return banking_service.status()


@router.get("/banking/aspsps")
async def get_aspsps(country: str = Query("FR")):
    """Liste des banques (ASPSP) disponibles pour un pays."""
    return banking_service.list_aspsps(country)


@router.post("/banking/connect")
async def connect(body: ConnectIn):
    """Démarre le flux d'autorisation OAuth pour un bien + une banque."""
    return banking_service.start_auth(body.property_id, body.aspsp_name)


@router.post("/banking/sessions")
async def create_session(body: SessionIn):
    """Échange le code OAuth contre une session Enable Banking (liste des comptes)."""
    try:
        return banking_service.create_session(body.code, body.state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/banking/connections/select")
async def select_connection(body: SelectIn, db: Session = Depends(get_db)):
    """Sélectionne un compte bancaire pour un bien (upsert : un compte par bien)."""
    acc = banking_service.select_account(
        db,
        property_id=body.property_id,
        account_uid=body.account_uid,
        session_id=body.session_id,
        session_valid_until=body.session_valid_until,
        aspsp_name=body.aspsp_name,
        account_name=body.account_name,
        iban_masked=body.iban_masked,
        currency=body.currency,
    )
    return _serialize_account(acc)


@router.get("/banking/connections")
async def get_connections(property_id: int = Query(...), db: Session = Depends(get_db)):
    """Liste les comptes bancaires connectés pour un bien."""
    accounts = banking_service.list_connections(db, property_id)
    return [_serialize_account(a) for a in accounts]


@router.post("/banking/sync")
async def sync(body: SyncIn, db: Session = Depends(get_db)):
    """Synchronise les comptes bancaires d'un bien (fetch + ingestion des transactions).

    Garde anti-pollution : refuse en mode démo (mock) pour ne jamais insérer de
    fausses transactions mock dans des données réelles via un appel direct à
    l'endpoint (le frontend désactive déjà le bouton, mais l'API doit se
    protéger elle-même)."""
    if not banking_service.is_live():
        raise HTTPException(
            status_code=409,
            detail="Synchronisation indisponible en mode démo (connecte tes identifiants Enable Banking)",
        )
    return banking_service.sync_property(db, body.property_id)


@router.delete("/banking/connections/{account_id}")
async def delete_connection(account_id: int, db: Session = Depends(get_db)):
    """Déconnecte un compte bancaire (conserve les transactions déjà importées)."""
    ok = banking_service.disconnect(db, account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return {"deleted": True}


def _serialize_account(acc) -> dict:
    return {
        "id": acc.id,
        "bank_name": acc.bank_name,
        "account_name": acc.account_name,
        "iban_masked": acc.iban_masked,
        "currency": acc.currency,
        "bank_balance": acc.bank_balance,
        "last_sync_at": acc.last_sync_at,
        "session_valid_until": acc.session_valid_until,
        "eb_account_uid": acc.eb_account_uid,
    }
