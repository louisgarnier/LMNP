from backend.database.models import Category, CategoryGroup
from backend.api.services.rule_migration_helpers import resolve_category_id


def _seed(db):
    grp = CategoryGroup(label="Produits", nature="produits")
    db.add(grp); db.flush()
    cat = Category(label="Encaissement locataire et CAF", group_id=grp.id)
    db.add(cat); db.commit()
    return cat.id


def test_resolves_known_triple(db_session):
    cat_id = _seed(db_session)
    # level_3 "Produits" → nature "produits" via NATURE_BY_LABEL
    got = resolve_category_id(db_session, "Encaissement locataire et CAF", "Produits", "Produits")
    assert got == cat_id


def test_unknown_triple_returns_none(db_session):
    _seed(db_session)
    assert resolve_category_id(db_session, "Inexistant", "Produits", "Produits") is None
