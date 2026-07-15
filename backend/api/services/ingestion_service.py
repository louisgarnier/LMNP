"""Point d'entrée unique d'ingestion : CSV, API, manuel. Étape 4."""
import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from backend.database.models import Transaction
from backend.api.services.enrichment_service import enrich_transaction
from backend.api.services.amortization_service import recalculate_transaction_amortization
from backend.api.utils.balance_utils import recalculate_all_balances

logger = logging.getLogger(__name__)


def _is_duplicate(db: Session, property_id: int, account_id: Optional[int],
                  d: date, quantite: float, nom: str, external_id: Optional[str]) -> bool:
    if external_id is not None:
        exists = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.external_id == external_id,
        ).first()
        return exists is not None
    exists = db.query(Transaction).filter(
        Transaction.property_id == property_id,
        Transaction.date == d,
        Transaction.quantite == quantite,   # EuroCents : égalité au centime
        Transaction.nom == nom,
    ).first()
    return exists is not None


def ingest_transactions(db: Session, property_id: int, account_id: Optional[int],
                        rows: list[dict], source: str) -> dict:
    """Normalise → dédoublonne → insère → classe → recalcule soldes + amortissements.
    Retourne {"inserted", "deduplicated", "ids"}. L'appelant gère le commit final
    (enrich_transaction/recalculate_all_balances committent déjà, comme dans l'import CSV)."""
    inserted, deduplicated, new_ids = 0, 0, []
    new_txs = []
    seen_keys = set()   # dédoublonnage intra-lot : la DB (autoflush=False) ne voit pas les lignes du lot en cours
    for r in rows:
        nom = (r["nom"] or "").strip()
        external_id = r.get("external_id")
        local_key = ("ext", account_id, external_id) if external_id is not None \
            else ("row", property_id, r["date"], r["quantite"], nom)
        if local_key in seen_keys or _is_duplicate(db, property_id, account_id, r["date"], r["quantite"], nom, external_id):
            deduplicated += 1
            continue
        seen_keys.add(local_key)
        tx = Transaction(
            property_id=property_id, account_id=account_id,
            date=r["date"], quantite=r["quantite"], nom=nom,
            solde=0.0, source=source, external_id=external_id,
            is_split_parent=False,
        )
        db.add(tx)
        new_txs.append(tx)
        inserted += 1
    db.flush()

    recalculate_all_balances(db, property_id)   # solde correct (exclut is_split_parent — Task 4)

    for tx in new_txs:
        new_ids.append(tx.id)
        enrich_transaction(tx, db)              # pose category_id via règles étape 3
        try:
            recalculate_transaction_amortization(db, tx.id)
        except Exception as e:                  # best-effort, identique à l'import CSV actuel
            logger.warning(f"[ingest] amortissement tx {tx.id} ignoré: {e}")

    db.commit()
    return {"inserted": inserted, "deduplicated": deduplicated, "ids": new_ids}
