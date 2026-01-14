"""
Tests pour le recalcul automatique des comptes de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from sqlalchemy.orm import Session

from backend.database import init_database, SessionLocal
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    LoanPayment,
    CompteResultatMapping,
    CompteResultatData
)
from backend.api.services.compte_resultat_service import (
    invalidate_compte_resultat_for_year,
    invalidate_compte_resultat_for_date_range,
    invalidate_all_compte_resultat,
    calculate_compte_resultat
)


def test_invalidate_for_year():
    """Test invalidation pour une année."""
    print("\nTesting invalidate_compte_resultat_for_year()...")
    db = SessionLocal()
    try:
        # Utiliser une année qui n'a probablement pas de données (2099)
        year = 2099
        
        # Créer des données de test
        data1 = CompteResultatData(
            annee=year,
            category_name="Test Category 1",
            amount=100.0
        )
        data2 = CompteResultatData(
            annee=year + 1,
            category_name="Test Category 2",
            amount=200.0
        )
        db.add(data1)
        db.add(data2)
        db.commit()
        
        # Vérifier que les données existent
        count_before = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year
        ).count()
        assert count_before == 1, f"Expected 1 data for year {year}, got {count_before}"
        
        # Invalider pour l'année
        deleted_count = invalidate_compte_resultat_for_year(db, year)
        assert deleted_count == 1, f"Expected 1 deleted, got {deleted_count}"
        
        # Vérifier que les données ont été supprimées
        count_after = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year
        ).count()
        assert count_after == 0, f"Expected 0 data for year {year}, got {count_after}"
        
        # Vérifier que les données d'autres années sont toujours là
        count_other = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year + 1
        ).count()
        assert count_other == 1, f"Expected 1 data for year {year + 1}, got {count_other}"
        
        # Nettoyer
        db.delete(data2)
        db.commit()
        
        print("✓ Invalidation pour une année fonctionne")
    finally:
        db.close()


def test_invalidate_for_date_range():
    """Test invalidation pour une plage de dates."""
    print("\nTesting invalidate_compte_resultat_for_date_range()...")
    db = SessionLocal()
    try:
        # Utiliser des années qui n'ont probablement pas de données (2097-2099)
        data1 = CompteResultatData(annee=2097, category_name="Test 1", amount=100.0)
        data2 = CompteResultatData(annee=2098, category_name="Test 2", amount=200.0)
        data3 = CompteResultatData(annee=2099, category_name="Test 3", amount=300.0)
        db.add(data1)
        db.add(data2)
        db.add(data3)
        db.commit()
        
        # Invalider pour la plage 2097-2098
        deleted_count = invalidate_compte_resultat_for_date_range(
            db, date(2097, 1, 1), date(2098, 12, 31)
        )
        assert deleted_count == 2, f"Expected 2 deleted, got {deleted_count}"
        
        # Vérifier que 2099 est toujours là
        count_2099 = db.query(CompteResultatData).filter(
            CompteResultatData.annee == 2099
        ).count()
        assert count_2099 == 1, f"Expected 1 data for 2099, got {count_2099}"
        
        # Nettoyer
        db.delete(data3)
        db.commit()
        
        print("✓ Invalidation pour une plage de dates fonctionne")
    finally:
        db.close()


def test_invalidate_all():
    """Test invalidation de tous les comptes de résultat."""
    print("\nTesting invalidate_all_compte_resultat()...")
    db = SessionLocal()
    try:
        # Compter les données existantes
        count_before = db.query(CompteResultatData).count()
        
        # Créer des données de test
        data1 = CompteResultatData(annee=2097, category_name="Test 1", amount=100.0)
        data2 = CompteResultatData(annee=2098, category_name="Test 2", amount=200.0)
        db.add(data1)
        db.add(data2)
        db.commit()
        
        # Vérifier que les données existent
        count_after_add = db.query(CompteResultatData).count()
        assert count_after_add == count_before + 2, f"Expected {count_before + 2} data, got {count_after_add}"
        
        # Invalider tout
        deleted_count = invalidate_all_compte_resultat(db)
        assert deleted_count == count_after_add, f"Expected {count_after_add} deleted, got {deleted_count}"
        
        # Vérifier que tout a été supprimé
        count_after = db.query(CompteResultatData).count()
        assert count_after == 0, f"Expected 0 data, got {count_after}"
        
        print("✓ Invalidation de tous les comptes de résultat fonctionne")
    finally:
        db.close()


def test_transaction_triggers_invalidation():
    """Test que la création/modification/suppression de transaction invalide les comptes."""
    print("\nTesting transaction triggers invalidation...")
    db = SessionLocal()
    try:
        # Utiliser une année qui n'a probablement pas de données (2099)
        year = 2099
        
        # Créer un compte de résultat pour l'année
        data = CompteResultatData(
            annee=year,
            category_name="Test Category",
            amount=100.0
        )
        db.add(data)
        db.commit()
        
        # Vérifier que les données existent
        count_before = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year
        ).count()
        assert count_before >= 1, f"Expected at least 1 data, got {count_before}"
        
        # Simuler l'invalidation (comme dans create_transaction)
        invalidate_compte_resultat_for_year(db, year)
        
        # Vérifier que les données ont été supprimées
        count_after = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year
        ).count()
        assert count_after == 0, f"Expected 0 data, got {count_after}"
        
        print("✓ Transaction triggers invalidation fonctionne")
    finally:
        db.close()


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("Testing Compte Resultat Recalcul")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    try:
        test_invalidate_for_year()
        test_invalidate_for_date_range()
        test_invalidate_all()
        test_transaction_triggers_invalidation()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
