"""Étape 2 Task 5 — Golden de CONTRAT du compte de résultat (harnais isolé).

Ce test fige (fixture `fixtures/cr_contract_etape2.json`) la sortie JSON de
`GET /api/compte-resultat/calculate` pour un mini-monde déterministe, AVANT la
bascule du service de calcul (level_1_values JSON → liaison category_id). Il
devient le verrou : après bascule, le JSON doit rester IDENTIQUE.

Le mini-monde est semé via le client isolé (`client` partage la session
`db_session` en mémoire — jamais la base de production) :
  - 1 propriété
  - 4 transactions (2 loyers + 2 entretiens) sur 2 années (2023, 2024)
  - classification via `update_transaction_classification` (moteur vivant,
    étape 3 Task 9 : remplace l'ancien appel API PUT
    /api/enrichment/transactions/{id}, route retirée) : écrit directement
    transactions.category_id.
  - config Level 3 + 2 lignes CR (1 produit, 1 charge) via l'API POST /mappings

Ordre volontaire : classifier AVANT de poster les mappings, pour que les
labels level_1 existent en tant que Category au moment où POST /mappings
résout la liaison par label.
"""

import json
from datetime import date
from pathlib import Path

from backend.database.models import Property, Transaction, Category, CategoryGroup
from backend.api.services.category_service import NATURE_BY_LABEL

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cr_contract_etape2.json"

# (nom, date, quantité, level_1, level_2, level_3)
_TX = [
    ("Loyers janv 2023", date(2023, 1, 10), 6000.0, "LOYERS", "Produits", "Produits"),
    ("Entretien 2023", date(2023, 7, 10), -800.0, "ENTRETIEN", "Charges", "Charges Déductibles"),
    ("Loyers janv 2024", date(2024, 1, 10), 7200.0, "LOYERS", "Produits", "Produits"),
    ("Entretien 2024", date(2024, 7, 10), -500.0, "ENTRETIEN", "Charges", "Charges Déductibles"),
]


