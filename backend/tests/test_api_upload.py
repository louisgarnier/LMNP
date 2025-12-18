"""
Tests pour les endpoints API upload (preview et import).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, FileImport

client = TestClient(app)


def setup_test_db():
    """Initialise la BDD de test."""
    init_database()
    db = SessionLocal()
    try:
        # Nettoyer les données de test
        db.query(Transaction).delete()
        db.query(FileImport).delete()
        db.commit()
    finally:
        db.close()


def test_preview_endpoint():
    """Test endpoint POST /api/transactions/preview"""
    print("\n📋 Test 1: POST /api/transactions/preview")
    
    setup_test_db()
    
    # Créer un fichier CSV de test
    csv_content = "Date;amount;name;Solde\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A;-15\n02/09/2021;1000;VIR INST LOUIS GARNIER;985"
    file_data = ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    
    response = client.post(
        "/api/transactions/preview",
        files={"file": file_data}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert "filename" in data, "❌ Champ filename manquant"
    assert "encoding" in data, "❌ Champ encoding manquant"
    assert "separator" in data, "❌ Champ separator manquant"
    assert "column_mapping" in data, "❌ Champ column_mapping manquant"
    assert "preview" in data, "❌ Champ preview manquant"
    assert len(data["column_mapping"]) > 0, "❌ Mapping des colonnes vide"
    assert len(data["preview"]) > 0, "❌ Preview vide"
    
    print(f"✅ Preview réussi: {data['filename']}, {len(data['preview'])} lignes")
    print("✅ Test réussi")


def test_import_endpoint():
    """Test endpoint POST /api/transactions/import"""
    print("\n📋 Test 2: POST /api/transactions/import")
    
    setup_test_db()
    
    # Créer un fichier CSV de test (SANS colonne Solde, elle sera calculée automatiquement)
    csv_content = "Date;amount;name\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A\n02/09/2021;1000;VIR INST LOUIS GARNIER"
    file_data = ("test_import.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    
    # Mapping des colonnes (SANS solde, il sera calculé automatiquement)
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"}
    ]
    
    response = client.post(
        "/api/transactions/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert "imported_count" in data, "❌ Champ imported_count manquant"
    assert "duplicates_count" in data, "❌ Champ duplicates_count manquant"
    assert data["imported_count"] == 2, f"❌ Nombre de transactions importées attendu: 2, obtenu: {data['imported_count']}"
    
    # Vérifier en BDD
    db = SessionLocal()
    try:
        count = db.query(Transaction).count()
        assert count == 2, f"❌ Nombre de transactions en BDD attendu: 2, obtenu: {count}"
        
        # Vérifier file_import
        file_import = db.query(FileImport).filter(FileImport.filename == "test_import.csv").first()
        assert file_import is not None, "❌ FileImport non créé"
        assert file_import.imported_count == 2, f"❌ imported_count attendu: 2, obtenu: {file_import.imported_count}"
    finally:
        db.close()
    
    print(f"✅ Import réussi: {data['imported_count']} transactions importées")
    print("✅ Test réussi")


def test_import_duplicate_file():
    """Test import du même fichier deux fois (doit échouer)"""
    print("\n📋 Test 3: Import fichier déjà chargé")
    
    setup_test_db()
    
    csv_content = "Date;amount;name;Solde\n17/08/2021;-15;TEST;-15"
    file_data = ("duplicate_test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"},
        {"file_column": "Solde", "db_column": "solde"}
    ]
    
    # Premier import
    response1 = client.post(
        "/api/transactions/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    assert response1.status_code == 200, "❌ Premier import devrait réussir"
    
    # Deuxième import (même fichier)
    file_data2 = ("duplicate_test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    response2 = client.post(
        "/api/transactions/import",
        files={"file": file_data2},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response2.status_code == 400, f"❌ Deuxième import devrait échouer avec 400, obtenu: {response2.status_code}"
    assert "déjà été chargé" in response2.json()["detail"], "❌ Message d'erreur incorrect"
    
    print("✅ Test fichier déjà chargé réussi")


def test_import_duplicate_transactions():
    """Test détection doublons de transactions"""
    print("\n📋 Test 4: Détection doublons de transactions")
    
    setup_test_db()
    
    # Insérer une transaction en BDD
    db = SessionLocal()
    try:
        from datetime import date
        transaction = Transaction(
            date=date(2021, 8, 17),
            quantite=-15.0,
            nom="SOUSCRIPTION PART SOCIALE A",
            solde=-15.0,
            source_file="existing.csv"
        )
        db.add(transaction)
        db.commit()
    finally:
        db.close()
    
    # Importer un fichier avec la même transaction
    csv_content = "Date;amount;name;Solde\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A;-15\n02/09/2021;1000;NOUVEAU;985"
    file_data = ("duplicate_trans.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"},
        {"file_column": "Solde", "db_column": "solde"}
    ]
    
    response = client.post(
        "/api/transactions/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert data["duplicates_count"] == 1, f"❌ Nombre de doublons attendu: 1, obtenu: {data['duplicates_count']}"
    assert data["imported_count"] == 1, f"❌ Nombre de transactions importées attendu: 1, obtenu: {data['imported_count']}"
    assert len(data["duplicates"]) == 1, f"❌ Liste des doublons devrait contenir 1 élément, obtenu: {len(data['duplicates'])}"
    
    # Vérifier en BDD (2 transactions au total: 1 existante + 1 nouvelle)
    db = SessionLocal()
    try:
        count = db.query(Transaction).count()
        assert count == 2, f"❌ Nombre de transactions en BDD attendu: 2, obtenu: {count}"
    finally:
        db.close()
    
    print(f"✅ Détection doublons réussie: {data['duplicates_count']} doublon(s)")
    print("✅ Test réussi")


def test_get_imports_history():
    """Test endpoint GET /api/transactions/imports"""
    print("\n📋 Test 5: GET /api/transactions/imports")
    
    setup_test_db()
    
    # Créer un import de test
    db = SessionLocal()
    try:
        file_import = FileImport(
            filename="test_history.csv",
            imported_count=5,
            duplicates_count=1,
            errors_count=0
        )
        db.add(file_import)
        db.commit()
    finally:
        db.close()
    
    response = client.get("/api/transactions/imports")
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert isinstance(data, list), "❌ La réponse devrait être une liste"
    assert len(data) >= 1, "❌ Au moins un import devrait être présent"
    
    # Vérifier le premier import
    first_import = data[0]
    assert "filename" in first_import, "❌ Champ filename manquant"
    assert "imported_count" in first_import, "❌ Champ imported_count manquant"
    
    print(f"✅ Historique récupéré: {len(data)} import(s)")
    print("✅ Test réussi")


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 60)
    print("🧪 Tests: API Upload Endpoints")
    print("=" * 60)
    
    try:
        test_preview_endpoint()
        test_import_endpoint()
        test_import_duplicate_file()
        test_import_duplicate_transactions()
        test_get_imports_history()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés avec succès!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()

