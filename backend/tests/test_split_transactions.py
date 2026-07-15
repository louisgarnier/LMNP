from datetime import date
from backend.database.models import Property, Transaction, Category, CategoryGroup, AmortizationType, AmortizationResult
from backend.api.services.category_service import get_or_create_category


def _seed(db_session):
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    prop = Property(name="Split"); db_session.add(prop); db_session.flush()
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 5), quantite=280.0,
                         nom="MATERA", solde=280.0, source="csv", is_split_parent=False, category_id=cat.id)
    db_session.add(parent); db_session.commit()
    return prop, cat, parent


def _seed_with_immo(db_session):
    """Comme `_seed`, plus une catégorie amortissable (référentiel Immobilisations)
    et son `AmortizationType`, pour tester le recalcul d'amortissement à
    l'éclatement (Task 6 fix)."""
    grp = CategoryGroup(label="Produits", nature="produits"); db_session.add(grp); db_session.flush()
    cat = Category(label="Loyers", group_id=grp.id, is_custom=False); db_session.add(cat); db_session.flush()
    immo_cat = get_or_create_category(db_session, "Immobilisations corporelles", "Immobilisations", "Actif")
    prop = Property(name="SplitImmo"); db_session.add(prop); db_session.flush()
    db_session.add(AmortizationType(
        property_id=prop.id, name="Immobilisation bâti",
        level_2_value="Immobilisations",
        level_1_values='["Immobilisations corporelles"]',
        start_date=date(2023, 1, 1), duration=25.0,
    ))
    parent = Transaction(property_id=prop.id, date=date(2023, 1, 5), quantite=-1000.0,
                         nom="ACHAT IMMO A REPARTIR", solde=-1000.0, source="csv",
                         is_split_parent=False, category_id=cat.id)
    db_session.add(parent); db_session.commit()
    return prop, cat, immo_cat, parent


def test_split_replaces_parent_with_children(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 450.0, "nom": "loyer", "category_id": cat.id},
        {"quantite": -170.0, "nom": "frais agence", "category_id": cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    db_session.refresh(parent)
    assert parent.is_split_parent is True
    assert parent.category_id is None            # masquée → hors CR/bilan
    children = db_session.query(Transaction).filter(
        Transaction.parent_transaction_id == parent.id
    ).order_by(Transaction.id).all()
    assert len(children) == 2
    assert sum(c.quantite for c in children) == 280.0
    # Renforcement (revue) : le solde recalculé doit refléter le cumul réel des
    # enfants (parente exclue, is_split_parent), pas seulement le statut HTTP.
    assert children[0].solde == 450.0
    assert children[1].solde == 280.0


def test_split_rejects_wrong_sum(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 100.0, "nom": "x", "category_id": None},
    ]})
    assert resp.status_code == 400
    db_session.refresh(parent)
    assert parent.is_split_parent is False       # rien n'a changé
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0


def test_split_rejects_unknown_category(client, db_session):
    prop, cat, parent = _seed(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 280.0, "nom": "tout", "category_id": 999999},
    ]})
    assert resp.status_code == 400
    db_session.refresh(parent)
    assert parent.is_split_parent is False        # rien n'a changé
    assert parent.category_id == cat.id
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0


def test_undo_split_restores_parent(client, db_session):
    prop, cat, parent = _seed(db_session)
    client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": 280.0, "nom": "tout", "category_id": cat.id},
    ]})
    resp = client.delete(f"/api/transactions/{parent.id}/split")
    assert resp.status_code == 200
    db_session.refresh(parent)
    assert parent.is_split_parent is False
    assert db_session.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).count() == 0


def test_split_child_amortizable_gets_schedule(client, db_session):
    """Bug (revue) : split_transaction créait les enfants sans jamais appeler
    recalculate_transaction_amortization → un enfant classé dans une catégorie
    amortissable n'avait aucun échéancier. Vérifie aussi que l'amortissement
    caduc de la PARENTE (posé avant l'éclatement) est purgé (sinon double
    comptage CR/bilan, la parente étant masquée mais ses AmortizationResult
    restant en base)."""
    prop, cat, immo_cat, parent = _seed_with_immo(db_session)
    # Pré-condition : la parente portait déjà un amortissement (comme si elle
    # avait été classée/amortie avant l'éclatement).
    db_session.add(AmortizationResult(transaction_id=parent.id, year=2023,
                                      category="Immobilisation bâti", amount=-40.0))
    db_session.commit()

    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": -1000.0, "nom": "achat immo", "category_id": immo_cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    child_id = resp.json()["child_ids"][0]

    results = db_session.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == child_id
    ).all()
    assert results, "l'enfant amortissable devrait avoir un échéancier d'amortissement"
    total = sum(abs(r.amount) for r in results)
    assert abs(total - 1000.0) < 0.01

    # La parente est masquée (category_id=None) → son amortissement caduc doit
    # être purgé, pas laissé en base (double comptage sinon).
    assert db_session.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == parent.id
    ).count() == 0


def test_undo_split_restores_parent_and_clears_children_amortization(client, db_session):
    """Après annulation : la parente redevient visible, aucun enfant ni aucun
    AmortizationResult orphelin d'enfant ne doit subsister."""
    prop, cat, immo_cat, parent = _seed_with_immo(db_session)
    resp = client.post(f"/api/transactions/{parent.id}/split", json={"parts": [
        {"quantite": -1000.0, "nom": "achat immo", "category_id": immo_cat.id},
    ]})
    assert resp.status_code == 200, resp.text
    child_id = resp.json()["child_ids"][0]
    # Pré-condition (Task 6 fix) : l'enfant amortissable a bien un échéancier
    # avant l'annulation, sinon le test de nettoyage ci-dessous serait vide de sens.
    assert db_session.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == child_id
    ).count() > 0

    resp = client.delete(f"/api/transactions/{parent.id}/split")
    assert resp.status_code == 200, resp.text
    db_session.refresh(parent)
    assert parent.is_split_parent is False
    assert db_session.query(Transaction).filter(
        Transaction.parent_transaction_id == parent.id
    ).count() == 0
    # Aucun résultat d'amortissement orphelin pour l'ex-enfant supprimé.
    assert db_session.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == child_id
    ).count() == 0
