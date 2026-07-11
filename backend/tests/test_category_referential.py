"""Étape 2 Task 2 : référentiel global categories/groups. Harnais isolé."""


def test_models_and_resolution(db_session):
    from backend.database.models import CategoryGroup, Category
    from backend.api.services.category_service import (
        resolve_category, get_or_create_category, NATURE_BY_LABEL)

    g = CategoryGroup(label="Produits", nature=NATURE_BY_LABEL["Produits"])
    db_session.add(g); db_session.flush()
    c = Category(label="Encaissement locataire et CAF", group_id=g.id, is_custom=False)
    db_session.add(c); db_session.flush()

    found = resolve_category(db_session, "Encaissement locataire et CAF", "Produits", "Produits")
    assert found is not None and found.id == c.id
    assert resolve_category(db_session, "Inconnu", "Produits", "Produits") is None

    created = get_or_create_category(db_session, "Nouvelle cat", "Produits", "Produits")
    assert created.is_custom is True and created.group_id == g.id


def test_nature_enum_is_closed():
    from backend.api.services.category_service import NATURE_BY_LABEL
    assert set(NATURE_BY_LABEL.keys()) == {"Produits", "Charges Déductibles", "Emprunt", "Actif", "Passif"}
    assert set(NATURE_BY_LABEL.values()) == {"produits", "charges_deductibles", "emprunt", "actif", "passif"}
