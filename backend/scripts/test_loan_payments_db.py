"""
Script de test pour vérifier les mensualités de crédit en base de données par crédit.

Usage: python3 backend/scripts/test_loan_payments_db.py
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import LoanConfig, LoanPayment
from sqlalchemy import inspect, text, func

def yearfrac(date1: date | None, date2: date | None) -> float | None:
    """
    Fonction équivalente à YEARFRAC(date1, date2, 3) d'Excel
    Base 3 = année réelle/365 (nombre réel de jours dans l'année)
    """
    if not date1 or not date2:
        return None
    diff_days = (date2 - date1).days
    return diff_days / 365.0

def calculate_months_elapsed(start_date: date | None) -> int | None:
    """
    Calcule le nombre de mois écoulés depuis la date d'emprunt
    ROUND(YEARFRAC(date_emprunt, date_du_jour, 3) * 12, 0)
    """
    if not start_date:
        return None
    today = date.today()
    years = yearfrac(start_date, today)
    if years is None:
        return None
    return round(years * 12)

def calculate_months_remaining(end_date: date | None) -> int | None:
    """
    Calcule le nombre de mois restants jusqu'à la date de fin
    ROUND(YEARFRAC(date_du_jour, date_fin, 3) * 12, 0)
    """
    if not end_date:
        return None
    today = date.today()
    years = yearfrac(today, end_date)
    if years is None:
        return None
    return round(years * 12)

def format_remaining_duration(months: int | None) -> str:
    """
    Formate la durée restante en "X ans et Y mois"
    """
    if months is None or months < 0:
        return '-'
    years = months // 12
    remaining_months = round(((months / 12) - (months // 12)) * 12)
    if years == 0:
        return f"{remaining_months} mois"
    elif remaining_months == 0:
        return f"{years} ans"
    else:
        return f"{years} ans et {remaining_months} mois"

def print_section(title):
    """Affiche une section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_table_structure():
    """Vérifie la structure de la table loan_payments."""
    print_section("1. Structure de la table loan_payments")
    
    inspector = inspect(engine)
    
    # Vérifier que la table existe
    tables = inspector.get_table_names()
    if 'loan_payments' not in tables:
        print("❌ Table 'loan_payments' n'existe pas !")
        return False
    
    print("✅ Table 'loan_payments' existe")
    
    # Afficher les colonnes
    columns = inspector.get_columns('loan_payments')
    print(f"\n📋 Colonnes ({len(columns)}):")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"   - {col['name']}: {col['type']} {nullable}{default}")
    
    return True

