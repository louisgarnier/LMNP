"""
Tests pour l'endpoint pivot (Step 4.1.1).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import get_db, init_database
from backend.database.models import Transaction, EnrichedTransaction
from datetime import date
import json

# Initialize database
init_database()

client = TestClient(app)


def setup_test_data(db):
    """Crée des données de test pour les tests pivot."""
    # Nettoyer les données existantes
    db.query(EnrichedTransaction).delete()
    db.query(Transaction).delete()
    db.commit()
    
    # Créer des transactions de test
    transactions = [
        Transaction(date=date(2024, 1, 15), quantite=1000.0, nom="CHARGES - Énergie", solde=5000.0),
        Transaction(date=date(2024, 1, 20), quantite=500.0, nom="CHARGES - Eau", solde=4500.0),
        Transaction(date=date(2024, 2, 10), quantite=1200.0, nom="CHARGES - Énergie", solde=3300.0),
        Transaction(date=date(2024, 2, 15), quantite=800.0, nom="CHARGES - Eau", solde=2500.0),
        Transaction(date=date(2024, 3, 12), quantite=1500.0, nom="PRODUITS - Loyers", solde=4000.0),
        Transaction(date=date(2024, 3, 18), quantite=2000.0, nom="PRODUITS - Loyers", solde=6000.0),
    ]
    
    for t in transactions:
        db.add(t)
    db.commit()
    
    # Créer des enriched transactions
    enriched = [
        EnrichedTransaction(transaction_id=1, mois=1, annee=2024, level_1="CHARGES", level_2="Énergie", level_3=None),
        EnrichedTransaction(transaction_id=2, mois=1, annee=2024, level_1="CHARGES", level_2="Eau", level_3=None),
        EnrichedTransaction(transaction_id=3, mois=2, annee=2024, level_1="CHARGES", level_2="Énergie", level_3=None),
        EnrichedTransaction(transaction_id=4, mois=2, annee=2024, level_1="CHARGES", level_2="Eau", level_3=None),
        EnrichedTransaction(transaction_id=5, mois=3, annee=2024, level_1="PRODUITS", level_2="Loyers", level_3=None),
        EnrichedTransaction(transaction_id=6, mois=3, annee=2024, level_1="PRODUITS", level_2="Loyers", level_3=None),
    ]
    
    for e in enriched:
        db.add(e)
    db.commit()
    
    print("✓ Données de test créées")


def test_pivot_level1_rows():
    """Test pivot avec level_1 en lignes uniquement."""
    print("\n" + "="*60)
    print("Test 1: Pivot avec level_1 en lignes uniquement")
    print("="*60)
    
    response = client.get("/api/analytics/pivot?rows=level_1&data_field=quantite&data_operation=sum")
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Rows: {data.get('rows')}")
    print(f"- Columns: {data.get('columns')}")
    print(f"- Data: {data.get('data')}")
    print(f"- Row totals: {data.get('row_totals')}")
    print(f"- Grand total: {data.get('grand_total')}")
    
    # Vérifications
    assert "rows" in data
    assert "data" in data
    assert "grand_total" in data
    
    # Vérifier que CHARGES et PRODUITS sont présents
    rows = data["rows"]
    assert any("CHARGES" in str(row) for row in rows), "CHARGES devrait être dans les lignes"
    assert any("PRODUITS" in str(row) for row in rows), "PRODUITS devrait être dans les lignes"
    
    # Vérifier le grand total (1000 + 500 + 1200 + 800 + 1500 + 2000 = 7000)
    assert abs(data["grand_total"] - 7000.0) < 0.01, f"Grand total incorrect: {data['grand_total']}, attendu: 7000.0"
    
    print("\n✅ TEST 1 RÉUSSI: Pivot avec level_1 en lignes fonctionne")


def test_pivot_level1_rows_mois_columns():
    """Test pivot avec level_1 en lignes et mois en colonnes."""
    print("\n" + "="*60)
    print("Test 2: Pivot avec level_1 en lignes, mois en colonnes")
    print("="*60)
    
    response = client.get("/api/analytics/pivot?rows=level_1&columns=mois&data_field=quantite&data_operation=sum")
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Rows: {data.get('rows')}")
    print(f"- Columns: {data.get('columns')}")
    print(f"- Data: {json.dumps(data.get('data'), indent=2)}")
    print(f"- Row totals: {data.get('row_totals')}")
    print(f"- Column totals: {data.get('column_totals')}")
    print(f"- Grand total: {data.get('grand_total')}")
    
    # Vérifications
    assert "rows" in data
    assert "columns" in data
    assert "data" in data
    assert len(data["columns"]) > 0, "Devrait avoir des colonnes (mois)"
    assert len(data["rows"]) > 0, "Devrait avoir des lignes (level_1)"
    
    # Vérifier que les mois 1, 2, 3 sont présents
    columns = data["columns"]
    # Les colonnes peuvent être des int ou des listes d'int
    column_values = []
    for col in columns:
        if isinstance(col, list):
            column_values.extend(col)
        else:
            column_values.append(col)
    assert 1 in column_values or any(1 in col for col in columns if isinstance(col, list)), "Mois 1 devrait être présent"
    assert 2 in column_values or any(2 in col for col in columns if isinstance(col, list)), "Mois 2 devrait être présent"
    assert 3 in column_values or any(3 in col for col in columns if isinstance(col, list)), "Mois 3 devrait être présent"
    
    print("\n✅ TEST 2 RÉUSSI: Pivot avec level_1 en lignes et mois en colonnes fonctionne")


def test_pivot_with_filters():
    """Test pivot avec filtres."""
    print("\n" + "="*60)
    print("Test 3: Pivot avec filtres (level_1 = CHARGES)")
    print("="*60)
    
    filters = json.dumps({"level_1": "CHARGES"})
    response = client.get(f"/api/analytics/pivot?rows=level_2&columns=mois&data_field=quantite&data_operation=sum&filters={filters}")
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Rows: {data.get('rows')}")
    print(f"- Columns: {data.get('columns')}")
    print(f"- Data: {json.dumps(data.get('data'), indent=2)}")
    print(f"- Grand total: {data.get('grand_total')}")
    
    # Vérifier que le grand total correspond aux CHARGES uniquement (1000 + 500 + 1200 + 800 = 3500)
    assert abs(data["grand_total"] - 3500.0) < 0.01, f"Grand total incorrect: {data['grand_total']}, attendu: 3500.0"
    
    print("\n✅ TEST 3 RÉUSSI: Pivot avec filtres fonctionne")


def test_pivot_multiple_rows():
    """Test pivot avec plusieurs champs en lignes."""
    print("\n" + "="*60)
    print("Test 4: Pivot avec level_1 et level_2 en lignes")
    print("="*60)
    
    response = client.get("/api/analytics/pivot?rows=level_1,level_2&columns=mois&data_field=quantite&data_operation=sum")
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Rows: {data.get('rows')}")
    print(f"- Columns: {data.get('columns')}")
    print(f"- Data: {json.dumps(data.get('data'), indent=2)}")
    print(f"- Grand total: {data.get('grand_total')}")
    
    # Vérifications
    assert "rows" in data
    assert len(data["rows"]) > 0, "Devrait avoir des lignes"
    
    print("\n✅ TEST 4 RÉUSSI: Pivot avec plusieurs champs en lignes fonctionne")


def test_pivot_invalid_field():
    """Test pivot avec un champ invalide."""
    print("\n" + "="*60)
    print("Test 5: Pivot avec champ invalide (devrait échouer)")
    print("="*60)
    
    response = client.get("/api/analytics/pivot?rows=invalid_field&data_field=quantite&data_operation=sum")
    
    assert response.status_code == 400, f"Devrait retourner 400, mais a retourné {response.status_code}"
    print(f"✓ Erreur attendue: {response.json()}")
    
    print("\n✅ TEST 5 RÉUSSI: Validation des champs fonctionne")


def test_pivot_details_simple():
    """Test endpoint details avec une cellule simple (level_1 = CHARGES, mois = 1)."""
    print("\n" + "="*60)
    print("Test 6: Pivot details - Cellule simple (level_1=CHARGES, mois=1)")
    print("="*60)
    
    import json
    row_values = json.dumps(["CHARGES"])
    column_values = json.dumps([1])
    
    response = client.get(
        f"/api/analytics/pivot/details?rows=level_1&columns=mois&row_values={row_values}&column_values={column_values}"
    )
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Total transactions: {data.get('total')}")
    print(f"- Page: {data.get('page')}")
    print(f"- Page size: {data.get('page_size')}")
    print(f"- Nombre de transactions retournées: {len(data.get('transactions', []))}")
    
    if len(data.get('transactions', [])) > 0:
        print(f"\nPremière transaction:")
        t = data['transactions'][0]
        print(f"  - ID: {t.get('id')}")
        print(f"  - Nom: {t.get('nom')}")
        print(f"  - Quantité: {t.get('quantite')}")
        print(f"  - Level 1: {t.get('level_1')}")
    
    # Vérifications
    assert "transactions" in data
    assert "total" in data
    assert data["total"] >= 0
    # Devrait avoir au moins 1 transaction (CHARGES en mois 1 = 1000 + 500 = 1500)
    assert data["total"] >= 1, "Devrait avoir au moins 1 transaction"
    
    print("\n✅ TEST 6 RÉUSSI: Pivot details fonctionne pour cellule simple")


def test_pivot_details_multiple_fields():
    """Test endpoint details avec plusieurs champs (level_1, level_2 en lignes)."""
    print("\n" + "="*60)
    print("Test 7: Pivot details - Plusieurs champs (level_1=CHARGES, level_2=Énergie, mois=1)")
    print("="*60)
    
    import json
    row_values = json.dumps(["CHARGES", "Énergie"])
    column_values = json.dumps([1])
    
    response = client.get(
        f"/api/analytics/pivot/details?rows=level_1,level_2&columns=mois&row_values={row_values}&column_values={column_values}"
    )
    
    assert response.status_code == 200, f"Erreur {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"\nRéponse reçue:")
    print(f"- Total transactions: {data.get('total')}")
    print(f"- Nombre de transactions retournées: {len(data.get('transactions', []))}")
    
    # Vérifications
    assert "transactions" in data
    assert data["total"] >= 1, "Devrait avoir au moins 1 transaction (CHARGES - Énergie en mois 1)"
    
    # Vérifier que toutes les transactions ont level_1 = CHARGES et level_2 = Énergie
    for t in data["transactions"]:
        assert t.get("level_1") == "CHARGES", f"Transaction {t.get('id')} devrait avoir level_1=CHARGES"
        assert t.get("level_2") == "Énergie", f"Transaction {t.get('id')} devrait avoir level_2=Énergie"
    
    print("\n✅ TEST 7 RÉUSSI: Pivot details fonctionne avec plusieurs champs")


def test_pivot_details_pagination():
    """Test endpoint details avec pagination."""
    print("\n" + "="*60)
    print("Test 8: Pivot details - Pagination")
    print("="*60)
    
    import json
    row_values = json.dumps(["CHARGES"])
    column_values = json.dumps([])
    
    # Première page (limit=2)
    response1 = client.get(
        f"/api/analytics/pivot/details?rows=level_1&columns=&row_values={row_values}&column_values={json.dumps([])}&skip=0&limit=2"
    )
    
    assert response1.status_code == 200, f"Erreur {response1.status_code}: {response1.text}"
    data1 = response1.json()
    
    print(f"\nPage 1 (skip=0, limit=2):")
    print(f"- Total: {data1.get('total')}")
    print(f"- Transactions retournées: {len(data1.get('transactions', []))}")
    
    # Deuxième page (skip=2, limit=2)
    if data1.get('total', 0) > 2:
        response2 = client.get(
            f"/api/analytics/pivot/details?rows=level_1&columns=&row_values={row_values}&column_values={json.dumps([])}&skip=2&limit=2"
        )
        
        assert response2.status_code == 200, f"Erreur {response2.status_code}: {response2.text}"
        data2 = response2.json()
        
        print(f"\nPage 2 (skip=2, limit=2):")
        print(f"- Total: {data2.get('total')}")
        print(f"- Transactions retournées: {len(data2.get('transactions', []))}")
        
        # Vérifier que les transactions sont différentes
        ids1 = {t['id'] for t in data1['transactions']}
        ids2 = {t['id'] for t in data2['transactions']}
        assert len(ids1.intersection(ids2)) == 0, "Les pages ne devraient pas avoir de transactions en commun"
    
    print("\n✅ TEST 8 RÉUSSI: Pagination fonctionne")


def test_pivot_details_validation():
    """Test endpoint details avec validation des paramètres."""
    print("\n" + "="*60)
    print("Test 9: Pivot details - Validation des paramètres")
    print("="*60)
    
    import json
    
    # Test avec nombre de valeurs incorrect
    row_values = json.dumps(["CHARGES", "Énergie"])  # 2 valeurs
    response = client.get(
        f"/api/analytics/pivot/details?rows=level_1&columns=&row_values={row_values}&column_values={json.dumps([])}"
    )
    
    assert response.status_code == 400, f"Devrait retourner 400, mais a retourné {response.status_code}"
    print(f"✓ Erreur attendue (nombre de valeurs incorrect): {response.json()}")
    
    print("\n✅ TEST 9 RÉUSSI: Validation des paramètres fonctionne")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTS ENDPOINT PIVOT (Step 4.1.1)")
    print("="*60)
    
    # Setup test data
    db = next(get_db())
    try:
        setup_test_data(db)
        
        # Run tests
        test_pivot_level1_rows()
        test_pivot_level1_rows_mois_columns()
        test_pivot_with_filters()
        test_pivot_multiple_rows()
        test_pivot_invalid_field()
        test_pivot_details_simple()
        test_pivot_details_multiple_fields()
        test_pivot_details_pagination()
        test_pivot_details_validation()
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

