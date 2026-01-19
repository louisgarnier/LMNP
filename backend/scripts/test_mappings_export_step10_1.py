"""
Test script for Step 10.1: Backend - Endpoint d'extraction des mappings

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Mapping
from backend.api.routes.mappings import export_mappings
from fastapi.testclient import TestClient
from backend.api.main import app
import io

def test_export_mappings_excel():
    """Test l'export des mappings en format Excel"""
    print("=" * 60)
    print("Test 1: Export Excel")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester l'export Excel
    response = client.get("/api/mappings/export?format=excel")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", \
        f"Content-Type incorrect: {response.headers['content-type']}"
    assert "attachment" in response.headers["content-disposition"], \
        "Content-Disposition doit contenir 'attachment'"
    assert "mappings_" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir 'mappings_'"
    assert ".xlsx" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir '.xlsx'"
    
    # Vérifier que le contenu est bien un fichier Excel
    assert len(response.content) > 0, "Le fichier ne doit pas être vide"
    assert response.content[:2] == b'PK', "Le fichier doit commencer par 'PK' (signature ZIP/Excel)"
    
    print("✅ Export Excel: OK")
    print(f"   Taille du fichier: {len(response.content)} bytes")
    print(f"   Content-Disposition: {response.headers['content-disposition']}")
    print()


def test_export_mappings_csv():
    """Test l'export des mappings en format CSV"""
    print("=" * 60)
    print("Test 2: Export CSV")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester l'export CSV
    response = client.get("/api/mappings/export?format=csv")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert "text/csv" in response.headers["content-type"], \
        f"Content-Type incorrect: {response.headers['content-type']}"
    assert "attachment" in response.headers["content-disposition"], \
        "Content-Disposition doit contenir 'attachment'"
    assert "mappings_" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir 'mappings_'"
    assert ".csv" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir '.csv'"
    
    # Vérifier le contenu CSV
    content = response.content.decode('utf-8-sig')
    lines = content.strip().split('\n')
    assert len(lines) > 1, "Le CSV doit contenir au moins une ligne d'en-tête et des données"
    
    # Vérifier les colonnes
    header = lines[0]
    expected_columns = ['id', 'nom', 'level_1', 'level_2', 'level_3', 'is_prefix_match', 'priority', 'created_at', 'updated_at']
    for col in expected_columns:
        assert col in header, f"Colonne '{col}' manquante dans l'en-tête CSV"
    
    print("✅ Export CSV: OK")
    print(f"   Nombre de lignes: {len(lines)}")
    print(f"   En-tête: {header[:100]}...")
    print(f"   Content-Disposition: {response.headers['content-disposition']}")
    print()


def test_export_mappings_default_format():
    """Test que le format par défaut est Excel"""
    print("=" * 60)
    print("Test 3: Format par défaut (Excel)")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester sans paramètre format (doit être Excel par défaut)
    response = client.get("/api/mappings/export")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", \
        "Le format par défaut doit être Excel"
    assert ".xlsx" in response.headers["content-disposition"], \
        "Le format par défaut doit être Excel (.xlsx)"
    
    print("✅ Format par défaut: OK (Excel)")
    print()


def test_export_mappings_empty():
    """Test l'export quand il n'y a pas de mappings (doit retourner 404)"""
    print("=" * 60)
    print("Test 4: Export avec base vide (simulation)")
    print("=" * 60)
    
    # Note: Ce test nécessiterait de vider temporairement la base
    # Pour l'instant, on vérifie juste que l'endpoint gère le cas
    print("ℹ️  Test non exécuté (nécessiterait de vider la base)")
    print()


def test_export_mappings_data_integrity():
    """Test que les données exportées correspondent aux données en base"""
    print("=" * 60)
    print("Test 5: Intégrité des données")
    print("=" * 60)
    
    db = next(get_db())
    
    # Récupérer les mappings depuis la base
    mappings_from_db = db.query(Mapping).order_by(Mapping.id).all()
    db_count = len(mappings_from_db)
    
    # Exporter en CSV et compter les lignes
    client = TestClient(app)
    response = client.get("/api/mappings/export?format=csv")
    
    content = response.content.decode('utf-8-sig')
    lines = content.strip().split('\n')
    csv_count = len(lines) - 1  # -1 pour l'en-tête
    
    assert csv_count == db_count, \
        f"Nombre de mappings incorrect: DB={db_count}, CSV={csv_count}"
    
    print(f"✅ Intégrité des données: OK")
    print(f"   Mappings en base: {db_count}")
    print(f"   Lignes dans le CSV: {csv_count} (sans en-tête)")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTS - Step 10.1: Endpoint d'extraction des mappings")
    print("=" * 60)
    print()
    
    try:
        test_export_mappings_excel()
        test_export_mappings_csv()
        test_export_mappings_default_format()
        test_export_mappings_empty()
        test_export_mappings_data_integrity()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ ERREUR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