def test_list_all_loans():
    """Liste tous les crédits avec leurs configurations et mensualités."""
    print_section("2. Liste de tous les crédits avec leurs données")
    
    db = SessionLocal()
    try:
        # Récupérer toutes les configurations
        configs = db.query(LoanConfig).order_by(LoanConfig.name).all()
        
        if not configs:
            print("⚠️  Aucune configuration de crédit trouvée")
            return []
        
        print(f"📋 {len(configs)} crédit(s) trouvé(s):\n")
        
        for config in configs:
            print(f"\n{'─' * 60}")
            print(f"💰 CRÉDIT: {config.name} (ID: {config.id})")
            print(f"{'─' * 60}")
            
            # Informations de la configuration
            print(f"\n📊 Configuration:")
            print(f"   - Crédit accordé: {config.credit_amount:,.2f} €")
            print(f"   - Taux fixe: {config.interest_rate} %")
            print(f"   - Durée: {config.duration_years} ans")
            print(f"   - Décalage initial: {config.initial_deferral_months} mois")
            if config.loan_start_date:
                print(f"   - Date d'emprunt: {config.loan_start_date.strftime('%d/%m/%Y')}")
            else:
                print(f"   - Date d'emprunt: (non définie)")
            if config.loan_end_date:
                print(f"   - Date de fin prévisionnelle: {config.loan_end_date.strftime('%d/%m/%Y')}")
            else:
                print(f"   - Date de fin prévisionnelle: (non définie)")
            
            # Calculs automatiques
            if config.loan_start_date and config.loan_end_date:
                duration_years = yearfrac(config.loan_start_date, config.loan_end_date)
                duration_years_with_deferral = duration_years - (config.initial_deferral_months / 12) if duration_years else None
                months_elapsed = calculate_months_elapsed(config.loan_start_date)
                months_remaining = calculate_months_remaining(config.loan_end_date)
                remaining_duration = format_remaining_duration(months_remaining)
                
                print(f"\n   📈 Calculs automatiques:")
                if duration_years is not None:
                    print(f"   - Durée crédit (années): {duration_years:.2f} ans")
                if duration_years_with_deferral is not None:
                    print(f"   - Durée crédit (années) incluant différé: {duration_years_with_deferral:.2f} ans")
                if months_elapsed is not None:
                    print(f"   - Nombre de mois écoulés: {months_elapsed} mois")
                if months_remaining is not None:
                    print(f"   - Nombre de mois restants: {months_remaining} mois")
                if remaining_duration != '-':
                    print(f"   - Durée restante: {remaining_duration}")
            
            print(f"   - Créé le: {config.created_at}")
            
            # Récupérer les mensualités pour ce crédit
            payments = db.query(LoanPayment).filter(
                LoanPayment.loan_name == config.name
            ).order_by(LoanPayment.date).all()
            
            print(f"\n📅 Mensualités: {len(payments)} ligne(s)")
            
            if payments:
                # Statistiques
                total_capital = sum(p.capital for p in payments)
                total_interest = sum(p.interest for p in payments)
                total_insurance = sum(p.insurance for p in payments)
                total_amount = sum(p.total for p in payments)
                
                print(f"\n   Totaux:")
                print(f"   - Capital: {total_capital:,.2f} €")
                print(f"   - Intérêts: {total_interest:,.2f} €")
                print(f"   - Assurance: {total_insurance:,.2f} €")
                print(f"   - Total: {total_amount:,.2f} €")
                
                # Dates min/max
                dates = [p.date for p in payments]
                min_date = min(dates)
                max_date = max(dates)
                print(f"\n   Période:")
                print(f"   - Du: {min_date.strftime('%d/%m/%Y')}")
                print(f"   - Au: {max_date.strftime('%d/%m/%Y')}")
                
                # Afficher les 10 premières et dernières mensualités
                print(f"\n   📋 Détail des mensualités:")
                print(f"   {'Date':<12} {'Capital':>12} {'Intérêts':>12} {'Assurance':>12} {'Total':>12}")
                print(f"   {'─' * 60}")
                
                # Premières 5
                for payment in payments[:5]:
                    print(f"   {payment.date.strftime('%d/%m/%Y'):<12} "
                          f"{payment.capital:>12,.2f} "
                          f"{payment.interest:>12,.2f} "
                          f"{payment.insurance:>12,.2f} "
                          f"{payment.total:>12,.2f}")
                
                if len(payments) > 10:
                    print(f"   {'...':<12} {'...':>12} {'...':>12} {'...':>12} {'...':>12}")
                
                # Dernières 5
                for payment in payments[-5:]:
                    print(f"   {payment.date.strftime('%d/%m/%Y'):<12} "
                          f"{payment.capital:>12,.2f} "
                          f"{payment.interest:>12,.2f} "
                          f"{payment.insurance:>12,.2f} "
                          f"{payment.total:>12,.2f}")
            else:
                print(f"   ⚠️  Aucune mensualité trouvée pour ce crédit")
        
        return configs
    finally:
        db.close()

def test_payments_by_loan_name(loan_name: str):
    """Affiche les mensualités pour un crédit spécifique."""
    print_section(f"3. Mensualités pour le crédit: {loan_name}")
    
    db = SessionLocal()
    try:
        payments = db.query(LoanPayment).filter(
            LoanPayment.loan_name == loan_name
        ).order_by(LoanPayment.date).all()
        
        if not payments:
            print(f"⚠️  Aucune mensualité trouvée pour '{loan_name}'")
            return []
        
        print(f"📋 {len(payments)} mensualité(s) trouvée(s):\n")
        print(f"{'ID':<6} {'Date':<12} {'Capital':>12} {'Intérêts':>12} {'Assurance':>12} {'Total':>12}")
        print(f"{'─' * 70}")
        
        for payment in payments:
            print(f"{payment.id:<6} "
                  f"{payment.date.strftime('%d/%m/%Y'):<12} "
                  f"{payment.capital:>12,.2f} "
                  f"{payment.interest:>12,.2f} "
                  f"{payment.insurance:>12,.2f} "
                  f"{payment.total:>12,.2f}")
        
        return payments
    finally:
        db.close()

