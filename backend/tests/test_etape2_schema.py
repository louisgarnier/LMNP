"""
Étape 2 Task 1 : les modèles morts sont supprimés, l'unicité loan_configs
est par propriété. Harnais isolé (db_session) — jamais la base de prod.
"""
import pytest
from sqlalchemy.exc import IntegrityError


def test_dead_models_are_gone():
    import backend.database.models as m
    for dead in ("Parameter", "Amortization", "FinancialStatement",
                 "ConsolidatedFinancialStatement"):
        assert not hasattr(m, dead), f"{dead} doit être supprimé de models.py"


def test_loan_config_name_unique_per_property_only(db_session):
    from backend.database.models import LoanConfig, Property
    p1 = Property(name="A"); p2 = Property(name="B")
    db_session.add_all([p1, p2]); db_session.flush()
    common = dict(credit_amount=1000.0, interest_rate=1.0,
                  duration_years=10, initial_deferral_months=0)
    db_session.add(LoanConfig(name="pret", property_id=p1.id, **common))
    db_session.flush()
    # Même nom sur une AUTRE propriété : autorisé
    db_session.add(LoanConfig(name="pret", property_id=p2.id, **common))
    db_session.flush()
    # Même nom sur la MÊME propriété : refusé
    db_session.add(LoanConfig(name="pret", property_id=p1.id, **common))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_delete_transaction_endpoint_still_works(client):
    """
    Verrou de comportement : DELETE /api/transactions/{id} doit continuer de
    fonctionner après le retrait du bloc mort `db.query(Amortization)...`
    (la table orpheline `amortizations` n'a jamais eu de writer ; la vraie
    cascade d'amortissement est le bloc AmortizationResult, conservé).
    """
    # Créer une propriété via l'API
    resp = client.post("/api/properties", json={"name": "Prop-DELETE-test"})
    assert resp.status_code == 201, resp.text
    property_id = resp.json()["id"]

    # Créer une transaction via l'API
    resp = client.post("/api/transactions", json={
        "date": "2025-01-15",
        "quantite": -100.0,
        "nom": "Test suppression",
        "solde": 900.0,
        "property_id": property_id,
    })
    assert resp.status_code == 201, resp.text
    transaction_id = resp.json()["id"]

    # La supprimer via l'endpoint DELETE (contrat : 204 No Content)
    resp = client.delete(f"/api/transactions/{transaction_id}",
                         params={"property_id": property_id})
    assert resp.status_code == 204, resp.text

    # Vérifier qu'elle a bien disparu
    resp = client.get(f"/api/transactions/{transaction_id}",
                      params={"property_id": property_id})
    assert resp.status_code == 404, resp.text
