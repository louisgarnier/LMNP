"""Étape 2 Task 6 — Golden de CONTRAT du bilan (harnais isolé).

Ce test fige (fixture `fixtures/bilan_contract_etape2.json`) la sortie JSON de
`GET /api/bilan/calculate` pour un mini-monde déterministe, AVANT la bascule du
service de calcul (level_1_values JSON → liaison category_id + dispatch par
line_code). Il devient le verrou : après bascule, le JSON doit rester IDENTIQUE.

Le mini-monde est semé via le client isolé (`client` partage la session
`db_session` en mémoire — jamais la base de production) :
  - 1 propriété
  - allowed_mappings (pour autoriser la classification via l'API)
  - transactions ACTIF (immobilisation) sur 2 années (2023, 2024)
  - classification via l'API PUT /api/enrichment/transactions/{id} : écrit
    enriched_transactions ET synchronise transactions.category_id (dual-write
    Task 4). La classification CRÉE les categories custom au passage, ce qui
    rend résoluble la liaison posée par POST /mappings.
  - config Level 3 + 1 ligne normale (Immobilisations) + 1 ligne spéciale
    (Compte bancaire, COMPTE_BANCAIRE) via l'API POST /mappings

Ordre volontaire : classifier AVANT de poster les mappings, pour que les
labels level_1 existent en tant que Category au moment où POST /mappings
résout la liaison par label.
"""

import json
from datetime import date
from pathlib import Path

from backend.database.models import Property, Transaction, AllowedMapping

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "bilan_contract_etape2.json"

# (nom, date, quantité, solde, level_1, level_2, level_3)
_TX = [
    ("Achat immobilisation 2023", date(2023, 1, 5), -100000.0, -100000.0,
     "IMMO", "Immobilisations", "Actif"),
    ("Loyer encaissé 2023", date(2023, 6, 15), 6000.0, -94000.0,
     "IMMO", "Immobilisations", "Actif"),
    ("Complément immo 2024", date(2024, 3, 10), -5000.0, -99000.0,
     "IMMO", "Immobilisations", "Actif"),
]


