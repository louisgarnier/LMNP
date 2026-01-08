"""
Test script to validate amortization service calculations.

Run with: python -m pytest backend/tests/test_amortization_service.py -v
Or: python backend/tests/test_amortization_service.py
"""

import sys
import json
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, SessionLocal
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    AmortizationType,
    AmortizationResult
)
from backend.api.services.amortization_service import (
    calculate_30_360_days,
    calculate_yearly_amounts,
    recalculate_transaction_amortization,
    recalculate_all_amortizations,
    validate_amortization_sum
)


def test_30_360_days_calculation():
    """Test 1: Calcul convention 30/360."""
    print("Test 1: Calcul convention 30/360...")
    
    # Test année complète
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    days = calculate_30_360_days(start, end)
    assert days == 360, f"Attendu 360 jours, obtenu {days}"
    print("  ✓ Année complète : 360 jours")
    
    # Test mois complet
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)
    days = calculate_30_360_days(start, end)
    assert days == 30, f"Attendu 30 jours, obtenu {days}"
    print("  ✓ Mois complet : 30 jours")
    
    # Test période partielle
    start = date(2024, 1, 15)
    end = date(2024, 3, 10)
    days = calculate_30_360_days(start, end)
    expected = (3 - 1) * 30 + (10 - 15)  # 2 mois * 30 + (10-15) jours
    assert days == expected, f"Attendu {expected} jours, obtenu {days}"
    print(f"  ✓ Période partielle : {days} jours")
    
    print("  ✓ Test 1 réussi")


def test_proportional_distribution():
    """Test 2: Répartition proportionnelle."""
    print("\nTest 2: Répartition proportionnelle...")
    
    start_date = date(2024, 1, 1)
    total_amount = -10000.0  # Montant négatif
    duration = 5.0  # 5 ans
    
    yearly_amounts = calculate_yearly_amounts(start_date, total_amount, duration)
    
    # Vérifier qu'on a 5 années
    assert len(yearly_amounts) == 5, f"Attendu 5 années, obtenu {len(yearly_amounts)}"
    print(f"  ✓ {len(yearly_amounts)} années calculées")
    
    # Vérifier que tous les montants sont négatifs
    for year, amount in yearly_amounts.items():
        assert amount < 0, f"Montant pour {year} devrait être négatif : {amount}"
    print("  ✓ Tous les montants sont négatifs")
    
    # Vérifier que la somme = montant initial
    total = sum(abs(amount) for amount in yearly_amounts.values())
    assert abs(total - abs(total_amount)) < 0.01, f"Somme incorrecte : {total} vs {abs(total_amount)}"
    print(f"  ✓ Somme correcte : {total:.2f} = {abs(total_amount):.2f}")
    
    print("  ✓ Test 2 réussi")


def test_annual_amount_override():
    """Test 3: Override annual_amount."""
    print("\nTest 3: Override annual_amount...")
    
    start_date = date(2024, 1, 1)
    total_amount = -10000.0
    duration = 5.0
    annual_amount = 2500.0  # Override
    
    yearly_amounts = calculate_yearly_amounts(
        start_date, total_amount, duration, annual_amount
    )
    
    # Vérifier que les montants utilisent annual_amount
    # Première année devrait être proche de 2500
    first_year = min(yearly_amounts.keys())
    first_amount = abs(yearly_amounts[first_year])
    assert abs(first_amount - annual_amount) < 100, f"Montant première année incorrect : {first_amount}"
    print(f"  ✓ Annual amount override fonctionne : {first_amount:.2f}")
    
    print("  ✓ Test 3 réussi")


