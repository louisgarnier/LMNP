"""
Script pour expliquer le calcul du coût du financement pour l'année 2023.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script détaille le calcul du "Coût du financement (hors remboursement du capital)"
pour l'année 2023 en affichant :
- Tous les crédits configurés
- Tous les loan_payments pour 2023
- Le détail par payment (interest + insurance)
- Le total calculé
"""

import sys
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.models import LoanConfig, LoanPayment, Base

# Chemin vers la base de données
DB_DIR = Path(__file__).parent.parent / "database"
DB_FILE = DB_DIR / "lmnp.db"

def explain_cout_financement(year: int = 2023):
    """
    Expliquer le calcul du coût du financement pour une année donnée.
    """
    if not DB_FILE.exists():
        print(f"❌ Base de données non trouvée : {DB_FILE}")
        return
    
    # Connexion à la base de données
    engine = create_engine(f'sqlite:///{DB_FILE}')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    print("=" * 80)
    print(f"📊 EXPLICATION DU CALCUL DU COÛT DU FINANCEMENT POUR L'ANNÉE {year}")
    print("=" * 80)
    print()
    
    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    print(f"📅 Période : du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}")
    print()
    
    # 1. Récupérer tous les crédits configurés
    print("1️⃣ CRÉDITS CONFIGURÉS")
    print("-" * 80)
    loan_configs = db.query(LoanConfig).all()
    
    if not loan_configs:
        print("   ⚠️  Aucun crédit configuré dans la base de données.")
        print()
        print("   Le coût du financement sera donc de 0.0")
        db.close()
        return
    
    print(f"   Nombre de crédits configurés : {len(loan_configs)}")
    print()
    
    for i, config in enumerate(loan_configs, 1):
        print(f"   Crédit #{i}:")
        print(f"      - ID : {config.id}")
        print(f"      - Nom : {config.name or 'N/A'}")
        print(f"      - Montant du crédit : {config.credit_amount:,.2f} €" if config.credit_amount else "      - Montant du crédit : N/A")
        print(f"      - Durée : {config.duration_years} ans" if config.duration_years else "      - Durée : N/A")
        print(f"      - Taux d'intérêt : {config.interest_rate}%" if config.interest_rate else "      - Taux d'intérêt : N/A")
        print(f"      - Assurance mensuelle : {config.monthly_insurance:,.2f} €" if config.monthly_insurance else "      - Assurance mensuelle : N/A")
        print(f"      - Date de début : {config.loan_start_date.strftime('%d/%m/%Y') if config.loan_start_date else 'N/A'}")
        print(f"      - Date de fin : {config.loan_end_date.strftime('%d/%m/%Y') if config.loan_end_date else 'N/A'}")
        print()
    
    # 2. Récupérer tous les loan_payments pour l'année
    print("2️⃣ PAIEMENTS (LOAN_PAYMENTS) POUR L'ANNÉE")
    print("-" * 80)
    payments = db.query(LoanPayment).filter(
        and_(
            LoanPayment.date >= start_date,
            LoanPayment.date <= end_date
        )
    ).order_by(LoanPayment.date).all()
    
    if not payments:
        print(f"   ⚠️  Aucun paiement trouvé pour l'année {year}.")
        print()
        print("   Le coût du financement sera donc de 0.0")
        db.close()
        return
    
    print(f"   Nombre de paiements trouvés : {len(payments)}")
    print()
    
    # 3. Détail par payment
    print("3️⃣ DÉTAIL DES PAIEMENTS")
    print("-" * 80)
    print(f"{'Date':<12} {'Nom crédit':<20} {'Intérêts':<15} {'Assurance':<15} {'Total (I+A)':<15}")
    print("-" * 80)
    
    total_cost = 0.0
    total_interest = 0.0
    total_insurance = 0.0
    
    for payment in payments:
        interest = payment.interest or 0.0
        insurance = payment.insurance or 0.0
        payment_total = interest + insurance
        
        total_interest += interest
        total_insurance += insurance
        total_cost += payment_total
        
        loan_name = payment.loan_name or 'N/A'
        if len(loan_name) > 18:
            loan_name = loan_name[:15] + '...'
        
        print(f"{payment.date.strftime('%d/%m/%Y'):<12} "
              f"{loan_name:<20} "
              f"{interest:>12,.2f} € "
              f"{insurance:>12,.2f} € "
              f"{payment_total:>12,.2f} €")
    
    print("-" * 80)
    print(f"{'TOTAL':<12} {'':<12} "
          f"{total_interest:>12,.2f} € "
          f"{total_insurance:>12,.2f} € "
          f"{total_cost:>12,.2f} €")
    print()
    
    # 4. Résumé
    print("4️⃣ RÉSUMÉ DU CALCUL")
    print("-" * 80)
    print(f"   Formule : Coût du financement = Σ (interest + insurance) pour tous les paiements de {year}")
    print()
    print(f"   - Nombre de crédits configurés : {len(loan_configs)}")
    print(f"   - Nombre de paiements en {year} : {len(payments)}")
    print(f"   - Total des intérêts : {total_interest:,.2f} €")
    print(f"   - Total des assurances : {total_insurance:,.2f} €")
    print(f"   - COÛT DU FINANCEMENT TOTAL : {total_cost:,.2f} €")
    print()
    
    # 5. Vérification avec le service
    print("5️⃣ VÉRIFICATION AVEC LE SERVICE")
    print("-" * 80)
    try:
        from backend.api.services.compte_resultat_service import get_cout_financement
        service_result = get_cout_financement(db, year)
        print(f"   Résultat du service get_cout_financement({year}) : {service_result:,.2f} €")
        
        if abs(service_result - total_cost) < 0.01:
            print("   ✅ Les calculs correspondent !")
        else:
            print(f"   ⚠️  Différence détectée : {abs(service_result - total_cost):,.2f} €")
            print("      (Vérifiez s'il y a des paiements avec des valeurs NULL)")
    except Exception as e:
        print(f"   ⚠️  Erreur lors de la vérification : {e}")
    
    print()
    print("=" * 80)
    
    db.close()

if __name__ == "__main__":
    explain_cout_financement(2023)
