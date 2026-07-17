import datetime
from backend.database.models import Category, CategoryGroup, Property, Transaction, ClassificationRule


def _seed(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Loyers", group_id=g.id); db.add(c); db.commit()
    return c.id


def test_inbox_lists_unclassified_with_proposed_rule(client, db_session):
    _seed(db_session)
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0,
                               category_id=None)); db_session.commit()
    body = client.get("/api/inbox", params={"property_id": 25}).json()
    assert len(body["items"]) == 1
    it = body["items"][0]
    assert it["proposed_rule"]["pattern"] == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert it["proposed_rule"]["match_type"] == "prefix"


def test_validate_creates_rule_and_classifies(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=540.0,
                     nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={
        "transaction_id": tx.id, "category_id": cat_id,
        "rule": {"pattern": "VIR AIRBNB PAYMENTS LUXEMBOU", "match_type": "prefix", "property_id": 25}})
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    rule = db_session.query(ClassificationRule).filter_by(pattern="VIR AIRBNB PAYMENTS LUXEMBOU").one()
    assert rule.source == "auto_from_inbox"


def test_validate_just_this_one_no_rule(client, db_session):
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR UNIQUE 123", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={"transaction_id": tx.id, "category_id": cat_id})
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id == cat_id
    assert db_session.query(ClassificationRule).count() == 0


def test_validate_all_groups_same_pattern_exact_and_prefix(client, db_session):
    cat_id = _seed(db_session)
    # règle existante qui suggère la même catégorie pour les deux transactions,
    # même si leurs motifs dérivés (exact vs prefix) diffèrent.
    db_session.add(ClassificationRule(pattern="VIR AIRBNB PAYMENTS LUXEMBOU", match_type="prefix",
                                      category_id=cat_id, property_id=None, priority=0,
                                      source="seed"))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=100.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU", solde=0.0, category_id=None))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 29), quantite=200.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROG", solde=0.0,
                               category_id=None))
    db_session.commit()

    r = client.post("/api/inbox/validate-all", params={"property_id": 25})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rules_created"] == 1
    assert body["transactions_validated"] == 2

    db_session.expire_all()
    new_rules = (db_session.query(ClassificationRule)
                 .filter_by(source="auto_from_inbox", pattern="VIR AIRBNB PAYMENTS LUXEMBOU").all())
    assert len(new_rules) == 1
    assert new_rules[0].match_type == "prefix"

    txs = db_session.query(Transaction).filter(Transaction.property_id == 25).all()
    assert len(txs) == 2
    assert all(t.category_id == cat_id for t in txs)


def test_validate_all_skips_none_suggestion(client, db_session):
    _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=10.0,
                     nom="VIR SANS AUCUNE REGLE 999", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()

    r = client.post("/api/inbox/validate-all", params={"property_id": 25})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rules_created"] == 0
    assert body["transactions_validated"] == 0

    db_session.expire_all()
    assert db_session.get(Transaction, tx.id).category_id is None
    assert db_session.query(ClassificationRule).filter_by(source="auto_from_inbox").count() == 0


def test_suggestion_prefix_requires_startswith(client, db_session):
    cat_id = _seed(db_session)
    # le motif du prefix-rule apparaît au milieu du libellé, pas au début :
    # une suggestion "prefix" ne doit pas se rabattre sur un simple "contains".
    db_session.add(ClassificationRule(pattern="AIRBNB PAYMENTS", match_type="prefix",
                                      category_id=cat_id, property_id=None, priority=0,
                                      source="seed"))
    db_session.add(Transaction(property_id=25, date=datetime.date(2025, 6, 28), quantite=50.0,
                               nom="VIR AIRBNB PAYMENTS LUXEMBOU", solde=0.0, category_id=None))
    db_session.commit()

    body = client.get("/api/inbox", params={"property_id": 25}).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["suggestion"]["category_id"] is None


