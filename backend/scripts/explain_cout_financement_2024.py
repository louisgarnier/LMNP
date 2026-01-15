"""
Script pour expliquer en détail le calcul du coût du financement pour 2024.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import LoanPayment, LoanConfig
from backend.api.services.compte_resultat_service import get_cout_financement, calculate_compte_resultat
from sqlalchemy import and_

init_database()
db = SessionLocal()

year = 2024

print("=" * 80)
print(f"📊 EXPLICATION DÉTAILLÉE DU CALCUL DU COÛT DU FINANCEMENT POUR {year}")
print("=" * 80)
print()

# 1. Récupérer les loan_payments pour 2024
start_date = date(year, 1, 1)
end_date = date(year, 12, 31)

print("1️⃣ PAIEMENTS (LOAN_PAYMENTS) POUR L'ANNÉE 2024")
print("-" * 80)
payments = db.query(LoanPayment).filter(
    and_(
        LoanPayment.date >= start_date,
        LoanPayment.date <= end_date
    )
).order_by(LoanPayment.date).all()

if not payments:
    print("   ⚠️  Aucun paiement trouvé pour 2024.")
    db.close()
    exit(0)

print(f"   Nombre de paiements trouvés : {len(payments)}")
print()
print(f"{'Date':<12} {'Nom crédit':<30} {'Intérêts':<15} {'Assurance':<15} {'Total (I+A)':<15}")
print("-" * 80)

total_interest = 0.0
total_insurance = 0.0

for payment in payments:
    interest = payment.interest or 0.0
    insurance = payment.insurance or 0.0
    payment_total = interest + insurance
    
    total_interest += interest
    total_insurance += insurance
    
    loan_name = payment.loan_name or 'N/A'
    if len(loan_name) > 28:
        loan_name = loan_name[:25] + '...'
    
    print(f"{payment.date.strftime('%d/%m/%Y'):<12} "
          f"{loan_name:<30} "
          f"{interest:>12,.2f} € "
          f"{insurance:>12,.2f} € "
          f"{payment_total:>12,.2f} €")

print("-" * 80)
print(f"{'TOTAL':<12} {'':<30} "
      f"{total_interest:>12,.2f} € "
      f"{total_insurance:>12,.2f} € "
      f"{total_interest + total_insurance:>12,.2f} €")
print()

# 2. Vérifier le calcul du backend
print("2️⃣ CALCUL DU BACKEND")
print("-" * 80)
cout_backend = get_cout_financement(db, year)
print(f"   get_cout_financement({year}) = {cout_backend:,.2f} €")
print()
print(f"   Formule : Σ (interest + insurance) pour tous les paiements de {year}")
print(f"   = {total_interest:,.2f} € (intérêts) + {total_insurance:,.2f} € (assurance)")
print(f"   = {total_interest + total_insurance:,.2f} €")
print()

if abs(cout_backend - (total_interest + total_insurance)) < 0.01:
    print("   ✅ Le calcul est correct !")
else:
    print(f"   ⚠️  Différence détectée : {abs(cout_backend - (total_interest + total_insurance)):,.2f} €")
print()

# 3. Vérifier via calculate_compte_resultat
print("3️⃣ VIA calculate_compte_resultat")
print("-" * 80)
result = calculate_compte_resultat(db, year)
cout_calcule = result['cout_financement']
print(f"   calculate_compte_resultat({year})['cout_financement'] = {cout_calcule:,.2f} €")
print()

# 4. Ce que le frontend reçoit
print("4️⃣ CE QUE LE FRONTEND REÇOIT")
print("-" * 80)
print(f"   L'API retourne : cout_financement = {cout_calcule:,.2f} €")
print(f"   (Valeur exacte : {cout_calcule})")
print()

# 5. Ce que getAmount() retourne
print("5️⃣ CE QUE getAmount() RETOURNE DANS LE FRONTEND")
print("-" * 80)
print(f"   Code frontend :")
print(f"   ```typescript")
print(f"   const cout = yearData.cout_financement;")
print(f"   return Math.abs(cout);")
print(f"   ```")
print()
print(f"   Pour {year} :")
print(f"   - yearData.cout_financement = {cout_calcule}")
print(f"   - Math.abs({cout_calcule}) = {abs(cout_calcule):,.2f} €")
print(f"   - getAmount() retourne donc : {abs(cout_calcule):,.2f} €")
print()

# 6. Ce que formatAmount() affiche
print("6️⃣ CE QUE formatAmount() AFFICHE")
print("-" * 80)
print(f"   Code frontend :")
print(f"   ```typescript")
print(f"   new Intl.NumberFormat('fr-FR', {{")
print(f"     style: 'currency',")
print(f"     currency: 'EUR',")
print(f"     minimumFractionDigits: 0,")
print(f"     maximumFractionDigits: 0,")
print(f"   }}).format(amount);")
print(f"   ```")
print()
print(f"   Pour {year} :")
print(f"   - amount = {abs(cout_calcule):,.2f} €")
print(f"   - Intl.NumberFormat arrondit à l'entier le plus proche")
print(f"   - {abs(cout_calcule):,.2f} € → arrondi à {round(abs(cout_calcule))} €")
print(f"   - Affichage final : {round(abs(cout_calcule)):,} € (avec séparateurs)")
print()

# 7. Résumé
print("7️⃣ RÉSUMÉ")
print("-" * 80)
print(f"   Backend calcule : {cout_calcule:,.2f} €")
print(f"   Frontend reçoit : {cout_calcule:,.2f} €")
print(f"   getAmount() retourne : {abs(cout_calcule):,.2f} €")
print(f"   formatAmount() affiche : {round(abs(cout_calcule)):,} €")
print()
print(f"   ⚠️  DIFFÉRENCE : {abs(cout_calcule):,.2f} € (backend) vs {round(abs(cout_calcule)):,} € (frontend)")
print(f"   La différence vient de l'arrondi JavaScript qui arrondit {abs(cout_calcule):,.2f} à {round(abs(cout_calcule))}")
print()

print("=" * 80)

db.close()
