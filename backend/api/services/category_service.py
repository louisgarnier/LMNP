"""Référentiel de catégories (étape 2 refonte) : résolution triple → Category."""
from sqlalchemy.orm import Session
from backend.database.models import Category, CategoryGroup

NATURE_BY_LABEL = {
    "Produits": "produits",
    "Charges Déductibles": "charges_deductibles",
    "Emprunt": "emprunt",
    "Actif": "actif",
    "Passif": "passif",
}
LABEL_BY_NATURE = {v: k for k, v in NATURE_BY_LABEL.items()}


def resolve_category(db: Session, level_1: str, level_2: str, level_3: str):
    nature = NATURE_BY_LABEL.get(level_3)
    if nature is None:
        return None
    return (
        db.query(Category)
        .join(CategoryGroup, Category.group_id == CategoryGroup.id)
        .filter(Category.label == level_1,
                CategoryGroup.label == level_2,
                CategoryGroup.nature == nature)
        .first()
    )


def get_or_create_category(db: Session, level_1: str, level_2: str, level_3: str) -> Category:
    existing = resolve_category(db, level_1, level_2, level_3)
    if existing is not None:
        return existing
    nature = NATURE_BY_LABEL[level_3]  # KeyError volontaire si level_3 illégal
    group = (db.query(CategoryGroup)
             .filter(CategoryGroup.label == level_2, CategoryGroup.nature == nature)
             .first())
    if group is None:
        group = CategoryGroup(label=level_2, nature=nature)
        db.add(group); db.flush()
    category = Category(label=level_1, group_id=group.id, is_custom=True)
    db.add(category); db.flush()
    return category
