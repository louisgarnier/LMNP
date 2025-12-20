"""
Tests pour l'endpoint import mappings (Step 3.7.3).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import io
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import SessionLocal, init_database
from backend.database.models import Mapping, MappingImport

client = TestClient(app)


def create_test_excel_file() -> io.BytesIO:
    """Crée un fichier Excel de test en mémoire."""
    # Créer un DataFrame de test
    data = {
        'Nom': ['PRLV SEPA', 'VIR STRIPE', 'CARTE'],
        'Level 1': ['CHARGES', 'PRODUITS', 'CHARGES'],
        'Level 2': ['FRAIS BANCAIRES', 'REVENUS LOCATIFS', 'FRAIS BANCAIRES'],
        'Level 3': ['PRLV', 'STRIPE', 'CARTE BLEUE']
    }
    df = pd.DataFrame(data)
    
    # Créer un fichier Excel en mémoire
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return excel_buffer


def setup_test_db():
    """Initialise la BDD de test."""
    init_database()
    db = SessionLocal()
    try:
        # Nettoyer les données de test
        db.query(Mapping).delete()
        db.query(MappingImport).delete()
        db.commit()
    finally:
        db.close()


def test_import_mapping_endpoint():
    """Test endpoint POST /api/mappings/import"""
    print("\n📋 Test 1: POST /api/mappings/import")
    
    setup_test_db()
    
    # Créer un fichier Excel de test
    excel_file = create_test_excel_file()
    file_data = ("test_mappings.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    # Mapping des colonnes
    mapping = [
        {"file_column": "Nom", "db_column": "nom"},
        {"file_column": "Level 1", "db_column": "level_1"},
        {"file_column": "Level 2", "db_column": "level_2"},
        {"file_column": "Level 3", "db_column": "level_3"}
    ]
    
    response = client.post(
        "/api/mappings/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    print(f"📊 Réponse: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Vérifier les champs obligatoires
    assert "filename" in data, "❌ Champ filename manquant"
    assert "imported_count" in data, "❌ Champ imported_count manquant"
    assert "duplicates_count" in data, "❌ Champ duplicates_count manquant"
    assert "errors_count" in data, "❌ Champ errors_count manquant"
    assert "message" in data, "❌ Champ message manquant"
    
    # Vérifier le contenu
    assert data["filename"] == "test_mappings.xlsx", f"❌ Filename incorrect: {data['filename']}"
    assert data["imported_count"] == 3, f"❌ Imported count incorrect: {data['imported_count']} (attendu: 3)"
    assert data["duplicates_count"] == 0, f"❌ Duplicates count incorrect: {data['duplicates_count']}"
    assert data["errors_count"] == 0, f"❌ Errors count incorrect: {data['errors_count']}"
    
    # Vérifier en BDD
    db = SessionLocal()
    try:
        count = db.query(Mapping).count()
        assert count == 3, f"❌ Nombre de mappings en BDD incorrect: {count} (attendu: 3)"
        
        # Vérifier un mapping spécifique
        mapping_prlv = db.query(Mapping).filter(Mapping.nom == "PRLV SEPA").first()
        assert mapping_prlv is not None, "❌ Mapping PRLV SEPA non trouvé"
        assert mapping_prlv.level_1 == "CHARGES", "❌ Level 1 incorrect"
        assert mapping_prlv.level_2 == "FRAIS BANCAIRES", "❌ Level 2 incorrect"
        assert mapping_prlv.level_3 == "PRLV", "❌ Level 3 incorrect"
        
        # Vérifier l'historique
        import_history = db.query(MappingImport).filter(MappingImport.filename == "test_mappings.xlsx").first()
        assert import_history is not None, "❌ Historique d'import non créé"
        assert import_history.imported_count == 3, "❌ Imported count dans historique incorrect"
        
        print("✅ Import réussi: 3 mappings créés")
        print("✅ Historique créé correctement")
    finally:
        db.close()


def test_import_mapping_endpoint_duplicates():
    """Test endpoint POST /api/mappings/import avec doublons"""
    print("\n📋 Test 2: POST /api/mappings/import (doublons)")
    
    setup_test_db()
    
    # Créer un mapping existant en BDD
    db = SessionLocal()
    try:
        existing_mapping = Mapping(
            nom="PRLV SEPA",
            level_1="CHARGES",
            level_2="FRAIS BANCAIRES",
            level_3="PRLV"
        )
        db.add(existing_mapping)
        db.commit()
    finally:
        db.close()
    
    # Créer un fichier Excel avec un doublon
    excel_file = create_test_excel_file()
    file_data = ("test_duplicates.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    mapping = [
        {"file_column": "Nom", "db_column": "nom"},
        {"file_column": "Level 1", "db_column": "level_1"},
        {"file_column": "Level 2", "db_column": "level_2"},
        {"file_column": "Level 3", "db_column": "level_3"}
    ]
    
    response = client.post(
        "/api/mappings/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert data["duplicates_count"] == 1, f"❌ Duplicates count incorrect: {data['duplicates_count']} (attendu: 1)"
    assert data["imported_count"] == 2, f"❌ Imported count incorrect: {data['imported_count']} (attendu: 2)"
    assert len(data["duplicates"]) == 1, f"❌ Liste de doublons incorrecte: {len(data['duplicates'])}"
    assert data["duplicates"][0]["nom"] == "PRLV SEPA", "❌ Nom du doublon incorrect"
    
    print("✅ Gestion des doublons fonctionne correctement")


def test_import_mapping_endpoint_errors():
    """Test endpoint POST /api/mappings/import avec erreurs"""
    print("\n📋 Test 3: POST /api/mappings/import (erreurs)")
    
    setup_test_db()
    
    # Créer un fichier Excel avec des erreurs (nom vide, level_1 vide)
    data = {
        'Nom': ['PRLV SEPA', '', 'CARTE'],
        'Level 1': ['CHARGES', 'PRODUITS', ''],
        'Level 2': ['FRAIS BANCAIRES', 'REVENUS LOCATIFS', 'FRAIS BANCAIRES'],
        'Level 3': ['PRLV', 'STRIPE', 'CARTE BLEUE']
    }
    df = pd.DataFrame(data)
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    file_data = ("test_errors.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    mapping = [
        {"file_column": "Nom", "db_column": "nom"},
        {"file_column": "Level 1", "db_column": "level_1"},
        {"file_column": "Level 2", "db_column": "level_2"},
        {"file_column": "Level 3", "db_column": "level_3"}
    ]
    
    response = client.post(
        "/api/mappings/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert data["errors_count"] == 2, f"❌ Errors count incorrect: {data['errors_count']} (attendu: 2)"
    assert data["imported_count"] == 1, f"❌ Imported count incorrect: {data['imported_count']} (attendu: 1)"
    assert len(data["errors"]) == 2, f"❌ Liste d'erreurs incorrecte: {len(data['errors'])}"
    
    # Vérifier les messages d'erreur
    error_messages = [e["error_message"] for e in data["errors"]]
    assert any("nom" in msg.lower() and "obligatoire" in msg.lower() for msg in error_messages), "❌ Message d'erreur pour nom manquant incorrect"
    assert any("level_1" in msg.lower() and "obligatoire" in msg.lower() for msg in error_messages), "❌ Message d'erreur pour level_1 manquant incorrect"
    
    print("✅ Gestion des erreurs fonctionne correctement")


def test_import_mapping_endpoint_existing_file():
    """Test endpoint POST /api/mappings/import avec fichier déjà chargé"""
    print("\n📋 Test 4: POST /api/mappings/import (fichier déjà chargé)")
    
    setup_test_db()
    
    # Créer un import existant
    db = SessionLocal()
    try:
        existing_import = MappingImport(
            filename="test_existing.xlsx",
            imported_count=5,
            duplicates_count=1,
            errors_count=0
        )
        db.add(existing_import)
        db.commit()
    finally:
        db.close()
    
    # Importer le même fichier
    excel_file = create_test_excel_file()
    file_data = ("test_existing.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    mapping = [
        {"file_column": "Nom", "db_column": "nom"},
        {"file_column": "Level 1", "db_column": "level_1"},
        {"file_column": "Level 2", "db_column": "level_2"},
        {"file_column": "Level 3", "db_column": "level_3"}
    ]
    
    response = client.post(
        "/api/mappings/import",
        files={"file": file_data},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert "⚠️" in data["message"], "❌ Message d'avertissement manquant"
    
    # Vérifier que l'historique a été mis à jour (pas créé à nouveau)
    db = SessionLocal()
    try:
        import_count = db.query(MappingImport).filter(MappingImport.filename == "test_existing.xlsx").count()
        assert import_count == 1, f"❌ Nombre d'imports incorrect: {import_count} (attendu: 1)"
        
        updated_import = db.query(MappingImport).filter(MappingImport.filename == "test_existing.xlsx").first()
        assert updated_import.imported_count == 3, f"❌ Imported count mis à jour incorrect: {updated_import.imported_count}"
    finally:
        db.close()
    
    print("✅ Gestion fichier déjà chargé fonctionne correctement")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests Step 3.7.3 - Endpoint import mappings")
    print("=" * 60)
    
    try:
        test_import_mapping_endpoint()
        test_import_mapping_endpoint_duplicates()
        test_import_mapping_endpoint_errors()
        test_import_mapping_endpoint_existing_file()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

