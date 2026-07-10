"""
Tests for pivot config endpoints.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from backend.api.main import app
from backend.database import Base, get_db
from backend.database.models import PivotConfig, Property

# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pivot_configs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture
def property_id():
    """
    Crée une Property dans la base de test et retourne son id.

    Les routes /api/pivot-configs exigent un property_id validé
    (`validate_property_id`, support multi-propriété) depuis l'ajout de
    cette contrainte — ce fixture répare le test, écrit avant cet ajout,
    en fournissant une propriété réelle plutôt qu'un id arbitraire.
    """
    db = TestingSessionLocal()
    try:
        prop = Property(name="Test Property Pivot")
        db.add(prop)
        db.commit()
        db.refresh(prop)
        return prop.id
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Setup test database before each test, and scope the `get_db` override to
    this test's execution (installed here, removed/restored in `finally`).

    Bloc A Task 8 finding: the override used to be set once at MODULE level
    (`app.dependency_overrides[get_db] = override_get_db` at import time).
    Because `app` is a process-wide FastAPI singleton shared by every test
    module in the same pytest session, another file's fixture (e.g.
    `conftest.py`'s `client` fixture, used by `test_realtime_states.py`) can
    legitimately `app.dependency_overrides.pop(get_db, None)` in ITS OWN
    teardown after running — which silently erases this module's override
    too. The next request made through this module's `client` then falls
    through to the REAL `get_db()` (production `backend/database/lmnp.db`)
    instead of `TestingSessionLocal`, since FastAPI resolves overrides at
    request time, not at `TestClient(app)` construction time. Observed
    concretely: `test_create_pivot_config` returned 400 "Property ID 1
    n'existe pas" (looked up against the real prod `properties` table)
    instead of using the property just created in the test's own SQLite
    file. No corruption occurred (id collision would have been required
    with a real property id — none did, verified against the live DB), but
    this was a latent risk of the same class as the incident documented in
    docs/workflow/ERROR_INVESTIGATION.md. Fix: install/remove the override
    per-test, restoring whatever override (if any) was in place before.
    """
    Base.metadata.create_all(bind=engine)
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        if previous_override is not None:
            app.dependency_overrides[get_db] = previous_override
        else:
            app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)


def test_create_pivot_config(property_id):
    """Test creating a pivot config."""
    config_data = {
        "property_id": property_id,
        "name": "Test Pivot Table",
        "config": {
            "rows": ["level_1", "level_2"],
            "columns": ["mois"],
            "data": ["quantite"],
            "filters": {}
        }
    }

    response = client.post("/api/pivot-configs", json=config_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Pivot Table"
    assert data["config"]["rows"] == ["level_1", "level_2"]
    assert data["config"]["columns"] == ["mois"]
    assert data["id"] is not None
    assert "created_at" in data
    assert "updated_at" in data


def test_create_pivot_config_duplicate_name(property_id):
    """Test creating a pivot config with duplicate name."""
    config_data = {
        "property_id": property_id,
        "name": "Test Pivot Table",
        "config": {
            "rows": ["level_1"],
            "columns": [],
            "data": ["quantite"],
            "filters": {}
        }
    }

    # Create first config
    response1 = client.post("/api/pivot-configs", json=config_data)
    assert response1.status_code == 201

    # Try to create second config with same name
    response2 = client.post("/api/pivot-configs", json=config_data)
    assert response2.status_code == 400
    assert "existe déjà" in response2.json()["detail"]


def test_get_pivot_configs(property_id):
    """Test getting list of pivot configs."""
    # Create two configs
    config1 = {
        "property_id": property_id,
        "name": "Config 1",
        "config": {"rows": ["level_1"], "columns": [], "data": ["quantite"], "filters": {}}
    }
    config2 = {
        "property_id": property_id,
        "name": "Config 2",
        "config": {"rows": ["level_2"], "columns": [], "data": ["quantite"], "filters": {}}
    }

    client.post("/api/pivot-configs", json=config1)
    client.post("/api/pivot-configs", json=config2)

    # Get all configs
    response = client.get("/api/pivot-configs", params={"property_id": property_id})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] in ["Config 1", "Config 2"]
    assert data["items"][1]["name"] in ["Config 1", "Config 2"]


