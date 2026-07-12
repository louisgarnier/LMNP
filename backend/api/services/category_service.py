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


def resolve_categories_for_labels(db: Session, labels, property_id: int):
    """Résout une liste de labels `level_1` en un set de `category_id` (étape 2 Task 5).

    Utilisé par la migration de config CR et par les endpoints POST/PUT pour
    poser la liaison `compte_resultat_mapping_categories` à partir des labels
    `level_1_values` (frontend inchangé cette étape).

    Stratégie de résolution (cf. brief Task 5) :
      1. Par label seul s'il est unique dans le référentiel (cas réel : les 56
         labels sont globalement uniques).
      2. Sinon (0 correspondance OU label ambigu) → label non résolu (collecté,
         jamais deviné).

    Étape 2 Task 8 : la désambiguïsation historique via les combos
    `enriched_transactions` (level_2/level_3) a été retirée avec la suppression
    de la table. Les labels du référentiel étant globalement uniques (invariant
    prod, cf. task-8-report), la branche ambiguë n'était jamais atteinte en
    production ; un label ambigu est désormais simplement `unresolved` (journalisé
    par les appelants, jamais deviné). Le `property_id` reste dans la signature
    pour la stabilité de l'API interne.

    Retourne (category_ids: set[int], unresolved: list[str]).
    """
    category_ids = set()
    unresolved = []
    for label in labels:
        matches = db.query(Category).filter(Category.label == label).all()
        if len(matches) == 1:
            category_ids.add(matches[0].id)
        else:
            # 0 correspondance ou ambiguïté (>1) : non résolu, jamais deviné.
            unresolved.append(label)
    return category_ids, unresolved


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
