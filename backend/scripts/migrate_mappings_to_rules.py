"""Migration mappings → classification_rules (sans reclasser l'historique)."""
from sqlalchemy.orm import Session
from backend.database.models import Mapping, ClassificationRule
from backend.api.services.rule_migration_helpers import resolve_category_id


def migrate(db: Session) -> dict:
    mappings = db.query(Mapping).all()
    unresolved = []
    resolved = []  # (pattern, match_type, category_id, property_id, priority)
    for m in mappings:
        cat_id = resolve_category_id(db, m.level_1, m.level_2, m.level_3)
        if cat_id is None:
            unresolved.append((m.id, m.level_1, m.level_2, m.level_3))
            continue
        match_type = "prefix" if m.is_prefix_match else "exact"
        resolved.append((m.nom.strip(), match_type, cat_id, m.property_id, m.priority or 0))

    if unresolved:
        return {"created": 0, "deduped": 0, "unresolved": unresolved}

    seen = set()
    created = deduped = 0
    for pattern, match_type, cat_id, pid, prio in resolved:
        key = (pattern, match_type, cat_id, pid)
        if key in seen:
            deduped += 1
            continue
        seen.add(key)
        # L'ancien moteur (enrichment_service) contournait sa garde de similarité
        # 70 % pour les motifs de prélèvement récurrent : ces deux littéraux ne
        # doivent exister QUE dans ce script one-shot, jamais dans le moteur.
        strict_ratio = not ("PRLV SEPA" in pattern or pattern == "VIR STRIPE")
        db.add(ClassificationRule(pattern=pattern, match_type=match_type,
                                  category_id=cat_id, property_id=pid,
                                  priority=prio, source="migrated",
                                  strict_ratio=strict_ratio))
        created += 1
    db.commit()
    return {"created": created, "deduped": deduped, "unresolved": []}


if __name__ == "__main__":
    from backend.database.connection import SessionLocal
    db = SessionLocal()
    try:
        report = migrate(db)
        print(f"[migration] créées={report['created']} dédupliquées={report['deduped']} "
              f"non résolues={len(report['unresolved'])}")
        for u in report["unresolved"]:
            print(f"  NON RÉSOLU mapping#{u[0]}: {u[1]} / {u[2]} / {u[3]}")
    finally:
        db.close()
