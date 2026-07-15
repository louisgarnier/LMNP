from backend.database.models import Category, CategoryGroup
from backend.api.services.mapping_obligatoire_service import validate_mapping


def _seed(db):
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    db.add(Category(label="Encaissement locataire et CAF", group_id=g.id)); db.commit()


def test_valid_triple_resolves(db_session):
    _seed(db_session)
    assert validate_mapping(db_session, "Encaissement locataire et CAF", "Produits", "Produits", property_id=25) is True


def test_unknown_triple_false(db_session):
    _seed(db_session)
    assert validate_mapping(db_session, "Inexistant", "Produits", "Produits", property_id=25) is False
