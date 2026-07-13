"""Tests migration mappings → classification_rules (étape 3 Task 6).

⚠️ Harnais isolé UNIQUEMENT : fixture `db_session` (SQLite en mémoire, voir
conftest.py). Ne jamais importer le sessionmaker de production ni consommer
manuellement le générateur de dépendance DB ici — ce module ne doit jamais
toucher backend/database/lmnp.db (base de production).
"""
from backend.database.models import Mapping, ClassificationRule, Category, CategoryGroup, Property
from backend.scripts.migrate_mappings_to_rules import migrate


def _seed_ref(db):
    db.add(Property(id=25, name="Evry")); db.flush()
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    c = Category(label="Encaissement locataire et CAF", group_id=g.id); db.add(c); db.flush()
    return c.id


def test_migrates_prefix_and_exact(db_session):
    cat_id = _seed_ref(db_session)
    db_session.add_all([
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
        Mapping(property_id=25, nom="VIR STRIPE", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=False, priority=0),
    ]); db_session.commit()

    report = migrate(db_session)
    assert report["unresolved"] == []
    rules = db_session.query(ClassificationRule).order_by(ClassificationRule.pattern).all()
    by_pattern = {r.pattern: r for r in rules}
    assert by_pattern["VIR AIRBNB"].match_type == "prefix"
    assert by_pattern["VIR STRIPE"].match_type == "exact"
    assert all(r.category_id == cat_id and r.property_id == 25 and r.source == "migrated" for r in rules)


def test_unresolved_triple_aborts(db_session):
    _seed_ref(db_session)
    db_session.add(Mapping(property_id=25, nom="X", level_1="Inexistant",
                           level_2="Produits", level_3="Produits",
                           is_prefix_match=True, priority=0)); db_session.commit()
    report = migrate(db_session)
    assert report["unresolved"]           # non vide
    assert db_session.query(ClassificationRule).count() == 0   # rien inséré


def test_strict_ratio_false_for_recurring_debit_patterns(db_session):
    """Bypass historique de la garde 70 % : les motifs PRLV SEPA (et VIR STRIPE,
    couvert ailleurs) migrent avec strict_ratio=False ; les motifs ordinaires
    (ex: VIR AIRBNB) gardent strict_ratio=True."""
    cat_id = _seed_ref(db_session)
    db_session.add_all([
        Mapping(property_id=25, nom="PRLV SEPA FREE TELECOM", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
    ]); db_session.commit()

    report = migrate(db_session)
    assert report["unresolved"] == []
    rules = db_session.query(ClassificationRule).all()
    by_pattern = {r.pattern: r for r in rules}
    assert by_pattern["PRLV SEPA FREE TELECOM"].strict_ratio is False
    assert by_pattern["VIR AIRBNB"].strict_ratio is True
    assert all(r.category_id == cat_id and r.property_id == 25 for r in rules)


def test_dedup_identical_rules(db_session):
    """Doublon de RÈGLE (pas de mapping) : deux `nom` bruts distincts
    ("VIR AIRBNB" et "VIR AIRBNB ") passent l'index unique
    `(property_id, nom)` de Mapping (comparaison sur la chaîne brute), mais
    `.strip()` produit le même pattern "VIR AIRBNB" → une seule règle créée,
    l'autre est comptée dans `deduped`."""
    cat_id = _seed_ref(db_session)
    db_session.add_all([
        Mapping(property_id=25, nom="VIR AIRBNB", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
        Mapping(property_id=25, nom="VIR AIRBNB ", level_1="Encaissement locataire et CAF",
                level_2="Produits", level_3="Produits", is_prefix_match=True, priority=0),
    ])
    db_session.commit()
    report = migrate(db_session)
    assert report["deduped"] == 1
    assert db_session.query(ClassificationRule).filter_by(pattern="VIR AIRBNB", property_id=25).count() == 1
