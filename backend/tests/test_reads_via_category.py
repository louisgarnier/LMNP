"""Étape 2 Task 7 : les lectures backend dérivent level_1/2/3 de
`transactions.category_id` (référentiel), pas de `enriched_transactions`.

Contrat gelé : chaque endoint continue de RENVOYER level_1/level_2/level_3 avec
les MÊMES valeurs textuelles qu'avant (Category.label / CategoryGroup.label /
LABEL_BY_NATURE[nature]). Le seed passe par l'API (POST /api/transactions →
enrich_transaction → double-écriture Task 4) afin que `category_id` soit posé
par le vrai chemin de production, puis les endpoints de lecture sont exercés
via le même `TestClient` (session en mémoire isolée de conftest).

Harnais isolé (fixtures `db_session` / `client`) : ne touche JAMAIS la base de
production.
"""
from datetime import date

from backend.database.models import (
    Property,
    Mapping,
    AllowedMapping,
    AmortizationType,
    AmortizationResult,
    Transaction,
)

# Combos de classification utilisés (level_1 = Category.label,
# level_2 = CategoryGroup.label, level_3 = label de nature).
LOYER = ("Loyers hors charge encaissés", "Produits", "Produits")
ENTRETIEN = ("Charges d'entretien", "Charges", "Charges Déductibles")
IMMO = ("Immobilisations corporelles", "Immobilisations", "Actif")


def _seed_property_with_mappings(db):
    """Crée une propriété + les mappings (nom → classification) nécessaires pour
    que l'enrichissement pose category_id via la double-écriture."""
    p = Property(name="T7_READS")
    db.add(p)
    db.flush()
    for (l1, l2, l3), nom in [(LOYER, "VIR LOYER"), (ENTRETIEN, "PRLV ENTRETIEN"),
                              (IMMO, "ACHAT IMMO")]:
        db.add(AllowedMapping(property_id=p.id, level_1=l1, level_2=l2, level_3=l3,
                              is_hardcoded=False))
        db.add(Mapping(property_id=p.id, nom=nom, level_1=l1, level_2=l2, level_3=l3,
                       is_prefix_match=False, priority=1))
    db.commit()
    return p.id