def _seed_and_calculate(client, db_session):
    """Sème le mini-monde puis renvoie le JSON de GET /calculate (2023,2024)."""
    prop = Property(name="TEST_CR_CONTRACT_ETAPE2", address="1 rue du Test")
    db_session.add(prop)
    db_session.flush()
    pid = prop.id

    # Peupler le référentiel (validate_mapping résout désormais via
    # resolve_category, plus via allowed_mappings)
    for l1, l2, l3 in {(t[3], t[4], t[5]) for t in _TX}:
        nature = NATURE_BY_LABEL[l3]
        group = db_session.query(CategoryGroup).filter(
            CategoryGroup.label == l2, CategoryGroup.nature == nature
        ).first()
        if group is None:
            group = CategoryGroup(label=l2, nature=nature)
            db_session.add(group)
            db_session.flush()
        db_session.add(Category(label=l1, group_id=group.id, is_custom=False))

    # Insérer les transactions brutes
    tx_ids = []
    solde = 0.0
    for nom, d, q, l1, l2, l3 in _TX:
        solde += q
        tx = Transaction(property_id=pid, date=d, quantite=q, nom=nom, solde=solde,
                         source_file="cr_contract")
        db_session.add(tx)
        db_session.flush()
        tx_ids.append((tx.id, l1, l2, l3))
    db_session.commit()

    # Classifier via le moteur vivant (étape 3 Task 9 : remplace l'appel API
    # PUT /api/enrichment/transactions/{id}, route retirée avec le reste du
    # back legacy mapping — écrit directement transactions.category_id,
    # équivalent au dual-write historique qui écrivait aussi
    # enriched_transactions, table supprimée depuis étape 2 Task 8).
    from backend.api.services.enrichment_service import update_transaction_classification
    for tid, l1, l2, l3 in tx_ids:
        tx_obj = db_session.query(Transaction).filter(Transaction.id == tid).first()
        update_transaction_classification(db_session, tx_obj, level_1=l1, level_2=l2, level_3=l3)

    # Config Level 3 (natures autorisées dans le CR)
    resp = client.put(
        "/api/compte-resultat/config",
        params={"property_id": pid},
        json={"level_3_values": json.dumps(["Produits", "Charges Déductibles"])},
    )
    assert resp.status_code == 200, resp.text

    # 2 lignes CR (1 produit, 1 charge) — level_1_values en labels (inchangé)
    for category_name, type_, l1_values in [
        ("Loyers hors charge encaissés", "Produits d'exploitation", ["LOYERS"]),
        ("Charges d'entretien et de réparation", "Charges d'exploitation", ["ENTRETIEN"]),
    ]:
        resp = client.post(
            "/api/compte-resultat/mappings",
            json={
                "property_id": pid,
                "category_name": category_name,
                "type": type_,
                "level_1_values": json.dumps(l1_values),
            },
        )
        assert resp.status_code == 201, resp.text

    resp = client.get(
        "/api/compte-resultat/calculate",
        params={"property_id": pid, "years": "2023,2024"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _normalize(payload):
    """Rend le JSON comparable (indépendant de property_id concret)."""
    return json.loads(json.dumps(payload, sort_keys=True))


def test_cr_contract_golden(client, db_session):
    result = _normalize(_seed_and_calculate(client, db_session))

    if not FIXTURE_PATH.exists():
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(json.dumps(result, indent=2, sort_keys=True,
                                           ensure_ascii=False), encoding="utf-8")
        # Premier passage : fixture gelée. On échoue explicitement pour forcer
        # une relecture/commit consciente de la référence.
        raise AssertionError(
            f"Fixture de contrat créée : {FIXTURE_PATH}. "
            "Vérifier son contenu puis relancer le test (doit être GREEN)."
        )

    expected = _normalize(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    assert result == expected, (
        "Le compte de résultat a changé par rapport au golden de contrat.\n"
        f"attendu={json.dumps(expected, sort_keys=True, ensure_ascii=False)}\n"
        f"obtenu ={json.dumps(result, sort_keys=True, ensure_ascii=False)}"
    )


# --------------------------------------------------------------------------- #
# Tests unitaires ciblés de la liaison (dual-write, GET rebuild, cascade)      #
# --------------------------------------------------------------------------- #

def _seed_category(db, label, group_label, nature):
    from backend.database.models import Category, CategoryGroup
    group = db.query(CategoryGroup).filter(CategoryGroup.label == group_label).first()
    if group is None:
        group = CategoryGroup(label=group_label, nature=nature)
        db.add(group)
        db.flush()
    cat = Category(label=label, group_id=group.id, is_custom=False)
    db.add(cat)
    db.flush()
    return cat


def test_post_then_get_rebuilds_labels_from_liaison(client, db_session):
    from backend.database.models import Property, CompteResultatMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    cat_a = _seed_category(db_session, "AAA", "G1", "produits")
    cat_b = _seed_category(db_session, "BBB", "G1", "produits")
    db_session.commit()

    resp = client.post("/api/compte-resultat/mappings", json={
        "property_id": pid, "category_name": "Ligne produit",
        "type": "Produits d'exploitation",
        "level_1_values": json.dumps(["BBB", "AAA"]),
    })
    assert resp.status_code == 201, resp.text
    # Réponse : labels reconstruits depuis la liaison, triés
    assert json.loads(resp.json()["level_1_values"]) == ["AAA", "BBB"]

    mid = resp.json()["id"]
    links = db_session.query(CompteResultatMappingCategory).filter(
        CompteResultatMappingCategory.mapping_id == mid
    ).all()
    assert {l.category_id for l in links} == {cat_a.id, cat_b.id}


def test_put_replaces_liaison(client, db_session):
    from backend.database.models import Property, CompteResultatMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    cat_a = _seed_category(db_session, "AAA", "G1", "produits")
    cat_b = _seed_category(db_session, "BBB", "G1", "produits")
    db_session.commit()

    mid = client.post("/api/compte-resultat/mappings", json={
        "property_id": pid, "category_name": "L", "type": "Produits d'exploitation",
        "level_1_values": json.dumps(["AAA"]),
    }).json()["id"]

    resp = client.put(f"/api/compte-resultat/mappings/{mid}",
                      params={"property_id": pid},
                      json={"level_1_values": json.dumps(["BBB"])})
    assert resp.status_code == 200, resp.text

    links = db_session.query(CompteResultatMappingCategory).filter(
        CompteResultatMappingCategory.mapping_id == mid
    ).all()
    assert {l.category_id for l in links} == {cat_b.id}


def test_delete_mapping_cascades_liaison(client, db_session):
    from backend.database.models import Property, CompteResultatMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    _seed_category(db_session, "AAA", "G1", "produits")
    db_session.commit()

    mid = client.post("/api/compte-resultat/mappings", json={
        "property_id": pid, "category_name": "L", "type": "Produits d'exploitation",
        "level_1_values": json.dumps(["AAA"]),
    }).json()["id"]
    assert db_session.query(CompteResultatMappingCategory).filter(
        CompteResultatMappingCategory.mapping_id == mid).count() == 1

    resp = client.delete(f"/api/compte-resultat/mappings/{mid}", params={"property_id": pid})
    assert resp.status_code == 204, resp.text

    assert db_session.query(CompteResultatMappingCategory).filter(
        CompteResultatMappingCategory.mapping_id == mid).count() == 0


# NB étape 2 Task 8 : les tests de la migration one-shot
# `migrate_cr_config_to_ids._migrate` (level_1_values JSON → liaison) ont été
# retirés avec la migration elle-même (obsolète : la colonne level_1_values a
# été retirée du modèle, la liaison category_links est désormais la seule source).
# La construction/idempotence de la liaison reste couverte par les tests API
# ci-dessus (POST/PUT/DELETE) et par le golden de contrat.
