"""Étape 2 Task 8 : la classification écrit UNIQUEMENT transactions.category_id.

(Ex-« dual-write » Task 4 : la table enriched_transactions a été supprimée en
Task 8 ; category_id est désormais l'unique support de la classification. Nom de
fichier conservé pour la traçabilité de la suite de tests.)

Note d'adaptation par rapport au brief (.superpowers/sdd/task-4-brief.md) :
`enrich_transaction` a la signature réelle `(transaction, db, mappings=None)`
(et non `(db, transaction_id)` comme suggéré dans le pseudo-code du brief) —
les tests ci-dessous utilisent la signature réelle.

Le test de désassignation cible le VRAI chemin de désassignation en masse
(`mapping_obligatoire_service.reset_allowed_mappings`), et non
`update_transaction_classification(level_1=None)` : lecture du code réel montre
que cette dernière traite `level_1=None` (et idem level_2/level_3) comme « ne
pas toucher ce champ », pas comme « effacer » — y compris quand les trois
niveaux sont None simultanément. Seule la suppression du mapping (reset en masse
ou DELETE transaction) désassigne réellement (category_id repassé à NULL).
"""
from datetime import date


def test_enrich_transaction_sets_category_id(db_session):
    from backend.database.models import Property, Transaction, Mapping
    from backend.api.services.enrichment_service import enrich_transaction
    p = Property(name="T"); db_session.add(p); db_session.flush()
    db_session.add(Mapping(property_id=p.id, nom="VIR LOYER",
                           level_1="Encaissement locataire et CAF",
                           level_2="Produits", level_3="Produits",
                           is_prefix_match=False, priority=1))
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                    solde=500.0, property_id=p.id)
    db_session.add(t); db_session.flush()
    enrich_transaction(t, db_session)
    db_session.refresh(t)
    assert t.category_id is not None
    assert t.category.label == "Encaissement locataire et CAF"


def test_reset_allowed_mappings_clears_category_id(db_session):
    """Désassignation en masse (mapping_obligatoire_service.reset_allowed_mappings) :
    quand une combinaison devient interdite, le Mapping associé est supprimé ->
    transactions.category_id doit repasser à NULL (Étape 2 Task 8)."""
    from backend.database.models import Property, Transaction, Mapping, AllowedMapping
    from backend.api.services.enrichment_service import enrich_transaction
    from backend.api.services.mapping_obligatoire_service import reset_allowed_mappings

    p = Property(name="T"); db_session.add(p); db_session.flush()
    db_session.add(AllowedMapping(property_id=p.id,
                                   level_1="Encaissement locataire et CAF",
                                   level_2="Produits", level_3="Produits",
                                   is_hardcoded=False))
    db_session.add(Mapping(property_id=p.id, nom="VIR LOYER",
                           level_1="Encaissement locataire et CAF",
                           level_2="Produits", level_3="Produits",
                           is_prefix_match=False, priority=1))
    t = Transaction(date=date(2024, 1, 5), quantite=500.0, nom="VIR LOYER",
                    solde=500.0, property_id=p.id)
    db_session.add(t); db_session.flush()

    enrich_transaction(t, db_session)
    db_session.refresh(t)
    assert t.category_id is not None  # pré-condition : bien classifiée avant reset

    reset_allowed_mappings(db_session, p.id)
    db_session.refresh(t)

    assert t.category_id is None


def test_manual_classification_new_combo_creates_custom_category(db_session):
    """update_transaction_classification avec une combinaison nouvelle (absente du
    référentiel categories/category_groups) doit créer une Category is_custom=True
    via get_or_create_category, et synchroniser transactions.category_id dessus."""
    from backend.database.models import Property, Transaction, Category
    from backend.api.services.enrichment_service import update_transaction_classification

    p = Property(name="T"); db_session.add(p); db_session.flush()
    t = Transaction(date=date(2024, 2, 1), quantite=-42.0, nom="DIVERS",
                    solde=100.0, property_id=p.id)
    db_session.add(t); db_session.flush()

    update_transaction_classification(
        db_session, t,
        level_1="Nouvelle Catégorie Perso",
        level_2="Groupe Perso",
        level_3="Charges Déductibles",
    )
    db_session.refresh(t)

    assert t.category_id is not None
    cat = db_session.query(Category).filter(Category.id == t.category_id).first()
    assert cat.label == "Nouvelle Catégorie Perso"
    assert cat.is_custom is True