def test_get_pivot_config(property_id):
    """Test getting a single pivot config."""
    config_data = {
        "property_id": property_id,
        "name": "Test Config",
        "config": {
            "rows": ["level_1", "level_2"],
            "columns": ["mois"],
            "data": ["quantite"],
            "filters": {"level_1": "Achat"}
        }
    }

    # Create config
    create_response = client.post("/api/pivot-configs", json=config_data)
    config_id = create_response.json()["id"]

    # Get config
    response = client.get(f"/api/pivot-configs/{config_id}", params={"property_id": property_id})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Config"
    assert data["config"]["rows"] == ["level_1", "level_2"]
    assert data["config"]["filters"]["level_1"] == "Achat"


def test_get_pivot_config_not_found(property_id):
    """Test getting a non-existent pivot config."""
    response = client.get("/api/pivot-configs/999", params={"property_id": property_id})
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


def test_update_pivot_config(property_id):
    """Test updating a pivot config."""
    # Create config
    config_data = {
        "property_id": property_id,
        "name": "Original Name",
        "config": {
            "rows": ["level_1"],
            "columns": [],
            "data": ["quantite"],
            "filters": {}
        }
    }
    create_response = client.post("/api/pivot-configs", json=config_data)
    config_id = create_response.json()["id"]

    # Update config
    update_data = {
        "name": "Updated Name",
        "config": {
            "rows": ["level_1", "level_2"],
            "columns": ["mois"],
            "data": ["quantite"],
            "filters": {}
        }
    }
    response = client.put(
        f"/api/pivot-configs/{config_id}",
        json=update_data,
        params={"property_id": property_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert len(data["config"]["rows"]) == 2
    assert "mois" in data["config"]["columns"]


def test_update_pivot_config_partial(property_id):
    """Test partial update of a pivot config."""
    # Create config
    config_data = {
        "property_id": property_id,
        "name": "Original Name",
        "config": {
            "rows": ["level_1"],
            "columns": [],
            "data": ["quantite"],
            "filters": {}
        }
    }
    create_response = client.post("/api/pivot-configs", json=config_data)
    config_id = create_response.json()["id"]

    # Update only name
    update_data = {"name": "Updated Name"}
    response = client.put(
        f"/api/pivot-configs/{config_id}",
        json=update_data,
        params={"property_id": property_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["config"]["rows"] == ["level_1"]  # Config unchanged


def test_update_pivot_config_not_found(property_id):
    """Test updating a non-existent pivot config."""
    update_data = {
        "name": "Updated Name",
        "config": {"rows": ["level_1"], "columns": [], "data": ["quantite"], "filters": {}}
    }
    response = client.put(
        "/api/pivot-configs/999",
        json=update_data,
        params={"property_id": property_id},
    )
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


def test_delete_pivot_config(property_id):
    """Test deleting a pivot config."""
    # Create config
    config_data = {
        "property_id": property_id,
        "name": "To Delete",
        "config": {
            "rows": ["level_1"],
            "columns": [],
            "data": ["quantite"],
            "filters": {}
        }
    }
    create_response = client.post("/api/pivot-configs", json=config_data)
    config_id = create_response.json()["id"]

    # Delete config
    response = client.delete(f"/api/pivot-configs/{config_id}", params={"property_id": property_id})
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/pivot-configs/{config_id}", params={"property_id": property_id})
    assert get_response.status_code == 404


def test_delete_pivot_config_not_found(property_id):
    """Test deleting a non-existent pivot config."""
    response = client.delete("/api/pivot-configs/999", params={"property_id": property_id})
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
