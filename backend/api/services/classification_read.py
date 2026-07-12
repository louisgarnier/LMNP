"""Étape 2 Task 7 : lecture de la classification (level_1/2/3) via le référentiel.

Fournit des expressions SQLAlchemy dérivées de `transactions.category_id` →
`categories` → `category_groups`, produisant EXACTEMENT les mêmes valeurs
textuelles que les ex-colonnes `enriched_transactions.level_1/2/3`, afin que
l'API reste byte-identique après la bascule (le frontend ne change pas cette
étape) :

- level_1  == Category.label
- level_2  == CategoryGroup.label
- level_3  == LABEL_BY_NATURE[CategoryGroup.nature]  (expression CASE)
- mois/annee : dérivés de `Transaction.date` (les colonnes
  `enriched_transactions.mois/annee`, des entiers stockés, ne sont plus lues).

Chaque consommateur applique un LEFT JOIN transactions → categories →
category_groups (outer, pour que les transactions non classées — `category_id`
NULL — restent visibles avec des niveaux NULL, reproduisant la sémantique de
l'ancien LEFT JOIN vers `enriched_transactions`).
"""
from sqlalchemy import case, extract

from backend.database.models import Transaction, Category, CategoryGroup
from backend.api.services.category_service import LABEL_BY_NATURE


def level_3_expr():
    """Expression CASE : `category_groups.nature` → label level_3 (ex. 'Actif').

    Renvoie NULL pour une nature inconnue ou une transaction non classée
    (CategoryGroup absent après le LEFT JOIN), comme l'ancien `enriched.level_3`
    NULL pour les transactions non classées."""
    return case(
        {nature: label for nature, label in LABEL_BY_NATURE.items()},
        value=CategoryGroup.nature,
        else_=None,
    )


def category_label_columns():
    """(level_1, level_2, level_3) — expressions colonnes dérivées du référentiel.

    Mêmes valeurs textuelles que les ex-colonnes `enriched_transactions`.
    À utiliser après `join_classification(query)`.
    """
    return (Category.label, CategoryGroup.label, level_3_expr())


def month_expr():
    """Mois (1-12, int) dérivé de `Transaction.date` (ex-`enriched.mois`)."""
    return extract('month', Transaction.date)


def year_expr():
    """Année (int) dérivée de `Transaction.date` (ex-`enriched.annee`)."""
    return extract('year', Transaction.date)


def join_classification(query):
    """Applique les LEFT JOIN transactions → categories → category_groups.

    LEFT (outer) pour conserver les transactions non classées (category_id
    NULL) avec des niveaux NULL — sémantique identique à l'ancien LEFT JOIN
    vers `enriched_transactions`.
    """
    return query.outerjoin(
        Category, Transaction.category_id == Category.id
    ).outerjoin(
        CategoryGroup, Category.group_id == CategoryGroup.id
    )


def levels_for_transaction(transaction):
    """(level_1, level_2, level_3) pour une Transaction ORM, via ses relations.

    Reproduit les ex-colonnes `enriched.level_1/2/3` pour la sérialisation des
    réponses. (None, None, None) pour une transaction non classée."""
    cat = transaction.category
    if cat is None:
        return (None, None, None)
    group = cat.group
    if group is None:
        return (cat.label, None, None)
    return (cat.label, group.label, LABEL_BY_NATURE.get(group.nature))
