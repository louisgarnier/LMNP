"""
Tests pour l'endpoint preview mappings (Step 3.7.2).

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


def test_preview_mapping_endpoint():
    """Test endpoint POST /api/mappings/preview"""
    print("\n📋 Test 1: POST /api/mappings/preview")
    
    init_database()
    
    # Créer un fichier Excel de test
    excel_file = create_test_excel_file()
    file_data = ("test_mappings.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    response = client.post(
        "/api/mappings/preview",
        files={"file": file_data}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    print(f"📊 Réponse: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Vérifier les champs obligatoires
    assert "filename" in data, "❌ Champ filename manquant"
    assert "total_rows" in data, "❌ Champ total_rows manquant"
    assert "column_mapping" in data, "❌ Champ column_mapping manquant"
    assert "preview" in data, "❌ Champ preview manquant"
    assert "stats" in data, "❌ Champ stats manquant"
    
    # Vérifier le contenu
    assert data["filename"] == "test_mappings.xlsx", f"❌ Filename incorrect: {data['filename']}"
    assert data["total_rows"] == 3, f"❌ Total rows incorrect: {data['total_rows']}"
    assert len(data["column_mapping"]) > 0, "❌ Mapping des colonnes vide"
    assert len(data["preview"]) > 0, "❌ Preview vide"
    assert len(data["preview"]) <= 10, "❌ Preview contient plus de 10 lignes"
    
    # Vérifier que les colonnes obligatoires sont détectées
    mapped_db_columns = [m["db_column"] for m in data["column_mapping"]]
    assert "nom" in mapped_db_columns, "❌ Colonne 'nom' non détectée"
    assert "level_1" in mapped_db_columns, "❌ Colonne 'level_1' non détectée"
    assert "level_2" in mapped_db_columns, "❌ Colonne 'level_2' non détectée"
    
    print(f"✅ Preview réussi: {data['filename']}, {len(data['preview'])} lignes")
    print(f"✅ Colonnes détectées: {', '.join(mapped_db_columns)}")
    print("✅ Test réussi")


def test_preview_mapping_endpoint_invalid_file():
    """Test endpoint POST /api/mappings/preview avec fichier invalide"""
    print("\n📋 Test 2: POST /api/mappings/preview (fichier invalide)")
    
    init_database()
    
    # Créer un fichier CSV (pas Excel)
    csv_content = "Nom;Level 1;Level 2\nPRLV SEPA;CHARGES;FRAIS BANCAIRES"
    file_data = ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    
    response = client.post(
        "/api/mappings/preview",
        files={"file": file_data}
    )
    
    assert response.status_code == 400, f"❌ Status code attendu: 400, obtenu: {response.status_code}"
    assert "Excel" in response.json()["detail"], "❌ Message d'erreur incorrect"
    
    print("✅ Erreur correcte pour fichier non Excel")


def test_preview_mapping_endpoint_empty_file():
    """Test endpoint POST /api/mappings/preview avec fichier vide"""
    print("\n📋 Test 3: POST /api/mappings/preview (fichier vide)")
    
    init_database()
    
    # Créer un fichier Excel vide
    df = pd.DataFrame()
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    file_data = ("empty.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    response = client.post(
        "/api/mappings/preview",
        files={"file": file_data}
    )
    
    assert response.status_code == 400, f"❌ Status code attendu: 400, obtenu: {response.status_code}"
    assert "vide" in response.json()["detail"].lower(), "❌ Message d'erreur incorrect"
    
    print("✅ Erreur correcte pour fichier vide")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests Step 3.7.2 - Endpoint preview mappings")
    print("=" * 60)
    
    try:
        test_preview_mapping_endpoint()
        test_preview_mapping_endpoint_invalid_file()
        test_preview_mapping_endpoint_empty_file()
        
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

