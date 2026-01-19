"""
Test script for Step 10.2: Backend - Endpoint d'extraction des transactions

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Transaction
from fastapi.testclient import TestClient
from backend.api.main import app

def test_export_transactions_excel():
    """Test l'export des transactions en format Excel"""
    print("=" * 60)
    print("Test 1: Export Excel")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester l'export Excel
    response = client.get("/api/transactions/export?format=excel")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", \
        f"Content-Type incorrect: {response.headers['content-type']}"
    assert "attachment" in response.headers["content-disposition"], \
        "Content-Disposition doit contenir 'attachment'"
    assert "transactions_" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir 'transactions_'"
    assert ".xlsx" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir '.xlsx'"
    
    # Vérifier que le contenu est bien un fichier Excel
    assert len(response.content) > 0, "Le fichier ne doit pas être vide"
    assert response.content[:2] == b'PK', "Le fichier doit commencer par 'PK' (signature ZIP/Excel)"
    
    print("✅ Export Excel: OK")
    print(f"   Taille du fichier: {len(response.content)} bytes")
    print(f"   Content-Disposition: {response.headers['content-disposition']}")
    print()


def test_export_transactions_csv():
    """Test l'export des transactions en format CSV"""
    print("=" * 60)
    print("Test 2: Export CSV")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester l'export CSV
    response = client.get("/api/transactions/export?format=csv")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert "text/csv" in response.headers["content-type"], \
        f"Content-Type incorrect: {response.headers['content-type']}"
    assert "attachment" in response.headers["content-disposition"], \
        "Content-Disposition doit contenir 'attachment'"
    assert "transactions_" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir 'transactions_'"
    assert ".csv" in response.headers["content-disposition"], \
        "Nom de fichier doit contenir '.csv'"
    
    # Vérifier le contenu CSV
    content = response.content.decode('utf-8-sig')
    lines = content.strip().split('\n')
    assert len(lines) > 1, "Le CSV doit contenir au moins une ligne d'en-tête et des données"
    
    # Vérifier les colonnes
    header = lines[0]
    expected_columns = ['id', 'date', 'quantite', 'nom', 'solde', 'level_1', 'level_2', 'level_3', 'source_file', 'created_at', 'updated_at']
    for col in expected_columns:
        assert col in header, f"Colonne '{col}' manquante dans l'en-tête CSV"
    
    print("✅ Export CSV: OK")
    print(f"   Nombre de lignes: {len(lines)}")
    print(f"   En-tête: {header[:100]}...")
    print(f"   Content-Disposition: {response.headers['content-disposition']}")
    print()


def test_export_transactions_with_filters():
    """Test l'export avec filtres"""
    print("=" * 60)
    print("Test 3: Export avec filtres")
    print("=" * 60)
    
    # D'abord, trouver une plage de dates qui contient des transactions
    from backend.database.connection import get_db
    from backend.database.models import Transaction
    from datetime import date
    
    db = next(get_db())
    first_trans = db.query(Transaction).order_by(Transaction.date).first()
    
    if not first_trans:
        print("ℹ️  Aucune transaction dans la base, test ignoré")
        return
    
    # Utiliser l'année de la première transaction
    test_year = first_trans.date.year
    start_date = date(test_year, 1, 1)
    end_date = date(test_year, 12, 31)
    
    client = TestClient(app)
    
    # Tester avec un filtre de date
    response = client.get(f"/api/transactions/export?format=csv&start_date={start_date}&end_date={end_date}")
    
    # Si 404, c'est qu'il n'y a pas de transactions dans cette plage (acceptable)
    if response.status_code == 404:
        print(f"ℹ️  Aucune transaction dans la plage {start_date} - {end_date}, test ignoré")
        return
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    
    content = response.content.decode('utf-8-sig')
    lines = content.strip().split('\n')
    
    # Vérifier que les dates sont dans la plage (si des transactions existent)
    if len(lines) > 1:
        # Parser quelques lignes pour vérifier les dates
        import csv
        from io import StringIO
        csv_reader = csv.DictReader(StringIO(content))
        for row in list(csv_reader)[:5]:  # Vérifier les 5 premières lignes
            if row['date']:
                from datetime import datetime
                trans_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                assert trans_date >= start_date, \
                    f"Date {trans_date} est avant {start_date}"
                assert trans_date <= end_date, \
                    f"Date {trans_date} est après {end_date}"
    
    print("✅ Export avec filtres: OK")
    print(f"   Plage de dates: {start_date} - {end_date}")
    print(f"   Nombre de lignes (avec filtres): {len(lines) - 1}")
    print()


def test_export_transactions_default_format():
    """Test que le format par défaut est Excel"""
    print("=" * 60)
    print("Test 4: Format par défaut (Excel)")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Tester sans paramètre format (doit être Excel par défaut)
    response = client.get("/api/transactions/export")
    
    assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", \
        "Le format par défaut doit être Excel"
    assert ".xlsx" in response.headers["content-disposition"], \
        "Le format par défaut doit être Excel (.xlsx)"
    
    print("✅ Format par défaut: OK (Excel)")
    print()


def test_export_transactions_data_integrity():
    """Test que les données exportées correspondent aux données en base"""
    print("=" * 60)
    print("Test 5: Intégrité des données")
    print("=" * 60)
    
    db = next(get_db())
    
    # Récupérer les transactions depuis la base
    transactions_from_db = db.query(Transaction).count()
    
    # Exporter en CSV et compter les lignes
    client = TestClient(app)
    response = client.get("/api/transactions/export?format=csv")
    
    content = response.content.decode('utf-8-sig')
    lines = content.strip().split('\n')
    csv_count = len(lines) - 1  # -1 pour l'en-tête
    
    assert csv_count == transactions_from_db, \
        f"Nombre de transactions incorrect: DB={transactions_from_db}, CSV={csv_count}"
    
    print(f"✅ Intégrité des données: OK")
    print(f"   Transactions en base: {transactions_from_db}")
    print(f"   Lignes dans le CSV: {csv_count} (sans en-tête)")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTS - Step 10.2: Endpoint d'extraction des transactions")
    print("=" * 60)
    print()
    
    try:
        test_export_transactions_excel()
        test_export_transactions_csv()
        test_export_transactions_with_filters()
        test_export_transactions_default_format()
        test_export_transactions_data_integrity()
        
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