def test_create_amortization_results():
    """Test 4: Création de résultats d'amortissement."""
    print("\nTest 4: Création de résultats d'amortissement...")
    
    init_database()
    db = SessionLocal()
    
    try:
        # Créer une transaction
        transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=-50000.0,
            nom="Test Immobilisation",
            solde=0.0
        )
        db.add(transaction)
        db.flush()
        
        # Créer un enrichissement
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            mois=1,
            annee=2024,
            level_1="Test Level 1",
            level_2="ammortissements"
        )
        db.add(enriched)
        db.flush()
        
        # Créer un type d'amortissement
        amort_type = AmortizationType(
            name="Test Immobilisation",
            level_2_value="ammortissements",
            level_1_values=json.dumps(["Test Level 1"]),
            duration=10.0,
            annual_amount=None
        )
        db.add(amort_type)
        db.commit()
        
        # Recalculer les amortissements
        created_count = recalculate_transaction_amortization(db, transaction.id)
        
        assert created_count > 0, "Aucun résultat créé"
        print(f"  ✓ {created_count} résultats créés")
        
        # Vérifier les résultats
        results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).all()
        
        assert len(results) == created_count
        print(f"  ✓ {len(results)} résultats en base de données")
        
        # Vérifier la validation
        is_valid = validate_amortization_sum(db, transaction.id, abs(transaction.quantite))
        assert is_valid, "Validation de la somme échouée"
        print("  ✓ Validation de la somme réussie")
        
        # Nettoyer
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).delete()
        db.query(AmortizationType).filter(AmortizationType.id == amort_type.id).delete()
        db.query(EnrichedTransaction).filter(EnrichedTransaction.id == enriched.id).delete()
        db.query(Transaction).filter(Transaction.id == transaction.id).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("  ✓ Test 4 réussi")


def test_multiple_categories():
    """Test 5: Plusieurs catégories."""
    print("\nTest 5: Plusieurs catégories...")
    
    init_database()
    db = SessionLocal()
    
    try:
        categories = ["Immobilisation terrain", "Immobilisation travaux", "Immobilisation mobilier"]
        transactions_created = []
        
        for i, category in enumerate(categories):
            # Créer transaction
            transaction = Transaction(
                date=date(2024, 1, 1 + i),
                quantite=-10000.0 * (i + 1),
                nom=f"Test {category}",
                solde=0.0
            )
            db.add(transaction)
            db.flush()
            
            # Créer enrichissement
            enriched = EnrichedTransaction(
                transaction_id=transaction.id,
                mois=1,
                annee=2024,
                level_1=f"Level1_{i}",
                level_2="ammortissements"
            )
            db.add(enriched)
            db.flush()
            
            # Créer type
            amort_type = AmortizationType(
                name=category,
                level_2_value="ammortissements",
                level_1_values=json.dumps([f"Level1_{i}"]),
                duration=5.0
            )
            db.add(amort_type)
            db.commit()
            
            # Recalculer
            created = recalculate_transaction_amortization(db, transaction.id)
            transactions_created.append((transaction.id, created))
        
        # Vérifier que toutes les catégories ont des résultats
        for transaction_id, created in transactions_created:
            assert created > 0, f"Aucun résultat pour transaction {transaction_id}"
        
        print(f"  ✓ {len(categories)} catégories testées avec succès")
        
        # Nettoyer
        for transaction_id, _ in transactions_created:
            db.query(AmortizationResult).filter(
                AmortizationResult.transaction_id == transaction_id
            ).delete()
            db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction_id
            ).delete()
            db.query(Transaction).filter(Transaction.id == transaction_id).delete()
        db.query(AmortizationType).filter(
            AmortizationType.level_2_value == "ammortissements"
        ).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("  ✓ Test 5 réussi")


def test_recalculate_all():
    """Test 6: Recalcul complet."""
    print("\nTest 6: Recalcul complet...")
    
    init_database()
    db = SessionLocal()
    
    try:
        # Créer plusieurs transactions
        for i in range(3):
            transaction = Transaction(
                date=date(2024, 1, 1 + i),
                quantite=-10000.0,
                nom=f"Test Transaction {i}",
                solde=0.0
            )
            db.add(transaction)
            db.flush()
            
            enriched = EnrichedTransaction(
                transaction_id=transaction.id,
                mois=1,
                annee=2024,
                level_1=f"Level1_{i}",
                level_2="ammortissements"
            )
            db.add(enriched)
        
        # Créer un type
        amort_type = AmortizationType(
            name="Test Type",
            level_2_value="ammortissements",
            level_1_values=json.dumps([f"Level1_{i}" for i in range(3)]),
            duration=5.0
        )
        db.add(amort_type)
        db.commit()
        
        # Recalculer tout
        total_created = recalculate_all_amortizations(db)
        
        assert total_created > 0, "Aucun résultat créé"
        print(f"  ✓ {total_created} résultats créés au total")
        
        # Vérifier que tous les résultats existent
        all_results = db.query(AmortizationResult).all()
        assert len(all_results) == total_created
        print(f"  ✓ {len(all_results)} résultats en base de données")
        
        # Nettoyer
        db.query(AmortizationResult).delete()
        db.query(EnrichedTransaction).delete()
        db.query(Transaction).delete()
        db.query(AmortizationType).filter(AmortizationType.id == amort_type.id).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("  ✓ Test 6 réussi")


