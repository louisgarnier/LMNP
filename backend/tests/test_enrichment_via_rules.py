"""Étape 3 Task 5 : enrichment_service classe via classification_rules
(bien + globales), et non plus via mappings.
"""
from backend.database.models import (
    Transaction, ClassificationRule, Category, CategoryGroup, Property
)
from backend.api.services.enrichment_service import enrich_transaction
import datetime


def _seed_cat(db, label, group_label, nature):
    g = CategoryGroup(label=group_label, nature=nature); db.add(g); db.flush()
    c = Category(label=label, group_id=g.id); db.add(c); db.flush()
    return c.id


def test_enrich_assigns_category_from_matching_rule(db_session):
    db_session.add(Property(id=25, name="Evry")); db_session.flush()
    cat_id = _seed_cat(db_session, "Encaissement locataire et CAF", "Produits", "produits")
    db_session.add(ClassificationRule(pattern="VIR AIRBNB PAYMENTS LUXEMBOU",
                                      match_type="prefix", category_id=cat_id,
                                      property_id=25, priority=0, source="migrated"))
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                     nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0)
    db_session.add(tx); db_session.commit()

    enrich_transaction(tx, db_session)
    assert tx.category_id == cat_id


def test_no_rule_leaves_unclassified(db_session):
    db_session.add(Property(id=25, name="Evry")); db_session.commit()
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR INCONNU", solde=0.0)
    db_session.add(tx); db_session.commit()
    enrich_transaction(tx, db_session)
    assert tx.category_id is None


def test_global_rule_applies_across_properties(db_session):
    db_session.add(Property(id=26, name="colloc")); db_session.flush()
    cat_id = _seed_cat(db_session, "Énergie", "Charges Déductibles", "charges_deductibles")
    db_session.add(ClassificationRule(pattern="PRLV SEPA EDF", match_type="exact",
                                      category_id=cat_id, property_id=None,
                                      priority=0, source="manual"))
    tx = Transaction(property_id=26, date=datetime.date(2025, 3, 1), quantite=-80.0,
                     nom="PRLV SEPA EDF", solde=0.0)
    db_session.add(tx); db_session.commit()
    enrich_transaction(tx, db_session)
    assert tx.category_id == cat_id
