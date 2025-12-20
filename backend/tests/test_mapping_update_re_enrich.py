"""
Tests pour vérifier que la mise à jour d'un mapping re-enrichit les transactions (Step 3.7 amélioration).

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


def test_update_mapping_re_enriches_transactions():
    """
    Test que la mise à jour d'un mapping re-enrichit les transactions qui l'utilisaient.
    """
    print("\n" + "=" * 60)
    print("Test: Mise à jour mapping → re-enrichissement transactions")
    print("=" * 60)
    
    setup_test_db()
    db = SessionLocal()
    
    try:
        # 1. Créer un mapping initial
        print("\n1. Création d'un mapping initial...")
        initial_mapping = Mapping(
            nom="PRLV SEPA",
            level_1="CHARGES",
            level_2="FRAIS BANCAIRES",
            level_3="PRLV",
            is_prefix_match=True,
            priority=0
        )
        db.add(initial_mapping)
        db.commit()
        db.refresh(initial_mapping)
        mapping_id = initial_mapping.id
        print(f"✓ Mapping créé avec ID: {mapping_id}")
        print(f"  - Nom: {initial_mapping.nom}")
        print(f"  - Level 1: {initial_mapping.level_1}")
        print(f"  - Level 2: {initial_mapping.level_2}")
        print(f"  - Level 3: {initial_mapping.level_3}")
        
        # 2. Créer des transactions qui correspondent au mapping
        print("\n2. Création de transactions correspondant au mapping...")
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                quantite=-50.0,
                nom="PRLV SEPA CHARGES COPRO",
                solde=5000.0,
                source_file="test.csv"
            ),
            Transaction(
                date=date(2024, 1, 20),
                quantite=-30.0,
                nom="PRLV SEPA ASSURANCE",
                solde=4970.0,
                source_file="test.csv"
            ),
            # Transaction avec le même nom mais pas encore enrichie (ou avec des valeurs différentes)
            Transaction(
                date=date(2024, 2, 15),
                quantite=-60.0,
                nom="PRLV SEPA CHARGES COPRO",
                solde=4910.0,
                source_file="test.csv"
            ),
        ]
        
        for t in transactions:
            db.add(t)
        db.commit()
        
        for t in transactions:
            db.refresh(t)
        print(f"✓ {len(transactions)} transactions créées")
        
        # 3. Enrichir seulement les 2 premières transactions (la 3ème reste non enrichie ou avec des valeurs différentes)
        print("\n3. Enrichissement partiel des transactions...")
        for transaction in transactions[:2]:
            enrich_transaction(transaction, db)
        db.commit()
        
        # Vérifier que les 2 premières transactions sont enrichies avec les valeurs du mapping initial
        for transaction in transactions[:2]:
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            assert enriched is not None, f"Transaction {transaction.id} n'a pas été enrichie"
            assert enriched.level_1 == "CHARGES", f"Level 1 attendu: CHARGES, obtenu: {enriched.level_1}"
            assert enriched.level_2 == "FRAIS BANCAIRES", f"Level 2 attendu: FRAIS BANCAIRES, obtenu: {enriched.level_2}"
            assert enriched.level_3 == "PRLV", f"Level 3 attendu: PRLV, obtenu: {enriched.level_3}"
            print(f"✓ Transaction '{transaction.nom}' enrichie avec CHARGES / FRAIS BANCAIRES / PRLV")
        
        # La 3ème transaction n'est pas encore enrichie (ou a des valeurs différentes)
        print(f"✓ Transaction '{transactions[2].nom}' pas encore enrichie (sera enrichie après mise à jour du mapping)")
        
        # 4. Mettre à jour le mapping avec de nouvelles valeurs
        print("\n4. Mise à jour du mapping avec de nouvelles valeurs...")
        update_data = {
            "level_1": "CHARGES_MODIFIEES",
            "level_2": "FRAIS_MODIFIES",
            "level_3": "PRLV_MODIFIE"
        }
        
        response = client.put(f"/api/mappings/{mapping_id}", json=update_data)
        assert response.status_code == 200, f"Status code attendu: 200, obtenu: {response.status_code}"
        
        updated_mapping = response.json()
        assert updated_mapping["level_1"] == "CHARGES_MODIFIEES"
        assert updated_mapping["level_2"] == "FRAIS_MODIFIES"
        assert updated_mapping["level_3"] == "PRLV_MODIFIE"
        print(f"✓ Mapping mis à jour")
        print(f"  - Level 1: {updated_mapping['level_1']}")
        print(f"  - Level 2: {updated_mapping['level_2']}")
        print(f"  - Level 3: {updated_mapping['level_3']}")
        
        # 5. Vérifier que TOUTES les transactions avec le même nom sont re-enrichies avec les nouvelles valeurs
        print("\n5. Vérification du re-enrichissement de TOUTES les transactions correspondantes...")
        for transaction in transactions:
            db.refresh(transaction)
        
        # Vérifier que toutes les transactions sont maintenant enrichies avec les nouvelles valeurs
        for transaction in transactions:
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            assert enriched is not None, f"Transaction {transaction.id} n'a pas été enrichie"
            assert enriched.level_1 == "CHARGES_MODIFIEES", f"Level 1 attendu: CHARGES_MODIFIEES, obtenu: {enriched.level_1}"
            assert enriched.level_2 == "FRAIS_MODIFIES", f"Level 2 attendu: FRAIS_MODIFIES, obtenu: {enriched.level_2}"
            assert enriched.level_3 == "PRLV_MODIFIE", f"Level 3 attendu: PRLV_MODIFIE, obtenu: {enriched.level_3}"
            print(f"✓ Transaction '{transaction.nom}' re-enrichie avec CHARGES_MODIFIEES / FRAIS_MODIFIES / PRLV_MODIFIE")
        
        print("\n✓ IMPORTANT: Toutes les transactions avec le même nom ont été re-enrichies, même celles qui n'étaient pas encore enrichies!")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI: Les transactions sont bien re-enrichies après mise à jour du mapping!")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_update_mapping_re_enriches_transactions()