def test_start_date_override():
    """Test 7: Override start_date depuis AmortizationType."""
    print("\nTest 7: Override start_date...")
    
    init_database()
    db = SessionLocal()
    
    try:
        # Créer transaction avec date différente
        transaction = Transaction(
            date=date(2024, 6, 15),
            quantite=-20000.0,
            nom="Test Start Date Override",
            solde=0.0
        )
        db.add(transaction)
        db.flush()
        
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            mois=6,
            annee=2024,
            level_1="Test Level 1",
            level_2="ammortissements"
        )
        db.add(enriched)
        db.flush()
        
        # Créer type avec start_date override
        amort_type = AmortizationType(
            name="Test Type",
            level_2_value="ammortissements",
            level_1_values=json.dumps(["Test Level 1"]),
            start_date=date(2024, 1, 1),  # Override
            duration=5.0
        )
        db.add(amort_type)
        db.commit()
        
        # Recalculer
        created = recalculate_transaction_amortization(db, transaction.id)
        
        assert created > 0, "Aucun résultat créé"
        
        # Vérifier que les résultats commencent en 2024 (start_date override)
        results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).all()
        
        years = [r.year for r in results]
        assert 2024 in years, "L'année 2024 devrait être dans les résultats"
        print(f"  ✓ Start date override fonctionne : années {sorted(years)}")
        
        # Nettoyer
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).delete()
        db.query(AmortizationType).filter(AmortizationType.id == amort_type.id).delete()
        db.query(EnrichedTransaction).filter(EnrichedTransaction.id == enriched.id).delete()
        db.query(Transaction).filter(Transaction.id == transaction.id).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("  ✓ Test 7 réussi")


def test_duration_zero():
    """Test 8: Durée = 0 (non amortissable)."""
    print("\nTest 8: Durée = 0 (non amortissable)...")
    
    init_database()
    db = SessionLocal()
    
    try:
        # Créer transaction
        transaction = Transaction(
            date=date(2024, 1, 1),
            quantite=-10000.0,
            nom="Test Non Amortissable",
            solde=0.0
        )
        db.add(transaction)
        db.flush()
        
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            mois=1,
            annee=2024,
            level_1="Test Level 1",
            level_2="ammortissements"
        )
        db.add(enriched)
        db.flush()
        
        # Créer type avec duration = 0
        amort_type = AmortizationType(
            name="Test Type",
            level_2_value="ammortissements",
            level_1_values=json.dumps(["Test Level 1"]),
            duration=0.0  # Non amortissable
        )
        db.add(amort_type)
        db.commit()
        
        # Recalculer
        created = recalculate_transaction_amortization(db, transaction.id)
        
        assert created == 0, "Aucun résultat ne devrait être créé avec duration=0"
        print("  ✓ Aucun résultat créé pour duration=0")
        
        # Vérifier qu'il n'y a pas de résultats
        results = db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction.id
        ).all()
        
        assert len(results) == 0, "Aucun résultat ne devrait exister"
        print("  ✓ Aucun résultat en base de données")
        
        # Nettoyer
        db.query(AmortizationType).filter(AmortizationType.id == amort_type.id).delete()
        db.query(EnrichedTransaction).filter(EnrichedTransaction.id == enriched.id).delete()
        db.query(Transaction).filter(Transaction.id == transaction.id).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("  ✓ Test 8 réussi")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Amortization Service")
    print("=" * 60)
    
    try:
        test_30_360_days_calculation()
        test_proportional_distribution()
        test_annual_amount_override()
        test_create_amortization_results()
        test_multiple_categories()
        test_recalculate_all()
        test_start_date_override()
        test_duration_zero()
        
        print("\n" + "=" * 60)
        print("✓ All 8 tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