def test_statistics_by_loan():
    """Affiche des statistiques par crédit (basées sur les mensualités, pas les configurations)."""
    print_section("4. Statistiques par crédit (basées sur les mensualités)")
    print("⚠️  NOTE: Cette section liste tous les crédits qui ont des mensualités en base,")
    print("    même si leur configuration n'existe plus (mensualités orphelines).\n")
    
    db = SessionLocal()
    try:
        # Récupérer les noms de crédits valides (qui ont une configuration)
        valid_loan_names = set(row[0] for row in db.query(LoanConfig.name).all())
        
        # Grouper par loan_name
        stats = db.query(
            LoanPayment.loan_name,
            func.count(LoanPayment.id).label('count'),
            func.sum(LoanPayment.capital).label('total_capital'),
            func.sum(LoanPayment.interest).label('total_interest'),
            func.sum(LoanPayment.insurance).label('total_insurance'),
            func.sum(LoanPayment.total).label('total_amount'),
            func.min(LoanPayment.date).label('min_date'),
            func.max(LoanPayment.date).label('max_date')
        ).group_by(LoanPayment.loan_name).all()
        
        if not stats:
            print("⚠️  Aucune statistique disponible")
            return
        
        print(f"📊 {len(stats)} crédit(s) avec des mensualités:\n")
        print(f"{'Crédit':<30} {'Nb':>6} {'Capital':>15} {'Intérêts':>15} {'Assurance':>15} {'Total':>15} {'Status':<10}")
        print(f"{'─' * 110}")
        
        for stat in stats:
            is_orphan = stat.loan_name not in valid_loan_names
            status = "⚠️ ORPHELIN" if is_orphan else "✅ OK"
            print(f"{stat.loan_name:<30} "
                  f"{stat.count:>6} "
                  f"{stat.total_capital or 0:>15,.2f} "
                  f"{stat.total_interest or 0:>15,.2f} "
                  f"{stat.total_insurance or 0:>15,.2f} "
                  f"{stat.total_amount or 0:>15,.2f} "
                  f"{status:<10}")
            if stat.min_date and stat.max_date:
                print(f"   Période: {stat.min_date.strftime('%d/%m/%Y')} → {stat.max_date.strftime('%d/%m/%Y')}")
    finally:
        db.close()

def test_orphan_payments():
    """Détecte les mensualités orphelines (sans configuration associée)."""
    print_section("5. Vérification des mensualités orphelines")
    print("⚠️  Les mensualités orphelines sont des mensualités dont le crédit a été supprimé")
    print("    ou n'a jamais eu de configuration. Elles doivent être supprimées.\n")
    
    db = SessionLocal()
    try:
        # Récupérer tous les noms de crédits uniques dans loan_payments
        payment_loans = db.query(LoanPayment.loan_name).distinct().all()
        payment_loan_names = [row[0] for row in payment_loans]
        
        # Récupérer tous les noms de crédits dans loan_configs
        config_loans = db.query(LoanConfig.name).all()
        config_loan_names = [row[0] for row in config_loans]
        
        # Trouver les orphelins
        orphan_loans = set(payment_loan_names) - set(config_loan_names)
        
        if orphan_loans:
            print(f"⚠️  {len(orphan_loans)} crédit(s) orphelin(s) détecté(s):")
            total_orphan_payments = 0
            for loan_name in orphan_loans:
                count = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).count()
                total_orphan_payments += count
                print(f"   - '{loan_name}': {count} mensualité(s)")
            print(f"\n📊 Total: {total_orphan_payments} mensualité(s) orpheline(s)")
            print(f"\n💡 Pour nettoyer, exécutez: python3 backend/scripts/cleanup_orphan_loan_payments.py")
        else:
            print("✅ Toutes les mensualités ont une configuration associée")
        
        # Trouver les configurations sans mensualités
        configs_without_payments = set(config_loan_names) - set(payment_loan_names)
        if configs_without_payments:
            print(f"\n📋 {len(configs_without_payments)} configuration(s) sans mensualités:")
            for loan_name in configs_without_payments:
                print(f"   - '{loan_name}'")
    finally:
        db.close()

def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("  TEST DES MENSUALITÉS DE CRÉDIT EN BASE DE DONNÉES")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Tests
    if not test_table_structure():
        print("\n❌ La table n'existe pas, arrêt des tests")
        return
    
    configs = test_list_all_loans()
    
    if configs:
        test_statistics_by_loan()
        test_orphan_payments()
        
        # Afficher les détails pour le premier crédit
        if configs:
            test_payments_by_loan_name(configs[0].name)
    else:
        print("\n⚠️  Aucune configuration en base de données")
        print("   Créez des configurations via l'interface web ou l'API")
    
    print("\n" + "=" * 60)
    print("  ✅ TESTS TERMINÉS")
    print("=" * 60)

if __name__ == "__main__":
    main()
