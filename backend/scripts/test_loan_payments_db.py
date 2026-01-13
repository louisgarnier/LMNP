"""
Script de test pour vérifier les mensualités de crédit en base de données par crédit.

Usage: python3 backend/scripts/test_loan_payments_db.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import LoanConfig, LoanPayment
from sqlalchemy import inspect, text, func

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
    """Affiche des statistiques par crédit."""
    print_section("4. Statistiques par crédit")
    
    db = SessionLocal()
    try:
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
        print(f"{'Crédit':<30} {'Nb':>6} {'Capital':>15} {'Intérêts':>15} {'Assurance':>15} {'Total':>15}")
        print(f"{'─' * 100}")
        
        for stat in stats:
            print(f"{stat.loan_name:<30} "
                  f"{stat.count:>6} "
                  f"{stat.total_capital or 0:>15,.2f} "
                  f"{stat.total_interest or 0:>15,.2f} "
                  f"{stat.total_insurance or 0:>15,.2f} "
                  f"{stat.total_amount or 0:>15,.2f}")
            if stat.min_date and stat.max_date:
                print(f"   Période: {stat.min_date.strftime('%d/%m/%Y')} → {stat.max_date.strftime('%d/%m/%Y')}")
    finally:
        db.close()

def test_orphan_payments():
    """Détecte les mensualités sans configuration associée."""
    print_section("5. Vérification des mensualités orphelines")
    
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
            for loan_name in orphan_loans:
                count = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).count()
                print(f"   - '{loan_name}': {count} mensualité(s)")
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
