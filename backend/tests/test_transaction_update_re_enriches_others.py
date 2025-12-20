"""
Tests pour vérifier que la modification d'une transaction re-enrichit toutes les autres transactions avec le même nom.

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
from backend.database.models import Mapping, Transaction, EnrichedTransaction
from backend.api.services.enrichment_service import enrich_transaction

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


def test_update_transaction_re_enriches_others():
    """
    Test que la modification d'une transaction re-enrichit toutes les autres transactions avec le même nom.
    """
    print("\n" + "=" * 60)
    print("Test: Modification transaction → re-enrichissement autres transactions")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer plusieurs transactions avec le même nom (ex: facture d'électricité chaque mois)
        print("\n1. Création de transactions avec le même nom...")
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                quantite=-100.0,
                nom="FACTURE ELECTRICITE",
                solde=5000.0,
                source_file="test.csv"
            ),
            Transaction(
                date=date(2024, 2, 15),
                quantite=-100.0,
                nom="FACTURE ELECTRICITE",
                solde=4900.0,
                source_file="test.csv"
            ),
            Transaction(
                date=date(2024, 3, 15),
                quantite=-100.0,
                nom="FACTURE ELECTRICITE",
                solde=4800.0,
                source_file="test.csv"
            ),
        ]
        
        for t in transactions:
            db.add(t)
        db.commit()
        
        for t in transactions:
            db.refresh(t)
        print(f"✓ {len(transactions)} transactions créées avec le même nom 'FACTURE ELECTRICITE'")
        
        # 2. Vérifier qu'aucune transaction n'est encore enrichie
        print("\n2. Vérification de l'état initial...")
        for transaction in transactions:
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            assert enriched is None, f"Transaction {transaction.id} ne devrait pas être enrichie initialement"
        print("✓ Aucune transaction n'est encore enrichie")
        
        # 3. Modifier la classification de la première transaction
        print("\n3. Modification de la classification de la première transaction...")
        response = client.put(
            f"/api/enrichment/transactions/{transactions[0].id}",
            params={
                "level_1": "CHARGES",
                "level_2": "ENERGIE",
                "level_3": "ELECTRICITE"
            }
        )
        assert response.status_code == 200, f"Status code attendu: 200, obtenu: {response.status_code}"
        
        updated_transaction = response.json()
        assert updated_transaction["level_1"] == "CHARGES"
        assert updated_transaction["level_2"] == "ENERGIE"
        assert updated_transaction["level_3"] == "ELECTRICITE"
        print(f"✓ Première transaction modifiée avec CHARGES / ENERGIE / ELECTRICITE")
        
        # 4. Vérifier que TOUTES les transactions avec le même nom sont maintenant enrichies
        print("\n4. Vérification que TOUTES les transactions avec le même nom sont enrichies...")
        for transaction in transactions:
            db.refresh(transaction)
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            assert enriched is not None, f"Transaction {transaction.id} devrait être enrichie"
            assert enriched.level_1 == "CHARGES", f"Level 1 attendu: CHARGES, obtenu: {enriched.level_1}"
            assert enriched.level_2 == "ENERGIE", f"Level 2 attendu: ENERGIE, obtenu: {enriched.level_2}"
            assert enriched.level_3 == "ELECTRICITE", f"Level 3 attendu: ELECTRICITE, obtenu: {enriched.level_3}"
            print(f"✓ Transaction du {transaction.date} enrichie avec CHARGES / ENERGIE / ELECTRICITE")
        
        # 5. Vérifier qu'un mapping a été créé
        print("\n5. Vérification qu'un mapping a été créé...")
        mapping = db.query(Mapping).filter(Mapping.nom == "FACTURE ELECTRICITE").first()
        assert mapping is not None, "Un mapping devrait avoir été créé"
        assert mapping.level_1 == "CHARGES"
        assert mapping.level_2 == "ENERGIE"
        assert mapping.level_3 == "ELECTRICITE"
        print(f"✓ Mapping créé avec CHARGES / ENERGIE / ELECTRICITE")
        
        # 6. Modifier à nouveau la première transaction avec de nouvelles valeurs
        print("\n6. Modification de la première transaction avec de nouvelles valeurs...")
        response = client.put(
            f"/api/enrichment/transactions/{transactions[0].id}",
            params={
                "level_1": "CHARGES_MODIFIEES",
                "level_2": "ENERGIE_MODIFIEE",
                "level_3": "ELECTRICITE_MODIFIEE"
            }
        )
        assert response.status_code == 200
        
        # 7. Vérifier que TOUTES les transactions sont re-enrichies avec les nouvelles valeurs
        print("\n7. Vérification que TOUTES les transactions sont re-enrichies avec les nouvelles valeurs...")
        for transaction in transactions:
            db.refresh(transaction)
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            assert enriched.level_1 == "CHARGES_MODIFIEES", f"Level 1 attendu: CHARGES_MODIFIEES, obtenu: {enriched.level_1}"
            assert enriched.level_2 == "ENERGIE_MODIFIEE", f"Level 2 attendu: ENERGIE_MODIFIEE, obtenu: {enriched.level_2}"
            assert enriched.level_3 == "ELECTRICITE_MODIFIEE", f"Level 3 attendu: ELECTRICITE_MODIFIEE, obtenu: {enriched.level_3}"
            print(f"✓ Transaction du {transaction.date} re-enrichie avec CHARGES_MODIFIEES / ENERGIE_MODIFIEE / ELECTRICITE_MODIFIEE")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Toutes les transactions avec le même nom sont re-enrichies!")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_update_transaction_re_enriches_others()