def _seed_and_calculate(client, db_session):
    """Sème le mini-monde puis renvoie le JSON de GET /calculate (2023,2024)."""
    prop = Property(name="TEST_BILAN_CONTRACT_ETAPE2", address="1 rue du Test")
    db_session.add(prop)
    db_session.flush()
    pid = prop.id

    # Autoriser les combinaisons de classification pour cette propriété
    for l1, l2, l3 in {(t[4], t[5], t[6]) for t in _TX}:
        db_session.add(AllowedMapping(property_id=pid, level_1=l1, level_2=l2,
                                      level_3=l3, is_hardcoded=False))

    # Insérer les transactions brutes
    tx_ids = []
    for nom, d, q, solde, l1, l2, l3 in _TX:
        tx = Transaction(property_id=pid, date=d, quantite=q, nom=nom, solde=solde,
                         source_file="bilan_contract")
        db_session.add(tx)
        db_session.flush()
        tx_ids.append((tx.id, l1, l2, l3))
    db_session.commit()

    # Classifier via l'API (écrit enriched + category_id via dual-write Task 4)
    for tid, l1, l2, l3 in tx_ids:
        resp = client.put(
            f"/api/enrichment/transactions/{tid}",
            params={"level_1": l1, "level_2": l2, "level_3": l3},
        )
        assert resp.status_code == 200, resp.text

    # Config Level 3 (natures ACTIF/PASSIF autorisées dans le bilan)
    resp = client.put(
        "/api/bilan/config",
        json={"property_id": pid,
              "level_3_values": json.dumps(["Actif", "Passif"])},
    )
    assert resp.status_code == 200, resp.text

    # 1 ligne normale (Immobilisations, ACTIF) — level_1_values en labels
    resp = client.post(
        "/api/bilan/mappings",
        json={
            "property_id": pid,
            "category_name": "Immobilisations",
            "type": "ACTIF",
            "sub_category": "Actif immobilisé",
            "level_1_values": json.dumps(["IMMO"]),
            "is_special": False,
        },
    )
    assert resp.status_code == 201, resp.text

    # 1 ligne spéciale (Compte bancaire, COMPTE_BANCAIRE via special_source)
    resp = client.post(
        "/api/bilan/mappings",
        json={
            "property_id": pid,
            "category_name": "Compte bancaire",
            "type": "ACTIF",
            "sub_category": "Actif circulant",
            "is_special": True,
            "special_source": "transactions",
        },
    )
    assert resp.status_code == 201, resp.text

    resp = client.get(
        "/api/bilan/calculate",
        params={"property_id": pid, "years": "2023,2024"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _normalize(payload):
    """Rend le JSON comparable (indépendant de property_id concret)."""
    return json.loads(json.dumps(payload, sort_keys=True))


def test_bilan_contract_golden(client, db_session):
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
        "Le bilan a changé par rapport au golden de contrat.\n"
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
    from backend.database.models import Property, BilanMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    cat_a = _seed_category(db_session, "AAA", "G1", "actif")
    cat_b = _seed_category(db_session, "BBB", "G1", "actif")
    db_session.commit()

    resp = client.post("/api/bilan/mappings", json={
        "property_id": pid, "category_name": "Ligne actif",
        "type": "ACTIF", "sub_category": "Actif immobilisé",
        "level_1_values": json.dumps(["BBB", "AAA"]), "is_special": False,
    })
    assert resp.status_code == 201, resp.text
    # Réponse : labels reconstruits depuis la liaison, triés
    assert json.loads(resp.json()["level_1_values"]) == ["AAA", "BBB"]

    mid = resp.json()["id"]
    links = db_session.query(BilanMappingCategory).filter(
        BilanMappingCategory.mapping_id == mid
    ).all()
    assert {l.category_id for l in links} == {cat_a.id, cat_b.id}


def test_put_replaces_liaison(client, db_session):
    from backend.database.models import Property, BilanMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    cat_a = _seed_category(db_session, "AAA", "G1", "actif")
    cat_b = _seed_category(db_session, "BBB", "G1", "actif")
    db_session.commit()

    mid = client.post("/api/bilan/mappings", json={
        "property_id": pid, "category_name": "L", "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "level_1_values": json.dumps(["AAA"]), "is_special": False,
    }).json()["id"]

    resp = client.put(f"/api/bilan/mappings/{mid}",
                      params={"property_id": pid},
                      json={"level_1_values": json.dumps(["BBB"])})
    assert resp.status_code == 200, resp.text

    links = db_session.query(BilanMappingCategory).filter(
        BilanMappingCategory.mapping_id == mid
    ).all()
    assert {l.category_id for l in links} == {cat_b.id}


def test_delete_mapping_cascades_liaison(client, db_session):
    from backend.database.models import Property, BilanMappingCategory
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    _seed_category(db_session, "AAA", "G1", "actif")
    db_session.commit()

    mid = client.post("/api/bilan/mappings", json={
        "property_id": pid, "category_name": "L", "type": "ACTIF",
        "sub_category": "Actif immobilisé",
        "level_1_values": json.dumps(["AAA"]), "is_special": False,
    }).json()["id"]
    assert db_session.query(BilanMappingCategory).filter(
        BilanMappingCategory.mapping_id == mid).count() == 1

    resp = client.delete(f"/api/bilan/mappings/{mid}", params={"property_id": pid})
    assert resp.status_code == 204, resp.text

    assert db_session.query(BilanMappingCategory).filter(
        BilanMappingCategory.mapping_id == mid).count() == 0


def test_special_mapping_has_no_liaison_and_line_code_migrates(db_session):
    from backend.database.models import Property, BilanMapping, BilanMappingCategory
    from backend.database.migrations.migrate_bilan_config_to_ids import _migrate
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    pid = prop.id
    cat = _seed_category(db_session, "AAA", "G1", "actif")
    db_session.add(BilanMapping(
        property_id=pid, category_name="Immo", type="ACTIF",
        sub_category="Actif immobilisé", level_1_values=json.dumps(["AAA"]),
        is_special=False,
    ))
    db_session.add(BilanMapping(
        property_id=pid, category_name="Compte bancaire", type="ACTIF",
        sub_category="Actif circulant", is_special=True,
        special_source="transactions",
    ))
    db_session.add(BilanMapping(
        property_id=pid, category_name="Amortissements cumulés", type="ACTIF",
        sub_category="Actif immobilisé", is_special=True,
        special_source="amortizations",
    ))
    db_session.commit()

    stats, unresolved = _migrate(db_session)
    db_session.commit()
    assert unresolved == []
    assert stats["links_created"] == 1
    assert stats["line_codes_set"] == 2  # transactions + amortizations
    link = db_session.query(BilanMappingCategory).one()
    assert link.category_id == cat.id

    # line codes posés
    banque = db_session.query(BilanMapping).filter(
        BilanMapping.category_name == "Compte bancaire").one()
    assert banque.line_code == "COMPTE_BANCAIRE"
    amort = db_session.query(BilanMapping).filter(
        BilanMapping.category_name == "Amortissements cumulés").one()
    assert amort.line_code == "AMORT_CUMULES"

    # Idempotence : deuxième passage ne recrée rien
    stats2, unresolved2 = _migrate(db_session)
    assert unresolved2 == []
    assert stats2["links_created"] == 0
    assert stats2["links_existing"] == 1
    assert stats2["line_codes_set"] == 0


def test_migration_reports_unresolved_label(db_session):
    from backend.database.models import Property, BilanMapping
    from backend.database.migrations.migrate_bilan_config_to_ids import _migrate
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    db_session.add(BilanMapping(
        property_id=prop.id, category_name="Ligne", type="ACTIF",
        sub_category="Actif immobilisé",
        level_1_values=json.dumps(["LABEL_INEXISTANT"]), is_special=False,
    ))
    db_session.commit()

    stats, unresolved = _migrate(db_session)
    assert len(unresolved) == 1
    assert unresolved[0][2] == "LABEL_INEXISTANT"
    assert stats["links_created"] == 0


def test_empty_level_1_values_gives_zero_links(db_session):
    from backend.database.models import Property, BilanMapping, BilanMappingCategory
    from backend.database.migrations.migrate_bilan_config_to_ids import _migrate
    prop = Property(name="P"); db_session.add(prop); db_session.flush()
    db_session.add(BilanMapping(
        property_id=prop.id, category_name="Vide", type="PASSIF",
        sub_category="Capitaux propres", level_1_values="[]", is_special=False,
    ))
    db_session.commit()

    stats, unresolved = _migrate(db_session)
    db_session.commit()
    assert unresolved == []
    assert stats["links_created"] == 0
    assert db_session.query(BilanMappingCategory).count() == 0
