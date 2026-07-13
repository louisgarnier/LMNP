"""API `/api/inbox` : file d'attente de classification en un clic.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Étape 3 Task 9 : liste les transactions non classées (`category_id IS NULL`)
avec une suggestion (meilleure règle sous seuil RELÂCHÉ, sans la garde 70 %
de `find_matching_rule`) et une règle proposée (`derive_prefix_pattern`,
Task 4). Permet de valider une transaction seule (avec ou sans création de
règle) ou de valider en masse par groupe (motif proposé, catégorie
suggérée).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Transaction, ClassificationRule
from backend.api.services.enrichment_service import _rules_for_property
from backend.api.services.classification_engine import (
    find_matching_rule, rule_matches, derive_prefix_pattern, MIN_SIMILARITY_RATIO,
)

router = APIRouter()


class RuleSpec(BaseModel):
    pattern: str
    match_type: str
    property_id: int | None = None


class ValidateIn(BaseModel):
    transaction_id: int
    category_id: int
    rule: RuleSpec | None = None


def _suggestion(db, tx, rules):
    # suggestion = meilleure règle "seuil relâché" : on cherche le plus long motif
    # préfixe/contient présent dans le libellé, sans imposer les 70 %.
    best = None
    for r in rules:
        if r.match_type == "exact" and tx.nom.strip() == r.pattern.strip():
            return r.category_id
        if r.match_type in ("prefix", "contains") and r.pattern.strip() in tx.nom:
            if best is None or len(r.pattern) > len(best.pattern):
                best = r
    return best.category_id if best else None


@router.get("/inbox")
def list_inbox(property_id: int, db: Session = Depends(get_db)):
    rules = _rules_for_property(db, property_id)
    items = []
    txs = (db.query(Transaction)
           .filter(Transaction.property_id == property_id, Transaction.category_id.is_(None))
           .order_by(Transaction.date).all())
    for t in txs:
        pattern, match_type = derive_prefix_pattern(t.nom)
        items.append({"transaction_id": t.id, "nom": t.nom, "date": t.date.isoformat(),
                      "montant": t.quantite, "suggestion": {"category_id": _suggestion(db, t, rules)},
                      "proposed_rule": {"pattern": pattern, "match_type": match_type}})
    return {"items": items}


@router.post("/inbox/validate")
def validate(body: ValidateIn, db: Session = Depends(get_db)):
    tx = db.get(Transaction, body.transaction_id)
    if not tx:
        raise HTTPException(404, "Transaction introuvable")
    tx.category_id = body.category_id
    if body.rule is not None:
        db.add(ClassificationRule(pattern=body.rule.pattern.strip(),
                                  match_type=body.rule.match_type,
                                  category_id=body.category_id,
                                  property_id=body.rule.property_id if body.rule.property_id is not None else tx.property_id,
                                  priority=0, source="auto_from_inbox"))
    db.commit()
    return {"transaction_id": tx.id, "category_id": tx.category_id}


@router.post("/inbox/validate-all")
def validate_all(property_id: int, db: Session = Depends(get_db)):
    rules = _rules_for_property(db, property_id)
    txs = (db.query(Transaction)
           .filter(Transaction.property_id == property_id, Transaction.category_id.is_(None)).all())
    groups: dict[tuple, dict] = {}
    for t in txs:
        cat = _suggestion(db, t, rules)
        if cat is None:
            continue                      # ambiguë : reste dans l'inbox
        pattern, match_type = derive_prefix_pattern(t.nom)
        key = (pattern, match_type, cat)
        groups.setdefault(key, {"tx": [], "category_id": cat,
                                "pattern": pattern, "match_type": match_type})
        groups[key]["tx"].append(t)
    created = validated = 0
    for g in groups.values():
        db.add(ClassificationRule(pattern=g["pattern"], match_type=g["match_type"],
                                  category_id=g["category_id"], property_id=property_id,
                                  priority=0, source="auto_from_inbox"))
        created += 1
        for t in g["tx"]:
            t.category_id = g["category_id"]; validated += 1
    db.commit()
    return {"rules_created": created, "transactions_validated": validated}
