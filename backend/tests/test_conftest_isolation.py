"""
Test d'isolation du harnais de tests (conftest.py).

Ce test prouve que les fixtures pytest `client` / `db_session` définies dans
`conftest.py` n'écrivent JAMAIS dans la base de données de production
(backend/database/lmnp.db). Il crée une Property via le client HTTP de test,
vérifie qu'elle est bien retournée par l'API, puis vérifie que le fichier
lmnp.db n'a pas été modifié (hash SHA-256 avant/après identique).

Run with: python3 -m pytest backend/tests/test_conftest_isolation.py -v
"""

import hashlib
from pathlib import Path

PROD_DB_FILE = Path(__file__).parent.parent / "database" / "lmnp.db"


def _hash_file(path: Path) -> str:
    """Retourne le hash SHA-256 du fichier, ou None si le fichier n'existe pas."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_conftest_isolation_does_not_touch_prod_db(client):
    """
    Créer une Property via `client` (fixture conftest) doit passer par une
    base SQLite en mémoire, jamais par backend/database/lmnp.db.
    """
    hash_before = _hash_file(PROD_DB_FILE)

    # 1. Créer une propriété via l'API (passe par la fixture `client`)
    response = client.post(
        "/api/properties",
        json={"name": "Test Isolation Property", "address": "1 rue du Test"},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["name"] == "Test Isolation Property"
    property_id = created["id"]

    # 2. Vérifier qu'elle existe bien via l'API (relue depuis la même session en mémoire)
    response = client.get(f"/api/properties/{property_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == property_id
    assert fetched["name"] == "Test Isolation Property"

    # 3. Vérifier que le fichier de production n'a PAS été modifié
    hash_after = _hash_file(PROD_DB_FILE)
    assert hash_before == hash_after, (
        "backend/database/lmnp.db a été modifié par le test : "
        "le harnais de tests n'est PAS isolé de la base de production."
    )
