"""
Test des catégories spéciales du compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import date
from backend.database import SessionLocal
from backend.database.models import (
    CompteResultatMapping,
    AmortizationView,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    Transaction,
    EnrichedTransaction
)
from backend.api.services.compte_resultat_service import (
    get_amortissements,
    get_cout_financement,
    calculate_amounts_by_category_and_year
)
from sqlalchemy import func, and_


def test_charges_amortissements():
    """Test Step 7.6.4 : Validation des charges d'amortissements."""
    print("=" * 60)
    print("Test Step 7.6.4 : Charges d'amortissements")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Récupérer le mapping pour "Charges d'amortissements"
        mapping = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Charges d'amortissements"
        ).first()
        
        if not mapping:
            print("⚠️ Aucun mapping trouvé pour 'Charges d'amortissements'")
            return
        
        print(f"📋 Mapping trouvé : ID {mapping.id}")
        print(f"   - amortization_view_id: {mapping.amortization_view_id}")
        
        if not mapping.amortization_view_id:
            print("⚠️ Aucune vue d'amortissement sélectionnée")
            print("   → Le montant devrait être 0,00 € ou 'Vue non configurée'")
            return
        
        # Récupérer la vue d'amortissement
        view = db.query(AmortizationView).filter(
            AmortizationView.id == mapping.amortization_view_id
        ).first()
        
        if not view:
            print(f"❌ Vue d'amortissement ID {mapping.amortization_view_id} non trouvée")
            return
        
        print(f"📊 Vue d'amortissement : '{view.name}' (level_2: {view.level_2_value})")
        print()
        
        # Récupérer les années disponibles
        years = db.query(AmortizationResult.year).distinct().order_by(AmortizationResult.year).all()
        years = [y[0] for y in years]
        
        if not years:
            print("⚠️ Aucune année avec des résultats d'amortissement")
            return
        
        print(f"📅 Années disponibles : {years}")
        print()
        
        # Pour chaque année, vérifier le calcul
        for year in years:
            # Calculer via le service
            calculated_amount = get_amortissements(year, mapping.amortization_view_id, db)
            
            # Calculer manuellement depuis AmortizationResult
            manual_amount = db.query(
                func.sum(func.abs(AmortizationResult.amount))
            ).join(
                Transaction,
                AmortizationResult.transaction_id == Transaction.id
            ).join(
                EnrichedTransaction,
                Transaction.id == EnrichedTransaction.transaction_id
            ).filter(
                and_(
                    AmortizationResult.year == year,
                    EnrichedTransaction.level_2 == view.level_2_value
                )
            ).scalar() or 0.0
            
            # Vérifier
            match = abs(calculated_amount - manual_amount) < 0.01
            status = "✅" if match else "❌"
            
            print(f"{status} Année {year}:")
            print(f"   - Calculé via service: {calculated_amount:.2f} €")
            print(f"   - Calculé manuellement: {manual_amount:.2f} €")
            if not match:
                print(f"   ⚠️ Différence: {abs(calculated_amount - manual_amount):.2f} €")
            print()
        
        print("✅ Test des charges d'amortissements terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_cout_financement():
    """Test Step 7.6.5 : Validation du coût du financement."""
    print("=" * 60)
    print("Test Step 7.6.5 : Coût du financement")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Récupérer le mapping pour "Coût du financement"
        mapping = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Coût du financement (hors remboursement du capital)"
        ).first()
        
        if not mapping:
            print("⚠️ Aucun mapping trouvé pour 'Coût du financement (hors remboursement du capital)'")
            return
        
        print(f"📋 Mapping trouvé : ID {mapping.id}")
        print(f"   - selected_loan_ids: {mapping.selected_loan_ids}")
        
        if not mapping.selected_loan_ids:
            print("⚠️ Aucun crédit sélectionné")
            print("   → Le montant devrait être 0,00 € ou 'Crédits non configurés'")
            return
        
        # Parser les IDs de crédits
        loan_ids = mapping.selected_loan_ids
        if isinstance(loan_ids, str):
            import json
            loan_ids = json.loads(loan_ids)
        
        print(f"💰 Crédits sélectionnés : {loan_ids}")
        
        # Récupérer les noms des crédits
        loan_configs = db.query(LoanConfig).filter(LoanConfig.id.in_(loan_ids)).all()
        loan_names = [config.name for config in loan_configs]
        print(f"   - Noms: {loan_names}")
        print()
        
        # Récupérer les années disponibles
        years = db.query(func.extract('year', LoanPayment.date)).distinct().order_by(
            func.extract('year', LoanPayment.date)
        ).all()
        years = [int(y[0]) for y in years if y[0]]
        
        if not years:
            print("⚠️ Aucune année avec des loan_payments")
            return
        
        print(f"📅 Années disponibles : {years}")
        print()
        
        # Pour chaque année, vérifier le calcul
        for year in years:
            # Calculer via le service
            calculated_amount = get_cout_financement(year, loan_ids, db)
            
            # Calculer manuellement depuis LoanPayment
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            payments = db.query(LoanPayment).filter(
                and_(
                    LoanPayment.date >= start_date,
                    LoanPayment.date <= end_date,
                    LoanPayment.loan_name.in_(loan_names)
                )
            ).all()
            
            manual_amount = sum(payment.interest + payment.insurance for payment in payments)
            
            # Vérifier
            match = abs(calculated_amount - manual_amount) < 0.01
            status = "✅" if match else "❌"
            
            print(f"{status} Année {year}:")
            print(f"   - Calculé via service: {calculated_amount:.2f} €")
            print(f"   - Calculé manuellement: {manual_amount:.2f} €")
            print(f"   - Nombre de mensualités: {len(payments)}")
            if not match:
                print(f"   ⚠️ Différence: {abs(calculated_amount - manual_amount):.2f} €")
            print()
        
        print("✅ Test du coût du financement terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_calculate_amounts_integration():
    """Test d'intégration : vérifier que calculate_amounts_by_category_and_year utilise bien les mappings."""
    print("=" * 60)
    print("Test d'intégration : calculate_amounts_by_category_and_year")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Récupérer les années disponibles
        years = db.query(func.extract('year', Transaction.date)).distinct().order_by(
            func.extract('year', Transaction.date)
        ).all()
        years = [int(y[0]) for y in years if y[0] and y[0] >= 2020]  # Depuis 2020
        
        if not years:
            print("⚠️ Aucune année avec des transactions")
            return
        
        # Limiter aux 2 dernières années pour le test
        years = sorted(years)[-2:] if len(years) >= 2 else years
        
        print(f"📅 Test pour les années : {years}")
        print()
        
        # Calculer via le service
        results = calculate_amounts_by_category_and_year(years, db)
        
        # Vérifier les catégories spéciales
        for year in years:
            year_str = str(year)
            if year_str not in results:
                continue
            
            year_data = results[year]
            
            # Vérifier "Charges d'amortissements"
            if "Charges d'amortissements" in year_data:
                amount = year_data["Charges d'amortissements"]
                print(f"📊 Année {year} - Charges d'amortissements: {amount:.2f} €")
            
            # Vérifier "Coût du financement"
            if "Coût du financement (hors remboursement du capital)" in year_data:
                amount = year_data["Coût du financement (hors remboursement du capital)"]
                print(f"💰 Année {year} - Coût du financement: {amount:.2f} €")
        
        print()
        print("✅ Test d'intégration terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print()
    test_charges_amortissements()
    print()
    test_cout_financement()
    print()
    test_calculate_amounts_integration()
    print()
    print("=" * 60)
    print("✅ Tous les tests terminés")
    print("=" * 60)

