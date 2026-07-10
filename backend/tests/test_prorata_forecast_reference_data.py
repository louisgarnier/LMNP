"""
Tests pour GET /api/forecast-configs/reference-data
(backend/api/routes/prorata_forecast.py).

⚠️ Utilise le harnais isolé (fixtures `client` / `db_session`, base SQLite en
mémoire) : ne touche jamais backend/database/lmnp.db.

Bug corrigé (revue finale Bloc A, F1) : la route enveloppait TOUT son corps
dans un `try/except Exception`, y compris son propre
`raise HTTPException(400, "Type inconnu")` pour un `target_type` invalide.
Résultat : cette 400 était ré-attrapée par le handler générique, qui
avalait l'erreur et renvoyait 200 avec `categories=[]` — un `target_type`
invalide (faute de frappe, ancien client, etc.) passait donc inaperçu au
lieu de remonter une erreur exploitable.

Comportement attendu désormais : un `target_type` inconnu renvoie bien un
400 (pas un 200 avec une liste vide).
"""

from backend.database.models import Property


def _make_property(db_session) -> int:
    prop = Property(name="Test ReferenceData")
    db_session.add(prop)
    db_session.flush()
    return prop.id


def test_reference_data_invalid_target_type_returns_400(client, db_session):
    """target_type inconnu -> 400, pas un 200 avec categories=[]."""
    pid = _make_property(db_session)

    resp = client.get(
        "/api/forecast-configs/reference-data"
        f"?property_id={pid}&year=2024&target_type=type_inconnu"
    )

    assert resp.status_code == 400, resp.text
    assert "Type inconnu" in resp.json()["detail"]


def test_reference_data_valid_target_type_returns_200(client, db_session):
    """target_type valide (aucune donnée) -> 200 avec liste vide, comportement normal."""
    pid = _make_property(db_session)

    resp = client.get(
        "/api/forecast-configs/reference-data"
        f"?property_id={pid}&year=2024&target_type=compte_resultat"
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["categories"] == []
    assert body["year"] == 2024
    assert body["target_type"] == "compte_resultat"
