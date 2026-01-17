"""
Test script for Step 9.2: Bilan service.

This script tests:
1. get_mappings() - Récupération des mappings
2. get_level_3_values() - Récupération de la config
3. calculate_normal_category() - Calcul des catégories normales
4. calculate_amortizations_cumul() - Calcul des amortissements cumulés
5. calculate_compte_bancaire() - Calcul du solde bancaire
6. calculate_resultat_exercice() - Calcul du résultat de l'exercice
7. calculate_report_a_nouveau() - Calcul du report à nouveau
8. calculate_capital_restant_du() - Calcul du capital restant dû
9. calculate_bilan() - Calcul complet du bilan avec totaux et équilibre

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import (
    BilanMapping, BilanConfig, Transaction, EnrichedTransaction,
    AmortizationResult, LoanConfig, LoanPayment
)
from backend.api.services.bilan_service import (
    get_mappings, get_level_3_values, calculate_normal_category,
    calculate_amortizations_cumul, calculate_compte_bancaire,
    calculate_resultat_exercice, calculate_report_a_nouveau,
    calculate_capital_restant_du, calculate_bilan
)


def test_get_mappings():
    """Test get_mappings()."""
    print("📋 Testing get_mappings()...")
    
    db = SessionLocal()
    try:
        mappings = get_mappings(db)
        print(f"✅ get_mappings() returned {len(mappings)} mapping(s)")
        return True
    except Exception as e:
        print(f"❌ Error in get_mappings(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_get_level_3_values():
    """Test get_level_3_values()."""
    print("\n📋 Testing get_level_3_values()...")
    
    db = SessionLocal()
    try:
        # Créer une config si elle n'existe pas
        config = db.query(BilanConfig).first()
        if not config:
            config = BilanConfig(level_3_values=json.dumps(["VALEUR1", "VALEUR2"]))
            db.add(config)
            db.commit()
        
        values = get_level_3_values(db)
        print(f"✅ get_level_3_values() returned: {values}")
        return True
    except Exception as e:
        print(f"❌ Error in get_level_3_values(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_amortizations_cumul():
    """Test calculate_amortizations_cumul()."""
    print("\n📋 Testing calculate_amortizations_cumul()...")
    
    db = SessionLocal()
    try:
        # Vérifier s'il y a des amortissements
        count = db.query(AmortizationResult).count()
        print(f"   ℹ️  {count} amortization result(s) in database")
        
        result = calculate_amortizations_cumul(db, 2024)
        print(f"✅ calculate_amortizations_cumul(2024) = {result:.2f} €")
        return True
    except Exception as e:
        print(f"❌ Error in calculate_amortizations_cumul(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_compte_bancaire():
    """Test calculate_compte_bancaire()."""
    print("\n📋 Testing calculate_compte_bancaire()...")
    
    db = SessionLocal()
    try:
        # Vérifier s'il y a des transactions
        count = db.query(Transaction).count()
        print(f"   ℹ️  {count} transaction(s) in database")
        
        result = calculate_compte_bancaire(db, 2024)
        print(f"✅ calculate_compte_bancaire(2024) = {result:.2f} €")
        return True
    except Exception as e:
        print(f"❌ Error in calculate_compte_bancaire(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_resultat_exercice():
    """Test calculate_resultat_exercice()."""
    print("\n📋 Testing calculate_resultat_exercice()...")
    
    db = SessionLocal()
    try:
        result = calculate_resultat_exercice(db, 2024)
        print(f"✅ calculate_resultat_exercice(2024) = {result:.2f} €")
        return True
    except Exception as e:
        print(f"❌ Error in calculate_resultat_exercice(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_report_a_nouveau():
    """Test calculate_report_a_nouveau()."""
    print("\n📋 Testing calculate_report_a_nouveau()...")
    
    db = SessionLocal()
    try:
        result = calculate_report_a_nouveau(db, 2024)
        print(f"✅ calculate_report_a_nouveau(2024) = {result:.2f} €")
        return True
    except Exception as e:
        print(f"❌ Error in calculate_report_a_nouveau(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_capital_restant_du():
    """Test calculate_capital_restant_du()."""
    print("\n📋 Testing calculate_capital_restant_du()...")
    
    db = SessionLocal()
    try:
        # Vérifier s'il y a des crédits configurés
        loan_configs = db.query(LoanConfig).count()
        print(f"   ℹ️  {loan_configs} loan config(s) in database")
        
        result = calculate_capital_restant_du(db, 2024)
        print(f"✅ calculate_capital_restant_du(2024) = {result:.2f} €")
        return True
    except Exception as e:
        print(f"❌ Error in calculate_capital_restant_du(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_calculate_normal_category():
    """Test calculate_normal_category()."""
    print("\n📋 Testing calculate_normal_category()...")
    
    db = SessionLocal()
    try:
        # Créer un mapping de test
        mapping = BilanMapping(
            category_name="Test Category",
            type="ACTIF",
            sub_category="Test Sub Category",
            level_1_values=json.dumps(["TEST_LEVEL_1"]),
            is_special=False
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        level_3_values = ["VALEUR1", "VALEUR2"]
        result = calculate_normal_category(db, 2024, mapping, level_3_values)
        print(f"✅ calculate_normal_category(2024) = {result:.2f} €")
        
        # Nettoyer
        db.delete(mapping)
        db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Error in calculate_normal_category(): {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_calculate_bilan():
    """Test calculate_bilan() - Calcul complet."""
    print("\n📋 Testing calculate_bilan()...")
    
    db = SessionLocal()
    try:
        # Créer quelques mappings de test si nécessaire
        mappings = db.query(BilanMapping).all()
        if not mappings:
            print("   ⚠️  No mappings found. Creating test mappings...")
            # Créer un mapping normal
            mapping1 = BilanMapping(
                category_name="Immobilisations",
                type="ACTIF",
                sub_category="Actif immobilisé",
                level_1_values=json.dumps(["IMMOBILISATIONS"]),
                is_special=False
            )
            db.add(mapping1)
            
            # Créer un mapping spécial (amortissements)
            mapping2 = BilanMapping(
                category_name="Amortissements cumulés",
                type="ACTIF",
                sub_category="Actif immobilisé",
                level_1_values=None,
                is_special=True,
                special_source="amortization_result"
            )
            db.add(mapping2)
            
            # Créer un mapping spécial (compte bancaire)
            mapping3 = BilanMapping(
                category_name="Compte bancaire",
                type="ACTIF",
                sub_category="Actif circulant",
                level_1_values=None,
                is_special=True,
                special_source="transactions"
            )
            db.add(mapping3)
            
            db.commit()
            print("   ✅ Test mappings created")
        
        # Calculer le bilan
        result = calculate_bilan(db, 2024)
        
        print(f"✅ calculate_bilan(2024) completed")
        print(f"   - Categories: {len(result.get('categories', {}))}")
        print(f"   - ACTIF total: {result.get('actif_total', 0):.2f} €")
        print(f"   - PASSIF total: {result.get('passif_total', 0):.2f} €")
        print(f"   - Différence: {result.get('difference', 0):.2f} €")
        print(f"   - Différence %: {result.get('difference_percent', 0):.2f}%")
        
        return True
    except Exception as e:
        print(f"❌ Error in calculate_bilan(): {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Bilan Service (Step 9.2)")
    print("=" * 60)
    
    # Initialiser la base de données
    print("\n1. Initializing database...")
    init_database()
    print("   ✅ Database initialized")
    
    results = []
    
    results.append(("get_mappings", test_get_mappings()))
    results.append(("get_level_3_values", test_get_level_3_values()))
    results.append(("calculate_amortizations_cumul", test_calculate_amortizations_cumul()))
    results.append(("calculate_compte_bancaire", test_calculate_compte_bancaire()))
    results.append(("calculate_resultat_exercice", test_calculate_resultat_exercice()))
    results.append(("calculate_report_a_nouveau", test_calculate_report_a_nouveau()))
    results.append(("calculate_capital_restant_du", test_calculate_capital_restant_du()))
    results.append(("calculate_normal_category", test_calculate_normal_category()))
    results.append(("calculate_bilan", test_calculate_bilan()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
