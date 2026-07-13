"""Rejoue le moteur sur l'historique classé, rapporte les divergences (lecture seule)."""
from sqlalchemy.orm import Session
from backend.database.models import Transaction
from backend.api.services.enrichment_service import _rules_for_property
from backend.api.services.classification_engine import find_matching_rule


def check(db: Session) -> list[dict]:
    divergences = []
    rules_cache = {}
    for tx in db.query(Transaction).filter(Transaction.category_id.isnot(None)).all():
        if tx.property_id not in rules_cache:
            rules_cache[tx.property_id] = _rules_for_property(db, tx.property_id)
        match = find_matching_rule(tx.nom, rules_cache[tx.property_id])
        would_be = match.category_id if match else None
        if would_be != tx.category_id:
            divergences.append({"transaction_id": tx.id, "current": tx.category_id,
                                "would_be": would_be})
    return divergences


if __name__ == "__main__":
    import sys
    from backend.database.connection import SessionLocal
    db = SessionLocal()
    try:
        div = check(db)
        print(f"[non-régression] {len(div)} divergence(s)")
        for d in div[:50]:
            print(f"  tx#{d['transaction_id']}: actuel={d['current']} moteur={d['would_be']}")
        sys.exit(1 if div else 0)
    finally:
        db.close()
