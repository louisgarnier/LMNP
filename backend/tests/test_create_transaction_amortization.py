#!/usr/bin/env python3
"""
Test pour vérifier que les AmortizationResult sont créés automatiquement après création d'une transaction.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date
import json

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, EnrichedTransaction, AmortizationType, AmortizationResult
from backend.api.services.enrichment_service import enrich_transaction
from backend.api.services.amortization_service import recalculate_transaction_amortization

def test_create_transaction_with_amortization():
    """Test : Créer une transaction qui correspond à un AmortizationType et vérifier que les AmortizationResult sont créés."""
    print("=" * 60)
    print("Test : Création de transaction avec recalcul automatique des amortissements")
    print("=" * 60)
    print()
    
    init_database()
    db = SessionLocal()
    
    try:
        # Vérifier qu'il existe un AmortizationType pour "Immobilisations"
        amort_type = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == "Immobilisations"
        ).first()
        
        if not amort_type:
            print("⚠️  Aucun AmortizationType trouvé pour 'Immobilisations'")
            print("   Création d'un type de test...")
            
            amort_type = AmortizationType(
                name="Test Immobilisation",
                level_2_value="Immobilisations",
                level_1_values=json.dumps(["Test Level 1"]),
                duration=10.0,
                annual_amount=None,
                start_date=None
            )
            db.add(amort_type)
            db.commit()
            print("   ✓ Type créé")
        
        level_1_values = json.loads(amort_type.level_1_values or "[]")
        test_level_1 = level_1_values[0] if level_1_values else "Test Level 1"
        
        print(f"📋 Type d'amortissement utilisé : {amort_type.name}")
        print(f"   - Level 2: {amort_type.level_2_value}")
        print(f"   - Level 1: {test_level_1}")
        print(f"   - Durée: {amort_type.duration} années")
        print()
        
        # Compter les AmortizationResult existants pour cette transaction (avant)
        results_before = db.query(AmortizationResult).count()
        print(f"📊 AmortizationResult existants avant : {results_before}")
        print()
        
        # Créer une transaction de test
        print("📝 Création d'une transaction de test...")
        transaction = Transaction(
            date=date(2024, 6, 15),
            quantite=-50000.0,
            nom="Test Transaction Amortissement",
            solde=0.0
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        print(f"   ✓ Transaction créée (ID: {transaction.id})")
        print()
        
        # Enrichir la transaction (simule ce que fait create_transaction)
        print("🔍 Enrichissement de la transaction...")
        enriched = enrich_transaction(transaction, db)
        
        # Si pas de mapping trouvé, créer manuellement l'enrichissement avec les bonnes valeurs
        if not enriched.level_2 or enriched.level_2 != "Immobilisations":
            print("   ⚠️  Pas de mapping trouvé, création manuelle de l'enrichissement...")
            if enriched:
                enriched.level_1 = test_level_1
                enriched.level_2 = "Immobilisations"
                enriched.level_3 = None
            else:
                enriched = EnrichedTransaction(
                    transaction_id=transaction.id,
                    mois=transaction.date.month,
                    annee=transaction.date.year,
                    level_1=test_level_1,
                    level_2="Immobilisations",
                    level_3=None
                )
                db.add(enriched)
            db.commit()
            db.refresh(enriched)
        
        print(f"   ✓ Transaction enrichie (level_1: {enriched.level_1}, level_2: {enriched.level_2})")
        print()
        
        # Recalculer les amortissements (simule ce que fait create_transaction)
        print("🔄 Recalcul des amortissements...")
        created_count = recalculate_transaction_amortization(db, transaction.id)
        print(f"   ✓ {created_count} résultats d'amortissement créés")
        print()
        
        # Vérifier que les AmortizationResult ont été créés
        results_after = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).all()
        
        print(f"📊 AmortizationResult créés : {len(results_after)}")
        
        if len(results_after) > 0:
            print("   ✓ Les AmortizationResult ont été créés avec succès")
            print()
            print("   Détail des résultats :")
            for result in results_after[:5]:  # Afficher les 5 premiers
                print(f"     - Année {result.year}, Catégorie: {result.category}, Montant: {result.amount:,.2f} €")
            if len(results_after) > 5:
                print(f"     ... et {len(results_after) - 5} autres résultats")
        else:
            print("   ❌ Aucun AmortizationResult créé")
            print("   ⚠️  Vérifier que :")
            print("      - Le level_1 de la transaction correspond à un level_1_values du type")
            print("      - Le level_2 est 'Immobilisations'")
            print("      - La durée du type est > 0")
        
        print()
        print("=" * 60)
        print("✅ Test terminé")
        print("=" * 60)
        
        return len(results_after) > 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_create_transaction_with_amortization()
    sys.exit(0 if success else 1)

