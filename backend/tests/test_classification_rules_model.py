from backend.database.models import ClassificationRule, Category, CategoryGroup, Property


def test_classification_rule_roundtrip(db_session):
    # NB : property_id est une FK réelle vers properties.id, contrainte
    # appliquée par la fixture db_session (PRAGMA foreign_keys = ON, comme en
    # prod). On crée donc une Property réelle plutôt que d'utiliser un id
    # littéral arbitraire (25) qui violerait la contrainte FK.
    prop = Property(name="Appartement Evry")
    db_session.add(prop); db_session.flush()

    grp = CategoryGroup(label="Produits", nature="produits")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Encaissement locataire et CAF", group_id=grp.id)
    db_session.add(cat); db_session.flush()

    rule = ClassificationRule(
        pattern="VIR AIRBNB PAYMENTS LUXEMBOU",
        match_type="prefix",
        category_id=cat.id,
        property_id=prop.id,
        priority=0,
        source="migrated",
    )
    db_session.add(rule); db_session.commit()

    got = db_session.query(ClassificationRule).one()
    assert got.pattern == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert got.match_type == "prefix"
    assert got.category_id == cat.id
    assert got.property_id == prop.id     # règle de bien
    assert got.source == "migrated"


def test_global_rule_has_null_property(db_session):
    grp = CategoryGroup(label="Charges Déductibles", nature="charges_deductibles")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Énergie", group_id=grp.id)
    db_session.add(cat); db_session.flush()
    rule = ClassificationRule(pattern="PRLV SEPA EDF", match_type="prefix",
                              category_id=cat.id, property_id=None,
                              priority=0, source="manual")
    db_session.add(rule); db_session.commit()
    assert db_session.query(ClassificationRule).one().property_id is None
