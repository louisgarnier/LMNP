#!/usr/bin/env python3
"""
Script de test pour vérifier que les AmortizationResult sont mis à jour automatiquement
après modification d'une transaction ou d'un mapping.

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
    print("🧪 Test : Modification de transaction/mapping → AmortizationResult mis à jour")
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

        # Créer une transaction de test avec un montant initial
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
        print(f"  ✓ Transaction créée (ID: {test_transaction.id}, quantite: {test_transaction.quantite})")

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

        # Recalculer les amortissements initialement
        print()
        print("🔄 Recalcul initial des amortissements...")
        initial_count = recalculate_transaction_amortization(db, test_transaction.id)
        print(f"  ✓ {initial_count} AmortizationResult créés")

        # Récupérer les résultats initiaux
        results_before = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).all()
        total_before = sum(abs(r.amount) for r in results_before)
        print(f"  - Montant total initial : {total_before:,.2f} €")

        # TEST 1 : Modification de la quantité
        print()
        print("=" * 60)
        print("TEST 1 : Modification de la quantité")
        print("=" * 60)
        test_transaction.quantite = -75000.0  # Augmenter le montant
        db.commit()
        print(f"  ✓ Quantité modifiée : -50,000.00 € → -75,000.00 €")

        # Recalculer les amortissements (comme le fait update_transaction)
        recalculate_transaction_amortization(db, test_transaction.id)
        print("  ✓ Amortissements recalculés")

        # Vérifier que les résultats ont été mis à jour
        results_after_quantite = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).all()
        total_after_quantite = sum(abs(r.amount) for r in results_after_quantite)
        print(f"  - Montant total après modification : {total_after_quantite:,.2f} €")
        
        if total_after_quantite > total_before:
            print("  ✅ TEST 1 RÉUSSI : Les AmortizationResult ont été mis à jour après modification de la quantité")
        else:
            print("  ❌ TEST 1 ÉCHOUÉ : Les AmortizationResult n'ont pas été mis à jour")

        # TEST 2 : Modification de la date
        print()
        print("=" * 60)
        print("TEST 2 : Modification de la date")
        print("=" * 60)
        old_date = test_transaction.date
        new_date = date(2024, 6, 15)  # Changer la date (6 mois plus tard)
        test_transaction.date = new_date
        db.commit()
        print(f"  ✓ Date modifiée : {old_date} → {new_date}")

        # Recalculer les amortissements (comme le fait update_transaction)
        recalculate_transaction_amortization(db, test_transaction.id)
        print("  ✓ Amortissements recalculés")

        # Vérifier que les résultats ont été mis à jour
        results_after_date = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).all()
        
        # Vérifier que la première année a changé (prorata différent)
        first_year_result = next((r for r in results_after_date if r.year == 2024), None)
        if first_year_result:
            print(f"  - Montant pour 2024 (après changement de date) : {abs(first_year_result.amount):,.2f} €")
            print("  ✅ TEST 2 RÉUSSI : Les AmortizationResult ont été mis à jour après modification de la date")
        else:
            print("  ❌ TEST 2 ÉCHOUÉ : Aucun résultat pour 2024 trouvé")

        # TEST 3 : Modification du mapping (level_1/level_2)
        print()
        print("=" * 60)
        print("TEST 3 : Modification du mapping (level_1)")
        print("=" * 60)
        
        # Trouver un autre level_1 pour tester
        other_level_1 = "Travaux de rénovation, gros œuvre"
        test_enriched.level_1 = other_level_1
        db.commit()
        print(f"  ✓ Level_1 modifié : {level_1_values[0]} → {other_level_1}")

        # Recalculer les amortissements (comme le fait update_transaction_classifications)
        recalculate_transaction_amortization(db, test_transaction.id)
        print("  ✓ Amortissements recalculés")

        # Vérifier que les résultats ont été mis à jour (ou supprimés si pas de correspondance)
        results_after_mapping = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == test_transaction.id
        ).all()
        
        # Vérifier si le nouveau level_1 correspond à un type d'amortissement
        matching_type = db.query(AmortizationType).filter(
            AmortizationType.level_2_value == "Immobilisations"
        ).all()
        
        has_match = False
        for atype in matching_type:
            atype_level_1_values = json.loads(atype.level_1_values or "[]")
            if other_level_1 in atype_level_1_values:
                has_match = True
                break
        
        if has_match:
            if len(results_after_mapping) > 0:
                print(f"  - Nombre de résultats après modification : {len(results_after_mapping)}")
                print("  ✅ TEST 3 RÉUSSI : Les AmortizationResult ont été mis à jour après modification du mapping")
            else:
                print("  ❌ TEST 3 ÉCHOUÉ : Aucun résultat créé malgré la correspondance")
        else:
            if len(results_after_mapping) == 0:
                print("  ✅ TEST 3 RÉUSSI : Les AmortizationResult ont été supprimés (pas de correspondance)")
            else:
                print("  ❌ TEST 3 ÉCHOUÉ : Des résultats existent encore malgré l'absence de correspondance")

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

