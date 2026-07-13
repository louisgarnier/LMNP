import datetime
from backend.database.models import Transaction, ClassificationRule, Category, CategoryGroup, Property
from backend.scripts.check_rules_no_regression import check


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.flush()
    return c.id


def test_reports_zero_when_rules_reproduce(db_session):
    cat_id = _seed(db_session)
    db_session.add(ClassificationRule(pattern="VIR LOYER", match_type="prefix",
                                      category_id=cat_id, property_id=25,
                                      priority=0, source="migrated"))
    # "VIR LOYER 01" (12 car.) : ratio motif/libellé = 9/12 = 0.75 >= le seuil
    # de similarité 70 % de find_matching_rule (voir MIN_SIMILARITY_RATIO dans
    # classification_engine.py) — un libellé plus long comme "VIR LOYER JANV"
    # (ratio 0.643) ne matcherait pas et casserait ce test.
    tx = Transaction(property_id=25, date=datetime.date(2025, 1, 5), quantite=500.0,
                     nom="VIR LOYER 01", solde=0.0, category_id=cat_id)
    db_session.add(tx); db_session.commit()
    assert check(db_session) == []


def test_reports_divergence(db_session):
    cat_id = _seed(db_session)
    other = Category(label="Autre", group_id=db_session.query(CategoryGroup).first().id)
    db_session.add(other); db_session.flush()
    db_session.add(ClassificationRule(pattern="VIR LOYER", match_type="prefix",
                                      category_id=cat_id, property_id=25,
                                      priority=0, source="migrated"))
    # Même choix de libellé que ci-dessus (ratio 0.75 >= 70 %) pour que la
    # règle matche bien "Loyers" : la divergence testée ici doit venir du
    # category_id actuel erroné ("Autre"), pas d'un non-match du moteur.
    tx = Transaction(property_id=25, date=datetime.date(2025, 1, 5), quantite=500.0,
                     nom="VIR LOYER 01", solde=0.0, category_id=other.id)
    db_session.add(tx); db_session.commit()
    div = check(db_session)
    assert len(div) == 1 and div[0]["transaction_id"] == tx.id
