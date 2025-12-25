"""
Tests for amortization configuration endpoints.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.main import app
from backend.database.connection import get_db, init_database
from backend.database.models import AmortizationConfig, Base
from backend.database.connection import engine

# Initialize database
init_database()

client = TestClient(app)


def setup_test_db():
    """Setup test database - create tables and clean up."""
    Base.metadata.create_all(bind=engine)
    # Clean up existing configs
    db = next(get_db())
    try:
        db.query(AmortizationConfig).delete()
        db.commit()
    finally:
        db.close()


def test_get_config_not_found():
    """Test GET /api/amortization/config when no config exists."""
    setup_test_db()
    
    response = client.get("/api/amortization/config")
    
    assert response.status_code == 404
    assert "Aucune configuration" in response.json()["detail"]


def test_create_config():
    """Test PUT /api/amortization/config - create new config."""
    setup_test_db()
    
    config_data = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture", "Meubles"],
            "travaux": ["Construction work", "Travaux"],
            "construction": ["Construction loan", "Pret construction"],
            "terrain": ["Land loan", "Pret terrain"]
        },
        "duration_meubles": 10,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    
    response = client.put("/api/amortization/config", json=config_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["level_2_value"] == "ammortissements"
    assert data["duration_meubles"] == 10
    assert data["duration_travaux"] == 20
    assert data["duration_construction"] == 25
    assert data["duration_terrain"] == 30
    assert "meubles" in data["level_3_mapping"]
    assert "Furniture" in data["level_3_mapping"]["meubles"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_config_after_create():
    """Test GET /api/amortization/config after creating config."""
    setup_test_db()
    
    # Create config
    config_data = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture"],
            "travaux": ["Construction work"],
            "construction": ["Construction loan"],
            "terrain": ["Land loan"]
        },
        "duration_meubles": 10,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    client.put("/api/amortization/config", json=config_data)
    
    # Get config
    response = client.get("/api/amortization/config")
    
    assert response.status_code == 200
    data = response.json()
    assert data["level_2_value"] == "ammortissements"
    assert data["duration_meubles"] == 10


def test_update_config():
    """Test PUT /api/amortization/config - update existing config."""
    setup_test_db()
    
    # Create initial config
    initial_config = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture"],
            "travaux": ["Construction work"],
            "construction": ["Construction loan"],
            "terrain": ["Land loan"]
        },
        "duration_meubles": 10,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    create_response = client.put("/api/amortization/config", json=initial_config)
    config_id = create_response.json()["id"]
    
    # Update config
    updated_config = {
        "level_2_value": "ammort",
        "level_3_mapping": {
            "meubles": ["Furniture", "Meubles"],
            "travaux": ["Construction work"],
            "construction": ["Construction loan"],
            "terrain": ["Land loan"]
        },
        "duration_meubles": 15,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    update_response = client.put("/api/amortization/config", json=updated_config)
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == config_id  # Same ID (singleton)
    assert data["level_2_value"] == "ammort"  # Updated
    assert data["duration_meubles"] == 15  # Updated
    assert len(data["level_3_mapping"]["meubles"]) == 2  # Updated mapping


def test_config_validation_missing_keys():
    """Test PUT /api/amortization/config - validation error if missing required keys."""
    setup_test_db()
    
    config_data = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture"],
            "travaux": ["Construction work"]
            # Missing "construction" and "terrain"
        },
        "duration_meubles": 10,
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    
    response = client.put("/api/amortization/config", json=config_data)
    
    assert response.status_code == 400
    assert "meubles, travaux, construction, terrain" in response.json()["detail"]


def test_config_validation_duration_min():
    """Test PUT /api/amortization/config - validation error if duration < 1."""
    setup_test_db()
    
    config_data = {
        "level_2_value": "ammortissements",
        "level_3_mapping": {
            "meubles": ["Furniture"],
            "travaux": ["Construction work"],
            "construction": ["Construction loan"],
            "terrain": ["Land loan"]
        },
        "duration_meubles": 0,  # Invalid: must be >= 1
        "duration_travaux": 20,
        "duration_construction": 25,
        "duration_terrain": 30
    }
    
    response = client.put("/api/amortization/config", json=config_data)
    
    assert response.status_code == 422  # Validation error from Pydantic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

