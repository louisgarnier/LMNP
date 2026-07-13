from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.connection import get_db
from backend.database.models import ClassificationRule, Transaction
from backend.api.services.classification_engine import rule_matches

router = APIRouter()


class RuleIn(BaseModel):
    pattern: str
    match_type: str            # exact | prefix | contains
    category_id: int
    property_id: int | None = None
    priority: int = 0


class RuleOut(RuleIn):
    id: int
    source: str


def _tx_count(db, rule_pattern, match_type, property_id):
    q = db.query(Transaction)
    q = q.filter(Transaction.property_id == property_id) if property_id is not None else q
    return sum(1 for t in q.all() if rule_matches(t.nom, rule_pattern, match_type))


@router.get("/rules")
def list_rules(property_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(ClassificationRule)
    if property_id is not None:
        q = q.filter(or_(ClassificationRule.property_id == property_id,
                         ClassificationRule.property_id.is_(None)))
    items = []
    for r in q.all():
        items.append({"id": r.id, "pattern": r.pattern, "match_type": r.match_type,
                      "category_id": r.category_id, "property_id": r.property_id,
                      "priority": r.priority, "source": r.source,
                      "tx_count": _tx_count(db, r.pattern, r.match_type, r.property_id)})
    return {"items": items}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(body: RuleIn, db: Session = Depends(get_db)):
    if body.match_type not in ("exact", "prefix", "contains"):
        raise HTTPException(400, f"match_type invalide: {body.match_type}")
    rule = ClassificationRule(pattern=body.pattern.strip(), match_type=body.match_type,
                              category_id=body.category_id, property_id=body.property_id,
                              priority=body.priority, source="manual")
    db.add(rule); db.commit(); db.refresh(rule)
    return {"id": rule.id}


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, body: RuleIn, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(404, "Règle introuvable")
    rule.pattern = body.pattern.strip(); rule.match_type = body.match_type
    rule.category_id = body.category_id; rule.property_id = body.property_id
    rule.priority = body.priority
    db.commit()
    return {"id": rule.id}


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(404, "Règle introuvable")
    db.delete(rule); db.commit()   # ne déclasse aucune transaction (historique figé)


@router.post("/rules/preview")
def preview_rule(body: RuleIn, db: Session = Depends(get_db)):
    q = db.query(Transaction)
    if body.property_id is not None:
        q = q.filter(Transaction.property_id == body.property_id)
    would_classify, conflicts = 0, []
    for t in q.all():
        if not rule_matches(t.nom, body.pattern, body.match_type):
            continue
        if t.category_id is None:
            would_classify += 1
        elif t.category_id != body.category_id:
            conflicts.append({"transaction_id": t.id, "current_category_id": t.category_id})
    return {"would_classify": would_classify, "conflicts": conflicts}
