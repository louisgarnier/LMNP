"""
Test pour vérifier le calcul automatique du solde lors de l'import.

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


def test_balance_calculation_automatic():
    """
    Test que le solde est calculé automatiquement lors de l'import.
    - Solde initial = 0.0
    - Chaque transaction : solde = solde précédent + quantité
    - Les transactions sont triées par date
    """
    print("\n📋 Test: Calcul automatique du solde")
    
    setup_test_db()
    
    # Créer un fichier CSV SANS colonne solde
    csv_content = "Date;amount;name\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A\n02/09/2021;1000;VIR INST LOUIS GARNIER\n15/09/2021;-50;RETRAIT DAB"
    file_data = ("test_balance.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    
    # Mapping des colonnes (SANS solde)
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"}
    ]
    
    # 1. Preview pour vérifier que solde n'est pas proposé
    print("\n1️⃣ Test preview (vérifier que solde n'est pas dans le mapping)")
    file_data_preview = ("test_balance.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    response = client.post(
        "/api/transactions/preview",
        files={"file": file_data_preview}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    preview_data = response.json()
    suggested_mapping = preview_data.get("column_mapping", [])
    
    # Vérifier que solde n'est pas dans le mapping proposé
    solde_mappings = [m for m in suggested_mapping if m.get("db_column") == "solde"]
    assert len(solde_mappings) == 0, f"❌ Le mapping ne devrait pas contenir 'solde', trouvé: {solde_mappings}"
    print("✅ Solde n'est pas dans le mapping proposé")
    
    # 2. Import
    print("\n2️⃣ Test import avec calcul automatique du solde")
    file_data_import = ("test_balance.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    response = client.post(
        "/api/transactions/import",
        files={"file": file_data_import},
        data={"mapping": json.dumps(mapping)}
    )
    
    assert response.status_code == 200, f"❌ Status code attendu: 200, obtenu: {response.status_code}"
    
    data = response.json()
    assert data["imported_count"] == 3, f"❌ Nombre de transactions importées attendu: 3, obtenu: {data['imported_count']}"
    print(f"✅ {data['imported_count']} transactions importées")
    
    # 3. Vérifier les soldes en BDD
    print("\n3️⃣ Vérification des soldes calculés")
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).order_by(Transaction.date.asc(), Transaction.id.asc()).all()
        
        assert len(transactions) == 3, f"❌ Nombre de transactions en BDD attendu: 3, obtenu: {len(transactions)}"
        
        # Vérifier les soldes calculés
        # Transaction 1 (17/08/2021): -15 → solde = 0 + (-15) = -15
        assert transactions[0].quantite == -15.0, f"❌ Quantité transaction 1 attendue: -15, obtenue: {transactions[0].quantite}"
        assert transactions[0].solde == -15.0, f"❌ Solde transaction 1 attendu: -15, obtenu: {transactions[0].solde}"
        print(f"✅ Transaction 1: {transactions[0].date} | Quantité: {transactions[0].quantite} | Solde: {transactions[0].solde}")
        
        # Transaction 2 (02/09/2021): 1000 → solde = -15 + 1000 = 985
        assert transactions[1].quantite == 1000.0, f"❌ Quantité transaction 2 attendue: 1000, obtenue: {transactions[1].quantite}"
        assert transactions[1].solde == 985.0, f"❌ Solde transaction 2 attendu: 985, obtenu: {transactions[1].solde}"
        print(f"✅ Transaction 2: {transactions[1].date} | Quantité: {transactions[1].quantite} | Solde: {transactions[1].solde}")
        
        # Transaction 3 (15/09/2021): -50 → solde = 985 + (-50) = 935
        assert transactions[2].quantite == -50.0, f"❌ Quantité transaction 3 attendue: -50, obtenue: {transactions[2].quantite}"
        assert transactions[2].solde == 935.0, f"❌ Solde transaction 3 attendu: 935, obtenu: {transactions[2].solde}"
        print(f"✅ Transaction 3: {transactions[2].date} | Quantité: {transactions[2].quantite} | Solde: {transactions[2].solde}")
        
    finally:
        db.close()
    
    print("\n✅ Test réussi: Le solde est calculé automatiquement correctement!")


def test_balance_calculation_with_existing_transactions():
    """
    Test que le solde est calculé en tenant compte des transactions existantes en BDD.
    """
    print("\n📋 Test: Calcul du solde avec transactions existantes")
    
    setup_test_db()
    
    # 1. Créer une transaction existante en BDD
    db = SessionLocal()
    try:
        from datetime import date
        existing_transaction = Transaction(
            date=date(2021, 8, 1),
            quantite=500.0,
            nom="TRANSACTION EXISTANTE",
            solde=500.0,  # Solde initial
            source_file="manual"
        )
        db.add(existing_transaction)
        db.commit()
        print("✅ Transaction existante créée (solde: 500)")
    finally:
        db.close()
    
    # 2. Importer de nouvelles transactions
    csv_content = "Date;amount;name\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A\n02/09/2021;1000;VIR INST LOUIS GARNIER"
    file_data = ("test_balance_existing.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")
    
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
    assert data["imported_count"] == 2, f"❌ Nombre de transactions importées attendu: 2, obtenu: {data['imported_count']}"
    
    # 3. Vérifier que le solde continue depuis la transaction existante
    db = SessionLocal()
    try:
        # Récupérer toutes les transactions triées par date
        transactions = db.query(Transaction).order_by(Transaction.date.asc(), Transaction.id.asc()).all()
        
        assert len(transactions) == 3, f"❌ Nombre total de transactions attendu: 3, obtenu: {len(transactions)}"
        
        # Transaction existante (01/08/2021): solde = 500
        assert transactions[0].solde == 500.0, f"❌ Solde transaction existante attendu: 500, obtenu: {transactions[0].solde}"
        
        # Nouvelle transaction 1 (17/08/2021): solde = 500 + (-15) = 485
        new_trans_1 = [t for t in transactions if t.date == date(2021, 8, 17)][0]
        assert new_trans_1.solde == 485.0, f"❌ Solde nouvelle transaction 1 attendu: 485, obtenu: {new_trans_1.solde}"
        print(f"✅ Nouvelle transaction 1: {new_trans_1.date} | Quantité: {new_trans_1.quantite} | Solde: {new_trans_1.solde}")
        
        # Nouvelle transaction 2 (02/09/2021): solde = 485 + 1000 = 1485
        new_trans_2 = [t for t in transactions if t.date == date(2021, 9, 2)][0]
        assert new_trans_2.solde == 1485.0, f"❌ Solde nouvelle transaction 2 attendu: 1485, obtenu: {new_trans_2.solde}"
        print(f"✅ Nouvelle transaction 2: {new_trans_2.date} | Quantité: {new_trans_2.quantite} | Solde: {new_trans_2.solde}")
        
    finally:
        db.close()
    
    print("\n✅ Test réussi: Le solde continue correctement depuis les transactions existantes!")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Tests de calcul automatique du solde")
    print("=" * 60)
    
    try:
        test_balance_calculation_automatic()
        test_balance_calculation_with_existing_transactions()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

