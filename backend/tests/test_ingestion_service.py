from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup, ClassificationRule, BankAccount
from backend.api.services.ingestion_service import ingest_transactions


def _seed_property_with_rule(db_session):
    grp = CategoryGroup(label="Produits", nature="produits")
    db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False)
    db_session.add(cat); db_session.flush()
    prop = Property(name="Ingest-1")
    db_session.add(prop); db_session.flush()
    rule = ClassificationRule(pattern="LOYER", match_type="prefix", category_id=cat.id,
                              property_id=None, priority=0, source="manual", strict_ratio=False)
    db_session.add(rule); db_session.flush()
    return prop, cat


def test_ingest_inserts_and_classifies(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    res = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert res["inserted"] == 1
    assert res["deduplicated"] == 0
    tx = db_session.query(Transaction).filter(Transaction.property_id == prop.id).one()
    assert tx.category_id == cat.id          # classé par la règle
    assert tx.source == "csv"
    assert tx.solde == 390.0                  # solde recalculé


def test_ingest_dedup_fallback_key(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None}]
    ingest_transactions(db_session, prop.id, None, rows, "csv")
    res2 = ingest_transactions(db_session, prop.id, None, rows, "csv")   # même ligne
    assert res2["inserted"] == 0
    assert res2["deduplicated"] == 1
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 1


def test_ingest_dedup_external_id(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [{"date": date(2023, 2, 1), "quantite": 100.0, "nom": "VIR", "external_id": "EB-123"}]
    ingest_transactions(db_session, prop.id, None, rows, "api")
    # même external_id, nom/montant différents → toujours un doublon
    rows2 = [{"date": date(2023, 2, 2), "quantite": 999.0, "nom": "AUTRE", "external_id": "EB-123"}]
    res = ingest_transactions(db_session, prop.id, None, rows2, "api")
    assert res["inserted"] == 0 and res["deduplicated"] == 1


def test_ingest_fallback_keeps_intra_batch_duplicates(db_session):
    # Régression : la clé de repli (property_id, date, quantite, nom) ne doit PAS être
    # dédoublonnée au sein d'un même lot. Deux lignes identiques dans un même fichier CSV
    # sont souvent deux transactions RÉELLES distinctes (ex. deux encaissements de charges
    # locatives de 60€ le même jour, pour deux locataires différents) — la prod contient
    # 22 groupes de doublons littéraux (43 lignes) de ce type. L'ancien import CSV ne
    # dédoublonnait ces lignes que contre la BASE, jamais au sein du fichier en cours :
    # les deux lignes doivent donc être TOUTES DEUX insérées ici.
    prop, cat = _seed_property_with_rule(db_session)
    rows = [
        {"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None},
        {"date": date(2023, 1, 5), "quantite": 390.0, "nom": "LOYER MATERA", "external_id": None},
    ]
    res = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert res["inserted"] == 2
    assert res["deduplicated"] == 0
    assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 2


def test_ingest_dedup_intra_batch_external_id(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    account = BankAccount(property_id=prop.id)
    db_session.add(account); db_session.flush()
    rows = [
        {"date": date(2023, 2, 1), "quantite": 100.0, "nom": "VIR", "external_id": "EB-999"},
        {"date": date(2023, 2, 1), "quantite": 100.0, "nom": "VIR", "external_id": "EB-999"},
    ]
    res = ingest_transactions(db_session, prop.id, account.id, rows, "api")
    assert res["inserted"] == 1
    assert res["deduplicated"] == 1
    assert db_session.query(Transaction).filter(Transaction.account_id == account.id).count() == 1


def test_ingest_returns_ids(db_session):
    prop, cat = _seed_property_with_rule(db_session)
    rows = [
        {"date": date(2023, 3, 1), "quantite": 10.0, "nom": "A", "external_id": None},
        {"date": date(2023, 3, 2), "quantite": 20.0, "nom": "B", "external_id": None},
    ]
    res = ingest_transactions(db_session, prop.id, None, rows, "csv")
    assert len(res["ids"]) == 2
    db_ids = {tx.id for tx in db_session.query(Transaction).filter(Transaction.property_id == prop.id).all()}
    assert set(res["ids"]) == db_ids