def _post_tx(client, pid, d, quantite, nom):
    r = client.post("/api/transactions", json={
        "property_id": pid,
        "date": d.isoformat(),
        "quantite": quantite,
        "nom": nom,
        "solde": 0.0,
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_get_transactions_levels_and_filters(db_session, client):
    pid = _seed_property_with_mappings(db_session)
    _post_tx(client, pid, date(2023, 6, 15), 6000.0, "VIR LOYER")
    _post_tx(client, pid, date(2023, 7, 10), -800.0, "PRLV ENTRETIEN")
    # Transaction non classée (aucun mapping ne matche « DIVERS »)
    _post_tx(client, pid, date(2023, 8, 1), -42.0, "DIVERS achat")

    # Liste complète : les niveaux sont dérivés du référentiel
    r = client.get(f"/api/transactions?property_id={pid}&limit=100")
    assert r.status_code == 200
    by_nom = {t["nom"]: t for t in r.json()["transactions"]}
    assert by_nom["VIR LOYER"]["level_1"] == "Loyers hors charge encaissés"
    assert by_nom["VIR LOYER"]["level_2"] == "Produits"
    assert by_nom["VIR LOYER"]["level_3"] == "Produits"
    assert by_nom["PRLV ENTRETIEN"]["level_3"] == "Charges Déductibles"
    # Non classée : niveaux NULL
    assert by_nom["DIVERS achat"]["level_1"] is None
    assert by_nom["DIVERS achat"]["level_2"] is None
    assert by_nom["DIVERS achat"]["level_3"] is None

    # Filtre level_1 (contient, insensible à la casse)
    r = client.get(f"/api/transactions?property_id={pid}&filter_level_1=loyers&limit=100")
    noms = {t["nom"] for t in r.json()["transactions"]}
    assert noms == {"VIR LOYER"}

    # unclassified_only : seule la transaction sans category_id
    r = client.get(f"/api/transactions?property_id={pid}&unclassified_only=true&limit=100")
    noms = {t["nom"] for t in r.json()["transactions"]}
    assert noms == {"DIVERS achat"}

    # Tri par level_1 desc : les non classées (NULL) et classées cohabitent sans crash
    r = client.get(f"/api/transactions?property_id={pid}&sort_by=level_1&sort_direction=asc&limit=100")
    assert r.status_code == 200


def test_unique_values(db_session, client):
    pid = _seed_property_with_mappings(db_session)
    _post_tx(client, pid, date(2023, 6, 15), 6000.0, "VIR LOYER")
    _post_tx(client, pid, date(2023, 7, 10), -800.0, "PRLV ENTRETIEN")
    _post_tx(client, pid, date(2024, 1, 5), -42.0, "DIVERS achat")

    r = client.get(f"/api/transactions/unique-values?property_id={pid}&column=level_1")
    assert r.status_code == 200
    assert r.json()["values"] == ["Charges d'entretien", "Loyers hors charge encaissés"]

    r = client.get(f"/api/transactions/unique-values?property_id={pid}&column=level_3")
    assert set(r.json()["values"]) == {"Produits", "Charges Déductibles"}

    # Filtrage des level_1 par level_2
    r = client.get(f"/api/transactions/unique-values?property_id={pid}&column=level_1&filter_level_2=Produits")
    assert r.json()["values"] == ["Loyers hors charge encaissés"]

    # mois / annee dérivés de la date
    r = client.get(f"/api/transactions/unique-values?property_id={pid}&column=mois")
    assert set(r.json()["values"]) == {"1", "6", "7"}
    r = client.get(f"/api/transactions/unique-values?property_id={pid}&column=annee")
    assert set(r.json()["values"]) == {"2023", "2024"}


def test_analytics_pivot(db_session, client):
    pid = _seed_property_with_mappings(db_session)
    _post_tx(client, pid, date(2023, 6, 15), 6000.0, "VIR LOYER")
    _post_tx(client, pid, date(2023, 6, 20), 1000.0, "VIR LOYER")
    _post_tx(client, pid, date(2023, 7, 10), -800.0, "PRLV ENTRETIEN")

    r = client.get(f"/api/analytics/pivot?property_id={pid}&rows=level_1")
    assert r.status_code == 200, r.text
    row_totals = r.json()["row_totals"]
    assert row_totals["Loyers hors charge encaissés"] == 7000.0
    assert row_totals["Charges d'entretien"] == -800.0
    assert r.json()["grand_total"] == 6200.0

    # Filtre pivot sur level_3 : seuls les produits subsistent
    import json as _json
    filt = _json.dumps({"level_3": "Produits"})
    r = client.get(f"/api/analytics/pivot?property_id={pid}&rows=level_1&filters={filt}")
    row_totals = r.json()["row_totals"]
    assert set(row_totals.keys()) == {"Loyers hors charge encaissés"}
    assert row_totals["Loyers hors charge encaissés"] == 7000.0


def test_amortization_matching_via_category(db_session, client):
    pid = _seed_property_with_mappings(db_session)
    # Type d'amortissement matché sur (level_2 == group label, level_1 in labels)
    db_session.add(AmortizationType(
        property_id=pid, name="Immobilisation bâti",
        level_2_value="Immobilisations",
        level_1_values='["Immobilisations corporelles"]',
        start_date=date(2023, 1, 1), duration=25.0,
    ))
    db_session.commit()

    tx_id = _post_tx(client, pid, date(2023, 1, 5), -100000.0, "ACHAT IMMO")

    # La création de transaction déclenche déjà recalculate_transaction_amortization ;
    # on vérifie que le matching (désormais via category_id) a produit des résultats.
    results = db_session.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == tx_id
    ).all()
    assert results, "aucun résultat d'amortissement produit par le matching category_id"
    assert all(r.category == "Immobilisation bâti" for r in results)
    # Somme des amortissements == montant immobilisé (au centime)
    total = sum(abs(r.amount) for r in results)
    assert abs(total - 100000.0) < 0.01

    # L'endpoint transaction-count matche aussi via le référentiel
    type_id = db_session.query(AmortizationType).filter(
        AmortizationType.property_id == pid
    ).first().id
    r = client.get(f"/api/amortization/types/{type_id}/transaction-count?property_id={pid}")
    assert r.status_code == 200
    assert r.json()["transaction_count"] == 1


def test_calculate_normal_category_via_category_links(db_session):
    """`bilan_service.calculate_normal_category` (hors chemin API, utilisé par le
    script d'analyse de perf) lit désormais category_links + nature de groupe
    au lieu de enriched.level_1/level_3. On vérifie le matching via category_id
    sur une ligne passif à somme positive (la logique de signe ACTIF/PASSIF
    renvoie 0 pour une somme négative, inchangée par la bascule)."""
    from backend.database.models import BilanMapping, BilanMappingCategory
    from backend.api.services.bilan_service import calculate_normal_category
    from backend.api.services.category_service import get_or_create_category

    p = Property(name="T7_NORMAL_CAT")
    db_session.add(p)
    db_session.flush()
    # Catégorie « Cautions reçues » sous un groupe de nature passif.
    cat = get_or_create_category(db_session, "Cautions reçues", "Dépôts de garantie", "Passif")
    db_session.flush()
    db_session.add(Transaction(property_id=p.id, date=date(2023, 3, 1), quantite=500.0,
                               nom="CAUTION", solde=500.0, category_id=cat.id))
    mapping = BilanMapping(property_id=p.id, category_name="Cautions reçues",
                           type="PASSIF", sub_category="Dettes", is_special=False)
    mapping.category_links.append(BilanMappingCategory(category_id=cat.id))
    db_session.add(mapping)
    db_session.commit()

    montant = calculate_normal_category(db_session, 2023, mapping, ["Passif"], p.id)
    assert abs(montant - 500.0) < 0.01
    # Cumul avant la transaction : rien matché → 0.
    assert calculate_normal_category(db_session, 2022, mapping, ["Passif"], p.id) == 0.0
