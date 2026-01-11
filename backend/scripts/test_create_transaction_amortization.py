#!/usr/bin/env python3
"""
Script de test pour vérifier que les AmortizationResult sont créés automatiquement
après création d'une transaction.

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
from backend.api.services.amortization_service import recalculate_transaction_amortization
from sqlalchemy import and_

def main():
    print("=" * 60)
    print("🧪 Test : Création de transaction → AmortizationResult créés")
    print("=" * 60)
    print()

    init_database()
    db = SessionLocal()

    try:
        # Vérifier qu'il existe au moins un AmortizationType avec level_2 = "Immobilisations"
        amortization_type = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == "Immobilisations",
            AmortizationType.duration > 0
        ).first()

        if not amortization_type:
            print("⚠️  Aucun AmortizationType trouvé avec level_2 = 'Immobilisations' et duration > 0")
            print("   Création d'un type de test...")
            
            # Créer un type de test
            level_1_values = ["Immeuble (hors terrain)"]
            amortization_type = AmortizationType(
                name="Test Immobilisation",
                level_2_value="Immobilisations",
                level_1_values=json.dumps(level_1_values),
                duration=10.0,
                annual_amount=None
            )
            db.add(amortization_type)
            db.commit()
            db.refresh(amortization_type)
            print(f"   ✓ Type créé : {amortization_type.name} (ID: {amortization_type.id})")
        else:
            print(f"✓ Type d'amortissement trouvé : {amortization_type.name} (ID: {amortization_type.id})")
            level_1_values = json.loads(amortization_type.level_1_values or "[]")
            print(f"  - Level 1 values: {level_1_values}")
            print(f"  - Duration: {amortization_type.duration} ans")

        # Compter les AmortizationResult existants pour cette transaction (avant création)
        print()
        print("📊 État initial :")
        initial_count = db.query(AmortizationResult).count()
        print(f"  - Nombre total de AmortizationResult en base : {initial_count}")

        # Créer une transaction de test
        print()
        print("📝 Création d'une transaction de test...")
        test_transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=-50000.0,
            nom="TEST - Transaction pour amortissement",
            solde=0.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        print(f"  ✓ Transaction créée (ID: {test_transaction.id})")

        # Créer l'enrichissement correspondant
        print()
        print("📝 Création de l'enrichissement...")
        if level_1_values:
            test_enriched = EnrichedTransaction(
                transaction_id=test_transaction.id,
                mois=1,
                annee=2024,
                level_1=level_1_values[0],
                level_2="Immobilisations",
                level_3="Actif"
            )
            db.add(test_enriched)
            db.commit()
            print(f"  ✓ Enrichissement créé (level_1: {test_enriched.level_1}, level_2: {test_enriched.level_2})")

        # Vérifier qu'il n'y a pas encore de AmortizationResult pour cette transaction
        print()
        print("📊 Vérification avant recalcul...")
        results_before = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).count()
        print(f"  - Nombre de AmortizationResult pour cette transaction : {results_before}")

        # Appeler recalculate_transaction_amortization (comme le fait create_transaction)
        print()
        print("🔄 Recalcul des amortissements...")
        created_count = recalculate_transaction_amortization(db, test_transaction.id)
        print(f"  ✓ {created_count} AmortizationResult créés")

        # Vérifier que les AmortizationResult ont été créés
        print()
        print("📊 Vérification après recalcul...")
        results_after = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).all()
        print(f"  - Nombre de AmortizationResult pour cette transaction : {len(results_after)}")

        if results_after:
            print()
            print("  📋 Détails des AmortizationResult créés :")
            for result in results_after:
                print(f"    • Année {result.year}: {result.amount:,.2f} € (catégorie: {result.category})")
        else:
            print("  ⚠️  Aucun AmortizationResult créé !")

        # Vérifier le total
        total_count = db.query(AmortizationResult).count()
        print()
        print(f"📊 État final :")
        print(f"  - Nombre total de AmortizationResult en base : {total_count}")
        print(f"  - Différence : +{total_count - initial_count}")

        # Résultat du test
        print()
        if created_count > 0 and len(results_after) > 0:
            print("✅ TEST RÉUSSI : Les AmortizationResult ont été créés automatiquement")
        else:
            print("❌ TEST ÉCHOUÉ : Les AmortizationResult n'ont pas été créés")

        # Nettoyer (optionnel - commenter pour garder les données de test)
        print()
        print("🧹 Nettoyage...")
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).delete()
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == test_transaction.id
        ).delete()
        db.query(Transaction).filter(
            Transaction.id == test_transaction.id
        ).delete()
        db.commit()
        print("  ✓ Données de test supprimées")

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

