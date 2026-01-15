"""
Script pour déboguer la différence entre le backend et le frontend pour le coût du financement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.api.services.compte_resultat_service import calculate_compte_resultat, get_cout_financement

init_database()
db = SessionLocal()

year = 2023

print("=" * 80)
print(f"🔍 DÉBOGAGE COÛT DU FINANCEMENT - ANNÉE {year}")
print("=" * 80)
print()

# 1. Valeur directe du service
cout_direct = get_cout_financement(db, year)
print(f"1️⃣ get_cout_financement({year}): {cout_direct:,.2f} €")
print()

# 2. Valeur depuis calculate_compte_resultat
result = calculate_compte_resultat(db, year)
cout_calcule = result["cout_financement"]
print(f"2️⃣ calculate_compte_resultat({year})['cout_financement']: {cout_calcule:,.2f} €")
print()

# 3. Vérifier si c'est dans les charges
if "Coût du financement (hors remboursement du capital)" in result["charges"]:
    cout_charges = result["charges"]["Coût du financement (hors remboursement du capital)"]
    print(f"3️⃣ Dans result['charges']: {cout_charges:,.2f} €")
    print(f"   Différence avec cout_financement: {abs(cout_calcule - cout_charges):,.2f} €")
    print()

# 4. Vérifier le total_charges
total_charges = result["total_charges"]
print(f"4️⃣ total_charges: {total_charges:,.2f} €")
print()

# 5. Calculer manuellement le total des charges
charges_sum = sum(result["charges"].values())
print(f"5️⃣ Somme manuelle des charges: {charges_sum:,.2f} €")
print(f"   Différence avec total_charges: {abs(total_charges - charges_sum):,.2f} €")
print()

# 6. Détail des charges
print("6️⃣ DÉTAIL DES CHARGES:")
for cat, amount in sorted(result["charges"].items()):
    print(f"   {cat}: {amount:,.2f} €")
print()

# 7. Vérifier si le coût du financement est compté deux fois
cout_in_charges = result["charges"].get("Coût du financement (hors remboursement du capital)", 0)
cout_direct_abs = abs(cout_direct)
cout_in_charges_abs = abs(cout_in_charges)

print("7️⃣ VÉRIFICATION DOUBLE COMPTAGE:")
print(f"   cout_financement direct: {cout_direct:,.2f} € (abs: {cout_direct_abs:,.2f} €)")
print(f"   cout_financement dans charges: {cout_in_charges:,.2f} € (abs: {cout_in_charges_abs:,.2f} €)")
if abs(cout_direct_abs - cout_in_charges_abs) > 0.01:
    print(f"   ⚠️  DIFFÉRENCE DÉTECTÉE: {abs(cout_direct_abs - cout_in_charges_abs):,.2f} €")
else:
    print("   ✅ Les valeurs correspondent")
print()

# 8. Calculer ce que le frontend devrait voir
print("8️⃣ CE QUE LE FRONTEND DEVRAIT VOIR:")
print(f"   yearData.cout_financement: {cout_calcule:,.2f} €")
print(f"   Math.abs(yearData.cout_financement): {abs(cout_calcule):,.2f} €")
print()

# 9. Si l'utilisateur voit 3,127 €, calculer la différence
frontend_value = 3127.00
print(f"9️⃣ SI LE FRONTEND AFFICHE {frontend_value:,.2f} €:")
print(f"   Différence avec backend: {frontend_value - abs(cout_calcule):,.2f} €")
print(f"   Ratio: {frontend_value / abs(cout_calcule):.4f}")
print()

print("=" * 80)

db.close()
