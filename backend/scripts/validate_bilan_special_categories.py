"""
Script de validation des catégories spéciales du bilan (Step 9.8.4).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script valide que chaque catégorie spéciale est correctement calculée et affichée.
"""

import sys
import os
from datetime import date

# Ajouter le chemin du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from backend.database.connection import get_db
from backend.database.models import (
    BilanMapping,
    Transaction,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatOverride
)
from backend.api.services.bilan_service import (
    get_mappings,
    get_level_3_values,
    calculate_amortizations_cumul,
    calculate_compte_bancaire,
    calculate_resultat_exercice,
    calculate_report_a_nouveau,
    calculate_capital_restant_du,
    calculate_bilan
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat
from sqlalchemy import func

def print_section(title: str):
    """Afficher un titre de section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_test(test_name: str, passed: bool, details: str = ""):
    """Afficher le résultat d'un test."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"      {details}")

def validate_amortizations_cumules(db, years: list):
    """Valider Step 9.8.4.1 : Amortissements cumulés."""
    print_section("Step 9.8.4.1 : Amortissements cumulés")
    
    # Trouver le mapping pour "Amortissements cumulés"
    mappings = get_mappings(db)
    amort_mapping = next((m for m in mappings if m.category_name == "Amortissements cumulés"), None)
    
    if not amort_mapping:
        print_test("Mapping 'Amortissements cumulés' existe", False, "Mapping introuvable")
        return False
    
    print_test("Mapping 'Amortissements cumulés' existe", True)
    print_test("Source spéciale correcte", amort_mapping.special_source == "amortization_result", 
               f"Source: {amort_mapping.special_source}")
    print_test("Position sous 'Immobilisations'", amort_mapping.sub_category == "Actif immobilisé",
               f"Sous-catégorie: {amort_mapping.sub_category}")
    
    all_passed = True
    
    for year in years:
        # Calculer via la fonction dédiée
        calculated = calculate_amortizations_cumul(db, year)
        
        # Vérifier manuellement
        manual_calc = db.query(func.sum(AmortizationResult.amount)).filter(
            AmortizationResult.year <= year
        ).scalar()
        manual_calc = manual_calc if manual_calc is not None else 0.0
        
        # Le montant doit être négatif (diminution de l'actif)
        is_negative = calculated < 0 or calculated == 0
        matches_manual = abs(calculated - manual_calc) < 0.01
        
        print_test(f"Année {year}: Montant négatif", is_negative, 
                   f"Montant: {calculated:.2f}€")
        print_test(f"Année {year}: Calcul correct", matches_manual,
                   f"Calculé: {calculated:.2f}€, Manuel: {manual_calc:.2f}€")
        
        if not (is_negative and matches_manual):
            all_passed = False
    
    return all_passed

def validate_compte_bancaire(db, years: list):
    """Valider Step 9.8.4.2 : Compte bancaire."""
    print_section("Step 9.8.4.2 : Compte bancaire")
    
    mappings = get_mappings(db)
    compte_mapping = next((m for m in mappings if m.category_name == "Compte bancaire"), None)
    
    if not compte_mapping:
        print_test("Mapping 'Compte bancaire' existe", False, "Mapping introuvable")
        return False
    
    print_test("Mapping 'Compte bancaire' existe", True)
    print_test("Source spéciale correcte", compte_mapping.special_source == "transactions",
               f"Source: {compte_mapping.special_source}")
    print_test("Position dans 'Actif circulant'", compte_mapping.sub_category == "Actif circulant",
               f"Sous-catégorie: {compte_mapping.sub_category}")
    
    all_passed = True
    
    for year in years:
        calculated = calculate_compte_bancaire(db, year)
        
        # Vérifier manuellement : dernière transaction de l'année
        end_date = date(year, 12, 31)
        last_transaction = db.query(Transaction).filter(
            Transaction.date <= end_date
        ).order_by(
            Transaction.date.desc(),
            Transaction.id.desc()
        ).first()
        
        manual_solde = last_transaction.solde if last_transaction else 0.0
        
        # Le montant doit être positif (actif)
        is_positive = calculated >= 0
        matches_manual = abs(calculated - manual_solde) < 0.01
        
        print_test(f"Année {year}: Montant positif", is_positive,
                   f"Montant: {calculated:.2f}€")
        print_test(f"Année {year}: Solde final correct", matches_manual,
                   f"Calculé: {calculated:.2f}€, Dernière transaction: {manual_solde:.2f}€")
        
        if not (is_positive and matches_manual):
            all_passed = False
    
    return all_passed

def validate_resultat_exercice(db, years: list):
    """Valider Step 9.8.4.3 : Résultat de l'exercice."""
    print_section("Step 9.8.4.3 : Résultat de l'exercice")
    
    mappings = get_mappings(db)
    resultat_mapping = next((m for m in mappings if "Résultat" in m.category_name and "exercice" in m.category_name.lower()), None)
    
    if not resultat_mapping:
        print_test("Mapping 'Résultat de l'exercice' existe", False, "Mapping introuvable")
        return False
    
    print_test("Mapping 'Résultat de l'exercice' existe", True)
    print_test("Source spéciale correcte", resultat_mapping.special_source == "compte_resultat",
               f"Source: {resultat_mapping.special_source}")
    print_test("Position dans 'Capitaux propres'", resultat_mapping.sub_category == "Capitaux propres",
               f"Sous-catégorie: {resultat_mapping.sub_category}")
    
    all_passed = True
    
    for year in years:
        calculated = calculate_resultat_exercice(db, year, resultat_mapping.compte_resultat_view_id)
        
        # Vérifier via compte de résultat
        compte_resultat = calculate_compte_resultat(db, year)
        expected = compte_resultat.get("resultat_net", 0.0)
        
        # Vérifier s'il y a un override
        override = db.query(CompteResultatOverride).filter(
            CompteResultatOverride.year == year
        ).first()
        
        if override:
            expected = override.override_value
            print_test(f"Année {year}: Override présent", True, f"Valeur override: {expected:.2f}€")
        
        matches_expected = abs(calculated - expected) < 0.01
        
        # Le montant peut être positif (bénéfice) ou négatif (perte)
        print_test(f"Année {year}: Calcul correct", matches_expected,
                   f"Calculé: {calculated:.2f}€, Attendu: {expected:.2f}€")
        
        if not matches_expected:
            all_passed = False
    
    return all_passed

def validate_report_a_nouveau(db, years: list):
    """Valider Step 9.8.4.4 : Report à nouveau."""
    print_section("Step 9.8.4.4 : Report à nouveau")
    
    mappings = get_mappings(db)
    report_mapping = next((m for m in mappings if "Report" in m.category_name or "report" in m.category_name.lower()), None)
    
    if not report_mapping:
        print_test("Mapping 'Report à nouveau' existe", False, "Mapping introuvable")
        return False
    
    print_test("Mapping 'Report à nouveau' existe", True)
    print_test("Source spéciale correcte", report_mapping.special_source == "compte_resultat_cumul",
               f"Source: {report_mapping.special_source}")
    print_test("Position dans 'Capitaux propres'", report_mapping.sub_category == "Capitaux propres",
               f"Sous-catégorie: {report_mapping.sub_category}")
    
    all_passed = True
    
    # Trouver la première année avec transactions
    first_transaction = db.query(func.min(Transaction.date)).scalar()
    first_year = first_transaction.year if first_transaction else min(years)
    
    for year in years:
        calculated = calculate_report_a_nouveau(db, year)
        
        # Première année doit être 0
        if year <= first_year:
            is_zero = abs(calculated) < 0.01
            print_test(f"Année {year}: Première année = 0", is_zero,
                       f"Montant: {calculated:.2f}€")
            if not is_zero:
                all_passed = False
        else:
            # Vérifier le cumul manuellement
            total = 0.0
            for prev_year in range(first_year, year):
                resultat = calculate_resultat_exercice(db, prev_year)
                total += resultat
            
            matches_manual = abs(calculated - total) < 0.01
            print_test(f"Année {year}: Cumul correct", matches_manual,
                       f"Calculé: {calculated:.2f}€, Manuel: {total:.2f}€")
            
            if not matches_manual:
                all_passed = False
    
    return all_passed

def validate_emprunt_bancaire(db, years: list):
    """Valider Step 9.8.4.5 : Emprunt bancaire."""
    print_section("Step 9.8.4.5 : Emprunt bancaire")
    
    mappings = get_mappings(db)
    emprunt_mapping = next((m for m in mappings if "Emprunt" in m.category_name or "emprunt" in m.category_name.lower()), None)
    
    if not emprunt_mapping:
        print_test("Mapping 'Emprunt bancaire' existe", False, "Mapping introuvable")
        return False
    
    print_test("Mapping 'Emprunt bancaire' existe", True)
    print_test("Source spéciale correcte", emprunt_mapping.special_source == "loan_payments",
               f"Source: {emprunt_mapping.special_source}")
    print_test("Position dans 'Dettes financières'", emprunt_mapping.sub_category == "Dettes financières",
               f"Sous-catégorie: {emprunt_mapping.sub_category}")
    
    all_passed = True
    
    for year in years:
        calculated = calculate_capital_restant_du(db, year)
        
        # Vérifier manuellement
        end_date = date(year, 12, 31)
        loan_configs = db.query(LoanConfig).all()
        
        manual_total = 0.0
        for loan_config in loan_configs:
            credit_amount = loan_config.credit_amount
            # Cumul des remboursements de capital jusqu'à la fin de l'année
            # Note: LoanPayment utilise loan_name, LoanConfig utilise name
            capital_repaid = db.query(func.sum(LoanPayment.capital)).filter(
                LoanPayment.loan_name == loan_config.name,
                LoanPayment.date <= end_date
            ).scalar()
            capital_repaid = capital_repaid if capital_repaid is not None else 0.0
            
            remaining = credit_amount - capital_repaid
            manual_total += remaining
        
        # Le montant doit être positif (dette)
        is_positive = calculated >= 0
        matches_manual = abs(calculated - manual_total) < 0.01
        
        print_test(f"Année {year}: Montant positif", is_positive,
                   f"Montant: {calculated:.2f}€")
        print_test(f"Année {year}: Calcul correct", matches_manual,
                   f"Calculé: {calculated:.2f}€, Manuel: {manual_total:.2f}€")
        
        if not (is_positive and matches_manual):
            all_passed = False
    
    return all_passed

def main():
    """Fonction principale."""
    print("=" * 80)
    print("VALIDATION DES CATÉGORIES SPÉCIALES DU BILAN (Step 9.8.4)")
    print("=" * 80)
    
    db = next(get_db())
    
    # Années à tester
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    
    results = {}
    
    # Valider chaque catégorie spéciale
    results['amortizations'] = validate_amortizations_cumules(db, years)
    results['compte_bancaire'] = validate_compte_bancaire(db, years)
    results['resultat_exercice'] = validate_resultat_exercice(db, years)
    results['report_a_nouveau'] = validate_report_a_nouveau(db, years)
    results['emprunt_bancaire'] = validate_emprunt_bancaire(db, years)
    
    # Résumé
    print_section("RÉSUMÉ")
    
    all_passed = True
    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {category}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TOUTES LES VALIDATIONS SONT PASSÉES")
    else:
        print("❌ CERTAINES VALIDATIONS ONT ÉCHOUÉ")
    print("=" * 80)
    
    db.close()

if __name__ == "__main__":
    main()