def test_inbox_ne_propose_JAMAIS_le_libelle_complet(client, db_session):
    """Régression du 2026-07-17 : la machine à règles jetables.

    L'inbox appelait `derive_prefix_pattern`, qui se replie sur
    (libellé complet, "exact") dès que le libellé ne se termine pas par une
    référence bancaire. Le 17/07 à 09h08, Louis a classé 6 virements et l'app a
    fabriqué 6 règles de ce type — dont
    « VIR INST GESTION FEVRIER 26 - LG », qui ne matchera JAMAIS le virement du
    mois suivant. 272 des 370 règles de la base sont dans ce cas.

    Ici : aucun historique, et un libellé sans suffixe retirable → il ne doit
    rien être proposé, plutôt qu'une 373e empreinte.
    """
    _seed(db_session)
    db_session.add(Transaction(property_id=25, date=datetime.date(2026, 3, 8), quantite=-525.59,
                               nom="VIR INST GESTION FEVRIER 26 - LG", solde=0.0,
                               category_id=None))
    db_session.commit()
    it = client.get("/api/inbox", params={"property_id": 25}).json()["items"][0]
    assert it["proposed_rule"] is None, (
        f"l'inbox propose encore une règle jetable : {it['proposed_rule']}"
    )


def test_inbox_propose_un_motif_court_quand_l_historique_le_permet(client, db_session):
    """Avec de l'historique, l'inbox doit dégager le motif stable — pas le libellé.

    Les 3 libellés classés ci-dessous n'ont AUCUN préfixe commun (le mois et
    l'ordre des mots changent) : seul un motif tiré de l'historique peut les
    couvrir. C'est le cœur du correctif.
    """
    cat_id = _seed(db_session)
    for nom in ["VIR SEPA GESTION ABNB - AOUT25",
                "VIR INST VIREMENT GESTION DEC25 VH60192084P7UL01",
                "VIR INST ABNB GESTION - LOUIS G VH53242B3KB32Z01"]:
        db_session.add(Transaction(property_id=25, date=datetime.date(2025, 8, 6), quantite=-600.0,
                                   nom=nom, solde=0.0, category_id=cat_id))
    db_session.add(Transaction(property_id=25, date=datetime.date(2026, 3, 8), quantite=-525.59,
                               nom="VIR INST GESTION FEVRIER 26 - LG", solde=0.0, category_id=None))
    db_session.commit()

    it = client.get("/api/inbox", params={"property_id": 25}).json()["items"][0]
    assert it["suggestion"]["category_id"] == cat_id, "la catégorie doit être devinée par ressemblance"
    assert it["proposed_rule"] is not None
    assert it["proposed_rule"]["pattern"] == "GESTION"
    assert it["proposed_rule"]["match_type"] == "contains"
    assert it["proposed_rule"]["matches"] == 3


def test_la_regle_creee_depuis_l_inbox_desactive_la_garde_des_70_pourcent(client, db_session):
    """Sans strict_ratio=False, un motif court est rejeté par le moteur.

    « GESTION » fait 22 % de la longueur de « VIR INST GESTION FEVRIER 26 - LG » :
    la garde de similarité (classification_engine l.22-23) le refuserait, et la
    règle serait créée pour ne jamais servir. C'est cette garde qui a fabriqué
    l'annuaire.
    """
    cat_id = _seed(db_session)
    tx = Transaction(property_id=25, date=datetime.date(2026, 3, 8), quantite=-525.59,
                     nom="VIR INST GESTION FEVRIER 26 - LG", solde=0.0, category_id=None)
    db_session.add(tx); db_session.commit()
    r = client.post("/api/inbox/validate", json={
        "transaction_id": tx.id, "category_id": cat_id,
        "rule": {"pattern": "GESTION", "match_type": "contains", "property_id": 25}})
    assert r.status_code == 200, r.text

    regle = db_session.query(ClassificationRule).filter_by(pattern="GESTION").one()
    assert regle.strict_ratio is False, "la garde des 70 % rendrait cette règle inopérante"

    # Preuve par le moteur : un libellé FUTUR inédit doit matcher.
    from backend.api.services.classification_engine import find_matching_rule
    trouvee = find_matching_rule("VIR INST GESTION SEPTEMBRE 26 - LG CH3W99", [regle])
    assert trouvee is not None and trouvee.category_id == cat_id
