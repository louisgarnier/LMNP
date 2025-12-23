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
from backend.database.models import PivotConfig

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


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_pivot_config():
    """Test creating a pivot config."""
    config_data = {
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


def test_create_pivot_config_duplicate_name():
    """Test creating a pivot config with duplicate name."""
    config_data = {
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


def test_get_pivot_configs():
    """Test getting list of pivot configs."""
    # Create two configs
    config1 = {
        "name": "Config 1",
        "config": {"rows": ["level_1"], "columns": [], "data": ["quantite"], "filters": {}}
    }
    config2 = {
        "name": "Config 2",
        "config": {"rows": ["level_2"], "columns": [], "data": ["quantite"], "filters": {}}
    }
    
    client.post("/api/pivot-configs", json=config1)
    client.post("/api/pivot-configs", json=config2)
    
    # Get all configs
    response = client.get("/api/pivot-configs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] in ["Config 1", "Config 2"]
    assert data["items"][1]["name"] in ["Config 1", "Config 2"]


def test_get_pivot_config():
    """Test getting a single pivot config."""
    config_data = {
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
    response = client.get(f"/api/pivot-configs/{config_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Config"
    assert data["config"]["rows"] == ["level_1", "level_2"]
    assert data["config"]["filters"]["level_1"] == "Achat"


def test_get_pivot_config_not_found():
    """Test getting a non-existent pivot config."""
    response = client.get("/api/pivot-configs/999")
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


def test_update_pivot_config():
    """Test updating a pivot config."""
    # Create config
    config_data = {
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
    response = client.put(f"/api/pivot-configs/{config_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert len(data["config"]["rows"]) == 2
    assert "mois" in data["config"]["columns"]


def test_update_pivot_config_partial():
    """Test partial update of a pivot config."""
    # Create config
    config_data = {
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
    response = client.put(f"/api/pivot-configs/{config_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["config"]["rows"] == ["level_1"]  # Config unchanged


def test_update_pivot_config_not_found():
    """Test updating a non-existent pivot config."""
    update_data = {
        "name": "Updated Name",
        "config": {"rows": ["level_1"], "columns": [], "data": ["quantite"], "filters": {}}
    }
    response = client.put("/api/pivot-configs/999", json=update_data)
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


def test_delete_pivot_config():
    """Test deleting a pivot config."""
    # Create config
    config_data = {
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
    response = client.delete(f"/api/pivot-configs/{config_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/pivot-configs/{config_id}")
    assert get_response.status_code == 404


def test_delete_pivot_config_not_found():
    """Test deleting a non-existent pivot config."""
    response = client.delete("/api/pivot-configs/999")
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

