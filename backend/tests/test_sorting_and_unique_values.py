"""
Tests pour Step 3.8.1 et 3.8.2 : Tri et valeurs uniques.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, Mapping, EnrichedTransaction

client = TestClient(app)


def setup_test_db():
    """Initialise la BDD de test."""
    init_database()
    db = SessionLocal()
    try:
        # Nettoyer les données de test
        db.query(EnrichedTransaction).delete()
        db.query(Transaction).delete()
        db.query(Mapping).delete()
        db.commit()
    finally:
        db.close()


def test_transactions_sorting():
    """
    Test Step 3.8.1 : Tri des transactions.
    """
    print("\n" + "=" * 60)
    print("Test Step 3.8.1: Tri des transactions")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer des transactions de test
        print("\n1. Création de transactions de test...")
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                quantite=100.0,
                nom="Transaction A",
                solde=1000.0,
                source_file="test.csv"
            ),
            Transaction(
                date=date(2024, 2, 20),
                quantite=200.0,
                nom="Transaction B",
                solde=2000.0,
                source_file="test.csv"
            ),
            Transaction(
                date=date(2024, 3, 10),
                quantite=50.0,
                nom="Transaction C",
                solde=500.0,
                source_file="test.csv"
            ),
        ]
        
        for t in transactions:
            db.add(t)
        db.commit()
        
        # Enrichir certaines transactions
        enriched1 = EnrichedTransaction(
            transaction_id=transactions[0].id,
            level_1="CHARGES",
            level_2="FRAIS",
            level_3="DETAIL1",
            annee=2024,
            mois=1
        )
        enriched2 = EnrichedTransaction(
            transaction_id=transactions[1].id,
            level_1="PRODUITS",
            level_2="REVENUS",
            level_3="DETAIL2",
            annee=2024,
            mois=2
        )
        db.add(enriched1)
        db.add(enriched2)
        db.commit()
        
        print(f"✓ {len(transactions)} transactions créées")
        
        # 2. Test tri par date (asc)
        print("\n2. Test tri par date (asc)...")
        response = client.get("/api/transactions?sort_by=date&sort_direction=asc&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 3
        dates = [t["date"] for t in data["transactions"]]
        assert dates == sorted(dates), f"Dates non triées: {dates}"
        print(f"✓ Tri par date asc fonctionne: {dates}")
        
        # 3. Test tri par date (desc)
        print("\n3. Test tri par date (desc)...")
        response = client.get("/api/transactions?sort_by=date&sort_direction=desc&limit=10")
        assert response.status_code == 200
        data = response.json()
        dates = [t["date"] for t in data["transactions"]]
        assert dates == sorted(dates, reverse=True), f"Dates non triées desc: {dates}"
        print(f"✓ Tri par date desc fonctionne: {dates}")
        
        # 4. Test tri par nom (asc)
        print("\n4. Test tri par nom (asc)...")
        response = client.get("/api/transactions?sort_by=nom&sort_direction=asc&limit=10")
        assert response.status_code == 200
        data = response.json()
        noms = [t["nom"] for t in data["transactions"]]
        assert noms == sorted(noms), f"Noms non triés: {noms}"
        print(f"✓ Tri par nom asc fonctionne: {noms}")
        
        # 5. Test tri par quantite (desc)
        print("\n5. Test tri par quantite (desc)...")
        response = client.get("/api/transactions?sort_by=quantite&sort_direction=desc&limit=10")
        assert response.status_code == 200
        data = response.json()
        quantites = [t["quantite"] for t in data["transactions"]]
        assert quantites == sorted(quantites, reverse=True), f"Quantités non triées desc: {quantites}"
        print(f"✓ Tri par quantite desc fonctionne: {quantites}")
        
        # 6. Test tri par level_1 (asc)
        print("\n6. Test tri par level_1 (asc)...")
        response = client.get("/api/transactions?sort_by=level_1&sort_direction=asc&limit=10")
        assert response.status_code == 200
        data = response.json()
        level_1s = [t["level_1"] for t in data["transactions"] if t["level_1"]]
        # Les transactions avec level_1 doivent être triées
        if len(level_1s) >= 2:
            assert level_1s == sorted(level_1s), f"Level_1 non triés: {level_1s}"
        print(f"✓ Tri par level_1 asc fonctionne")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Tri des transactions fonctionne!")
        print("=" * 60)
        
    finally:
        db.close()


def test_mappings_sorting():
    """
    Test Step 3.8.1 : Tri des mappings.
    """
    print("\n" + "=" * 60)
    print("Test Step 3.8.1: Tri des mappings")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer des mappings de test
        print("\n1. Création de mappings de test...")
        mappings = [
            Mapping(nom="Mapping C", level_1="CHARGES", level_2="FRAIS", level_3="DETAIL1"),
            Mapping(nom="Mapping A", level_1="PRODUITS", level_2="REVENUS", level_3="DETAIL2"),
            Mapping(nom="Mapping B", level_1="CHARGES", level_2="AUTRES", level_3="DETAIL3"),
        ]
        
        for m in mappings:
            db.add(m)
        db.commit()
        
        print(f"✓ {len(mappings)} mappings créés")
        
        # 2. Test tri par nom (asc)
        print("\n2. Test tri par nom (asc)...")
        response = client.get("/api/mappings?sort_by=nom&sort_direction=asc&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["mappings"]) == 3
        noms = [m["nom"] for m in data["mappings"]]
        assert noms == sorted(noms), f"Noms non triés: {noms}"
        print(f"✓ Tri par nom asc fonctionne: {noms}")
        
        # 3. Test tri par level_1 (asc)
        print("\n3. Test tri par level_1 (asc)...")
        response = client.get("/api/mappings?sort_by=level_1&sort_direction=asc&limit=10")
        assert response.status_code == 200
        data = response.json()
        level_1s = [m["level_1"] for m in data["mappings"]]
        assert level_1s == sorted(level_1s), f"Level_1 non triés: {level_1s}"
        print(f"✓ Tri par level_1 asc fonctionne: {level_1s}")
        
        # 4. Test tri par id (desc)
        print("\n4. Test tri par id (desc)...")
        response = client.get("/api/mappings?sort_by=id&sort_direction=desc&limit=10")
        assert response.status_code == 200
        data = response.json()
        ids = [m["id"] for m in data["mappings"]]
        assert ids == sorted(ids, reverse=True), f"IDs non triés desc: {ids}"
        print(f"✓ Tri par id desc fonctionne: {ids}")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Tri des mappings fonctionne!")
        print("=" * 60)
        
    finally:
        db.close()


def test_transactions_unique_values():
    """
    Test Step 3.8.2 : Valeurs uniques pour transactions.
    """
    print("\n" + "=" * 60)
    print("Test Step 3.8.2: Valeurs uniques transactions")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer des transactions avec différentes valeurs
        print("\n1. Création de transactions avec différentes valeurs...")
        transactions = [
            Transaction(date=date(2024, 1, 15), quantite=100.0, nom="PRLV SEPA", solde=1000.0, source_file="test.csv"),
            Transaction(date=date(2024, 2, 20), quantite=200.0, nom="VIR STRIPE", solde=2000.0, source_file="test.csv"),
            Transaction(date=date(2024, 3, 10), quantite=50.0, nom="PRLV SEPA", solde=500.0, source_file="test.csv"),
        ]
        
        for t in transactions:
            db.add(t)
        db.commit()
        
        # Enrichir avec différentes valeurs
        enriched = [
            EnrichedTransaction(transaction_id=transactions[0].id, level_1="CHARGES", level_2="FRAIS", level_3="PRLV", annee=2024, mois=1),
            EnrichedTransaction(transaction_id=transactions[1].id, level_1="PRODUITS", level_2="REVENUS", level_3="STRIPE", annee=2024, mois=2),
            EnrichedTransaction(transaction_id=transactions[2].id, level_1="CHARGES", level_2="FRAIS", level_3="PRLV", annee=2024, mois=3),
        ]
        
        for e in enriched:
            db.add(e)
        db.commit()
        
        print(f"✓ {len(transactions)} transactions créées")
        
        # 2. Test valeurs uniques pour nom
        print("\n2. Test valeurs uniques pour nom...")
        response = client.get("/api/transactions/unique-values?column=nom")
        assert response.status_code == 200
        data = response.json()
        assert "values" in data
        assert "PRLV SEPA" in data["values"]
        assert "VIR STRIPE" in data["values"]
        assert len(data["values"]) == 2, f"Attendu 2 valeurs uniques, obtenu {len(data['values'])}"
        print(f"✓ Valeurs uniques pour nom: {data['values']}")
        
        # 3. Test valeurs uniques pour level_1
        print("\n3. Test valeurs uniques pour level_1...")
        response = client.get("/api/transactions/unique-values?column=level_1")
        assert response.status_code == 200
        data = response.json()
        assert "CHARGES" in data["values"]
        assert "PRODUITS" in data["values"]
        assert len(data["values"]) == 2
        print(f"✓ Valeurs uniques pour level_1: {data['values']}")
        
        # 4. Test valeurs uniques pour level_2
        print("\n4. Test valeurs uniques pour level_2...")
        response = client.get("/api/transactions/unique-values?column=level_2")
        assert response.status_code == 200
        data = response.json()
        assert "FRAIS" in data["values"]
        assert "REVENUS" in data["values"]
        print(f"✓ Valeurs uniques pour level_2: {data['values']}")
        
        # 5. Test avec filtre date
        print("\n5. Test avec filtre date...")
        response = client.get("/api/transactions/unique-values?column=nom&start_date=2024-02-01&end_date=2024-02-28")
        assert response.status_code == 200
        data = response.json()
        # Seulement VIR STRIPE devrait être dans la période
        assert "VIR STRIPE" in data["values"]
        print(f"✓ Filtre par date fonctionne: {data['values']}")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Valeurs uniques transactions fonctionnent!")
        print("=" * 60)
        
    finally:
        db.close()


def test_mappings_unique_values():
    """
    Test Step 3.8.2 : Valeurs uniques pour mappings.
    """
    print("\n" + "=" * 60)
    print("Test Step 3.8.2: Valeurs uniques mappings")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer des mappings avec différentes valeurs
        print("\n1. Création de mappings avec différentes valeurs...")
        mappings = [
            Mapping(nom="PRLV SEPA", level_1="CHARGES", level_2="FRAIS", level_3="PRLV"),
            Mapping(nom="VIR STRIPE", level_1="PRODUITS", level_2="REVENUS", level_3="STRIPE"),
            Mapping(nom="PRLV SEPA 2", level_1="CHARGES", level_2="FRAIS", level_3="PRLV"),
        ]
        
        for m in mappings:
            db.add(m)
        db.commit()
        
        print(f"✓ {len(mappings)} mappings créés")
        
        # 2. Test valeurs uniques pour nom
        print("\n2. Test valeurs uniques pour nom...")
        response = client.get("/api/mappings/unique-values?column=nom")
        assert response.status_code == 200
        data = response.json()
        assert "values" in data
        assert "PRLV SEPA" in data["values"]
        assert "PRLV SEPA 2" in data["values"]
        assert "VIR STRIPE" in data["values"]
        assert len(data["values"]) == 3
        print(f"✓ Valeurs uniques pour nom: {data['values']}")
        
        # 3. Test valeurs uniques pour level_1
        print("\n3. Test valeurs uniques pour level_1...")
        response = client.get("/api/mappings/unique-values?column=level_1")
        assert response.status_code == 200
        data = response.json()
        assert "CHARGES" in data["values"]
        assert "PRODUITS" in data["values"]
        assert len(data["values"]) == 2
        print(f"✓ Valeurs uniques pour level_1: {data['values']}")
        
        # 4. Test colonne invalide
        print("\n4. Test colonne invalide...")
        response = client.get("/api/mappings/unique-values?column=invalid")
        assert response.status_code == 400
        print("✓ Erreur 400 pour colonne invalide")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Valeurs uniques mappings fonctionnent!")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_transactions_sorting()
    test_mappings_sorting()
    test_transactions_unique_values()
    test_mappings_unique_values()
    print("\n" + "=" * 60)
    print("✅ TOUS LES TESTS SONT PASSÉS!")
    print("=" * 60)

