"""
Test du service de calcul du Bilan (Step 10.2).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_service_step10_2.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import date
from backend.database import SessionLocal
from backend.database.models import (
    BilanMapping, BilanData, Transaction, EnrichedTransaction,
    AmortizationResult, LoanPayment, LoanConfig, CompteResultatData
)
from backend.api.services import bilan_service


def test_get_mappings():
    """Test de la fonction get_mappings."""
    print("🧪 Test get_mappings...")
    db = SessionLocal()
    try:
        mappings = bilan_service.get_mappings(db)
        print(f"  ✅ {len(mappings)} mapping(s) trouvé(s)")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_normal_category():
    """Test de la fonction calculate_normal_category."""
    print("🧪 Test calculate_normal_category...")
    db = SessionLocal()
    try:
        # Créer un mapping de test
        mapping = BilanMapping(
            category_name="Immobilisations",
            level_1_values=["Achat immobilier"],
            type="ACTIF",
            sub_category="Actif immobilisé",
            is_special=False,
            special_source=None,
            amortization_view_id=None
        )
        db.add(mapping)
        db.commit()
        
        # Tester le calcul (même sans transactions, devrait retourner 0.0)
        amount = bilan_service.calculate_normal_category(2024, mapping, None, db)
        assert amount == 0.0 or amount is not None, "Le calcul devrait retourner un nombre"
        print(f"  ✅ Calcul normal category: {amount}")
        
        # Nettoyer
        db.delete(mapping)
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_amortizations_cumul():
    """Test de la fonction calculate_amortizations_cumul."""
    print("🧪 Test calculate_amortizations_cumul...")
    db = SessionLocal()
    try:
        # Tester sans vue d'amortissement
        amount = bilan_service.calculate_amortizations_cumul(2024, None, db)
        assert amount <= 0.0, "Les amortissements cumulés devraient être négatifs"
        print(f"  ✅ Calcul amortizations cumul: {amount}")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_compte_bancaire():
    """Test de la fonction calculate_compte_bancaire."""
    print("🧪 Test calculate_compte_bancaire...")
    db = SessionLocal()
    try:
        amount = bilan_service.calculate_compte_bancaire(2024, db)
        assert amount is not None, "Le calcul devrait retourner un nombre"
        print(f"  ✅ Calcul compte bancaire: {amount}")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_resultat_exercice():
    """Test de la fonction calculate_resultat_exercice."""
    print("🧪 Test calculate_resultat_exercice...")
    db = SessionLocal()
    try:
        amount = bilan_service.calculate_resultat_exercice(2024, db)
        assert amount is not None, "Le calcul devrait retourner un nombre"
        print(f"  ✅ Calcul résultat exercice: {amount}")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_report_a_nouveau():
    """Test de la fonction calculate_report_a_nouveau."""
    print("🧪 Test calculate_report_a_nouveau...")
    db = SessionLocal()
    try:
        amount = bilan_service.calculate_report_a_nouveau(2024, db)
        assert amount is not None, "Le calcul devrait retourner un nombre"
        print(f"  ✅ Calcul report à nouveau: {amount}")
        
        # Test première année
        amount_first = bilan_service.calculate_report_a_nouveau(2020, db)
        assert amount_first == 0.0, "La première année devrait avoir un report à 0"
        print(f"  ✅ Première année: {amount_first}")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_capital_restant_du():
    """Test de la fonction calculate_capital_restant_du."""
    print("🧪 Test calculate_capital_restant_du...")
    db = SessionLocal()
    try:
        amount = bilan_service.calculate_capital_restant_du(2024, db)
        assert amount >= 0.0, "Le capital restant dû devrait être positif"
        print(f"  ✅ Calcul capital restant dû: {amount}")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_bilan():
    """Test de la fonction calculate_bilan."""
    print("🧪 Test calculate_bilan...")
    db = SessionLocal()
    try:
        # Créer quelques mappings de test
        mapping1 = BilanMapping(
            category_name="Immobilisations",
            level_1_values=["Achat immobilier"],
            type="ACTIF",
            sub_category="Actif immobilisé",
            is_special=False,
            special_source=None,
            amortization_view_id=None
        )
        mapping2 = BilanMapping(
            category_name="Capitaux propres",
            level_1_values=["Apport initial"],
            type="PASSIF",
            sub_category="Capitaux propres",
            is_special=False,
            special_source=None,
            amortization_view_id=None
        )
        db.add(mapping1)
        db.add(mapping2)
        db.commit()
        
        # Tester le calcul du bilan
        result = bilan_service.calculate_bilan(2024, [mapping1, mapping2], None, db)
        
        assert "categories" in result
        assert "sub_category_totals" in result
        assert "type_totals" in result
        assert "equilibre" in result
        
        assert "ACTIF" in result["type_totals"]
        assert "PASSIF" in result["type_totals"]
        
        assert "actif" in result["equilibre"]
        assert "passif" in result["equilibre"]
        assert "difference" in result["equilibre"]
        assert "percentage" in result["equilibre"]
        
        print(f"  ✅ Structure du résultat correcte")
        print(f"     ACTIF: {result['type_totals']['ACTIF']}")
        print(f"     PASSIF: {result['type_totals']['PASSIF']}")
        print(f"     Différence: {result['equilibre']['difference']}")
        print(f"     Pourcentage: {result['equilibre']['percentage']:.2f}%")
        
        # Nettoyer
        db.delete(mapping1)
        db.delete(mapping2)
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_invalidate_functions():
    """Test des fonctions d'invalidation."""
    print("🧪 Test invalidate functions...")
    db = SessionLocal()
    try:
        # Créer une donnée de test
        data = BilanData(
            annee=2024,
            category_name="Test",
            amount=100.0
        )
        db.add(data)
        db.commit()
        
        # Tester invalidate_bilan_for_year
        bilan_service.invalidate_bilan_for_year(2024, db)
        remaining = db.query(BilanData).filter(BilanData.annee == 2024).count()
        assert remaining == 0, "Les données de 2024 devraient être supprimées"
        print("  ✅ invalidate_bilan_for_year fonctionne")
        
        # Créer des données pour plusieurs années
        for year in [2023, 2024, 2025]:
            data = BilanData(annee=year, category_name="Test", amount=100.0)
            db.add(data)
        db.commit()
        
        # Tester invalidate_all_bilan
        bilan_service.invalidate_all_bilan(db)
        remaining = db.query(BilanData).count()
        assert remaining == 0, "Toutes les données devraient être supprimées"
        print("  ✅ invalidate_all_bilan fonctionne")
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_get_bilan_data():
    """Test de la fonction get_bilan_data."""
    print("🧪 Test get_bilan_data...")
    db = SessionLocal()
    try:
        # Créer des données de test
        for year in [2023, 2024, 2025]:
            data = BilanData(annee=year, category_name="Test", amount=100.0)
            db.add(data)
        db.commit()
        
        # Test sans filtre
        all_data = bilan_service.get_bilan_data(db)
        assert len(all_data) >= 3, "Devrait retourner au moins 3 données"
        print(f"  ✅ Sans filtre: {len(all_data)} données")
        
        # Test avec filtre année
        year_data = bilan_service.get_bilan_data(db, year=2024)
        assert len(year_data) >= 1, "Devrait retourner au moins 1 donnée pour 2024"
        print(f"  ✅ Avec filtre année: {len(year_data)} données")
        
        # Test avec filtre start_year et end_year
        range_data = bilan_service.get_bilan_data(db, start_year=2023, end_year=2024)
        assert len(range_data) >= 2, "Devrait retourner au moins 2 données"
        print(f"  ✅ Avec filtre range: {len(range_data)} données")
        
        # Nettoyer
        db.query(BilanData).delete()
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Test du service de calcul du Bilan (Step 10.2)")
    print("=" * 60)
    print()
    
    try:
        test_get_mappings()
        print()
        test_calculate_normal_category()
        print()
        test_calculate_amortizations_cumul()
        print()
        test_calculate_compte_bancaire()
        print()
        test_calculate_resultat_exercice()
        print()
        test_calculate_report_a_nouveau()
        print()
        test_calculate_capital_restant_du()
        print()
        test_calculate_bilan()
        print()
        test_invalidate_functions()
        print()
        test_get_bilan_data()
        print()
        
        print("=" * 60)
        print("✅ Tous les tests sont passés !")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test échoué: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

