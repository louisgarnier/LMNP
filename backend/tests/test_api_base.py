"""
Test complet de l'API backend de base.

Ce test valide que l'API FastAPI fonctionne correctement avec tous les endpoints.

Run with: python3 backend/tests/test_api_base.py
Or: pytest backend/tests/test_api_base.py -v
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import init_database, get_db
from backend.database.models import Transaction


def test_api_health():
    """Test des endpoints de santé."""
    print("=" * 60)
    print("Test API Backend - Endpoints de Base")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test root endpoint
    print("\n1. Test endpoint root (/)...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data
    print("✓ Endpoint root fonctionne")
    
    # Test health endpoint
    print("\n2. Test endpoint health (/health)...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Endpoint health fonctionne")
    
    # Test documentation Swagger
    print("\n3. Test documentation Swagger (/docs)...")
    response = client.get("/docs")
    assert response.status_code == 200
    print("✓ Documentation Swagger accessible")
    
    # Test OpenAPI schema
    print("\n4. Test schéma OpenAPI (/openapi.json)...")
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "info" in schema
    assert schema["info"]["title"] == "LMNP API"
    print("✓ Schéma OpenAPI accessible")


def test_transactions_crud():
    """Test CRUD complet des transactions."""
    print("\n" + "=" * 60)
    print("Test CRUD Transactions")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Nettoyer les données de test
    db = next(get_db())
    db.query(Transaction).delete()
    db.commit()
    db.close()
    
    client = TestClient(app)
    
    # 1. Test GET /api/transactions (liste vide)
    print("\n1. Test GET /api/transactions (liste vide)...")
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["transactions"]) == 0
    print("✓ Liste vide retournée correctement")
    
    # 2. Test POST /api/transactions (création)
    print("\n2. Test POST /api/transactions (création)...")
    new_transaction = {
        "date": "2024-01-15",
        "quantite": 850.0,
        "nom": "VIR STRIPE PAYMENTS",
        "solde": 5000.0,
        "source_file": "test.csv"
    }
    response = client.post("/api/transactions", json=new_transaction)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["nom"] == "VIR STRIPE PAYMENTS"
    assert data["quantite"] == 850.0
    transaction_id = data["id"]
    print(f"✓ Transaction créée avec ID: {transaction_id}")
    
    # 3. Test GET /api/transactions/{id}
    print("\n3. Test GET /api/transactions/{id}...")
    response = client.get(f"/api/transactions/{transaction_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction_id
    assert data["nom"] == "VIR STRIPE PAYMENTS"
    print("✓ Transaction récupérée par ID")
    
    # 4. Test GET /api/transactions (liste avec données)
    print("\n4. Test GET /api/transactions (liste avec données)...")
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["transactions"]) == 1
    print("✓ Liste avec données retournée correctement")
    
    # 5. Test PUT /api/transactions/{id} (mise à jour)
    print("\n5. Test PUT /api/transactions/{id} (mise à jour)...")
    update_data = {
        "nom": "VIR STRIPE PAYMENTS UPDATED",
        "quantite": 900.0
    }
    response = client.put(f"/api/transactions/{transaction_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "VIR STRIPE PAYMENTS UPDATED"
    assert data["quantite"] == 900.0
    print("✓ Transaction mise à jour")
    
    # 6. Test filtres par date
    print("\n6. Test filtres par date...")
    # Créer une autre transaction avec date différente
    new_transaction2 = {
        "date": "2024-02-01",
        "quantite": 850.0,
        "nom": "VIR STRIPE PAYMENTS FEB",
        "solde": 5850.0,
        "source_file": "test.csv"
    }
    client.post("/api/transactions", json=new_transaction2)
    
    # Filtrer par date de début
    response = client.get("/api/transactions?start_date=2024-02-01")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    print("✓ Filtre par date fonctionne")
    
    # 7. Test DELETE /api/transactions/{id}
    print("\n7. Test DELETE /api/transactions/{id}...")
    response = client.delete(f"/api/transactions/{transaction_id}")
    assert response.status_code == 204
    print("✓ Transaction supprimée")
    
    # Vérifier qu'elle n'existe plus
    response = client.get(f"/api/transactions/{transaction_id}")
    assert response.status_code == 404
    print("✓ Transaction confirmée supprimée")
    
    # 8. Test pagination
    print("\n8. Test pagination...")
    # Créer plusieurs transactions
    for i in range(5):
        transaction = {
            "date": f"2024-03-{i+1:02d}",
            "quantite": 100.0 * (i + 1),
            "nom": f"Transaction {i+1}",
            "solde": 1000.0 * (i + 1),
            "source_file": "test.csv"
        }
        client.post("/api/transactions", json=transaction)
    
    # Test avec pagination
    response = client.get("/api/transactions?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["transactions"]) <= 3
    assert data["page"] == 1
    print("✓ Pagination fonctionne")
    
    print("\n" + "=" * 60)
    print("✓ TOUS LES TESTS CRUD SONT PASSÉS!")
    print("=" * 60)


def test_error_handling():
    """Test de la gestion des erreurs."""
    print("\n" + "=" * 60)
    print("Test Gestion des Erreurs")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test 404 - Transaction non trouvée
    print("\n1. Test 404 - Transaction non trouvée...")
    response = client.get("/api/transactions/99999")
    assert response.status_code == 404
    assert "non trouvée" in response.json()["detail"]
    print("✓ Erreur 404 gérée correctement")
    
    # Test validation - Données invalides
    print("\n2. Test validation - Données invalides...")
    invalid_transaction = {
        "date": "invalid-date",
        "quantite": "not-a-number"
    }
    response = client.post("/api/transactions", json=invalid_transaction)
    assert response.status_code == 422  # Unprocessable Entity
    print("✓ Validation des données fonctionne")
    
    print("\n" + "=" * 60)
    print("✓ TOUS LES TESTS DE GESTION D'ERREURS SONT PASSÉS!")
    print("=" * 60)


def main():
    """Exécuter tous les tests."""
    try:
        test_api_health()
        test_transactions_crud()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("✓ TOUS LES TESTS DE L'API SONT PASSÉS!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

