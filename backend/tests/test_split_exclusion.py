from datetime import date
from backend.database.models import Property, Transaction, ClassificationRule, CategoryGroup, Category
from backend.api.utils.balance_utils import recalculate_all_balances


def test_split_parent_excluded_from_balance(db_session):
    prop = Property(name="Excl")
    db_session.add(prop); db_session.flush()
    # parente masquée (ne doit PAS compter), 2 enfants qui la remplacent
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=280.0, nom="MATERA",
                         solde=0.0, source="csv", is_split_parent=True, category_id=None)
    c1 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=450.0, nom="loyer",
                     solde=0.0, source="manual", is_split_parent=False)
    c2 = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=-170.0, nom="agence",
                     solde=0.0, source="manual", is_split_parent=False)
    db_session.add_all([parent, c1, c2]); db_session.flush()
    recalculate_all_balances(db_session, prop.id)
    db_session.refresh(c2)
    # solde final = 450 - 170 = 280 (la parente 280 n'est PAS comptée en plus)
    last = db_session.query(Transaction).filter(
        Transaction.property_id == prop.id, Transaction.is_split_parent == False
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).first()
    assert last.solde == 280.0


def test_validate_all_ignores_split_parent(client, db_session):
    """`POST /api/inbox/validate-all` ne doit PAS classer une ligne parente
    éclatée (`is_split_parent=True`, `category_id=None`), même si son nom
    matche une règle de classification existante — sinon elle réapparaît
    dans le CR/bilan alors que ses enfants y sont déjà (double comptage)."""
    prop = Property(name="ValidateAllExcl")
    db_session.add(prop); db_session.flush()

    group = CategoryGroup(label="Charges test", nature="charges_deductibles")
    db_session.add(group); db_session.flush()
    category = Category(label="Frais agence", group_id=group.id)
    db_session.add(category); db_session.flush()

    # Règle globale (property_id=None) qui matche exactement le nom de la parente masquée.
    rule = ClassificationRule(pattern="MATERA", match_type="exact",
                              category_id=category.id, property_id=None,
                              priority=0, source="manual")
    db_session.add(rule); db_session.flush()

    # Parente masquée : category_id NULL (non classée) mais is_split_parent=True,
    # remplacée par ses enfants (déjà classés, non présents ici).
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 1), quantite=280.0,
                         nom="MATERA", solde=0.0, source="csv",
                         is_split_parent=True, category_id=None)
    db_session.add(parent); db_session.flush()
    parent_id = parent.id

    resp = client.post("/api/inbox/validate-all", params={"property_id": prop.id})
    assert resp.status_code == 200

    db_session.refresh(parent)
    # La parente masquée ne doit JAMAIS être classée automatiquement : elle
    # doit rester category_id=None (comme list_inbox l'exclut déjà).
    assert parent.category_id is None
    assert parent.is_split_parent is True
    assert db_session.get(Transaction, parent_id).category_id is None
