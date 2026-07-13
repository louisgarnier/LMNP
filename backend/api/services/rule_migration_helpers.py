"""Helpers de migration mappings → classification_rules."""
from sqlalchemy.orm import Session

from backend.api.services.category_service import resolve_category


def resolve_category_id(db: Session, level_1: str, level_2: str, level_3: str | None) -> int | None:
    """Résout un triplet de mapping vers un category_id via le référentiel étape 2.

    level_1 = label de catégorie, level_2 = label de groupe, level_3 = nature (libellé).
    Aucune création : renvoie None si le triplet n'existe pas.
    """
    cat = resolve_category(db, level_1, level_2, level_3)
    return cat.id if cat is not None else None
