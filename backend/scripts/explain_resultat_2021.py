"""
Script pour expliquer le calcul du "Résultat de l'exercice" pour 2021.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_compte_resultat
)


def explain_resultat_2021():
    """Explique le calcul du résultat de l'exercice pour 2021."""
    db = SessionLocal()
    
    try:
        # Récupérer les mappings et config
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        
        # Calculer le compte de résultat pour 2021
        result = calculate_compte_resultat(db, 2021, mappings, level_3_values)
        
        print("=" * 80)
        print("EXPLICATION DU CALCUL : Résultat de l'exercice pour 2021")
        print("=" * 80)
        print()
        
        print("📊 PRODUITS D'EXPLOITATION:")
        print("-" * 80)
        total_produits = result.get("total_produits", 0) or 0
        produits = result.get("produits", {})
        for category, amount in sorted(produits.items()):
            if amount and amount != 0:
                print(f"  {category:50} : {amount:>12,.2f} €")
        total_produits_label = "Total des produits d'exploitation"
        print(f"  {total_produits_label:50} : {total_produits:>12,.2f} €")
        print()
        
        print("📉 CHARGES D'EXPLOITATION:")
        print("-" * 80)
        total_charges = result.get("total_charges", 0) or 0
        charges = result.get("charges", {})
        for category, amount in sorted(charges.items()):
            if amount and amount != 0:
                # Les charges sont stockées en négatif, afficher en valeur absolue
                print(f"  {category:50} : {abs(amount):>12,.2f} €")
        total_charges_label = "Total des charges d'exploitation"
        print(f"  {total_charges_label:50} : {abs(total_charges):>12,.2f} €")
        print()
        
        print("💰 RÉSULTAT D'EXPLOITATION:")
        print("-" * 80)
        resultat_exploitation = result.get("resultat_exploitation", 0) or 0
        print(f"  Résultat d'exploitation = Total produits - Total charges")
        print(f"  Résultat d'exploitation = {total_produits:,.2f} € - {abs(total_charges):,.2f} €")
        print(f"  Résultat d'exploitation = {resultat_exploitation:,.2f} €")
        print()
        
        print("💸 CHARGES D'INTÉRÊT:")
        print("-" * 80)
        cout_financement = result.get("cout_financement", 0) or 0
        print(f"  Coût du financement (hors remboursement du capital) : {cout_financement:,.2f} €")
        print()
        
        print("🎯 RÉSULTAT DE L'EXERCICE:")
        print("-" * 80)
        resultat_net = result.get("resultat_net", 0) or 0
        print(f"  Résultat de l'exercice = Résultat d'exploitation - Charges d'intérêt")
        print(f"  Résultat de l'exercice = {resultat_exploitation:,.2f} € - {cout_financement:,.2f} €")
        print(f"  Résultat de l'exercice = {resultat_net:,.2f} €")
        print()
        
        print("=" * 80)
        print("✅ VALEUR CALCULÉE (backend) : {:.2f} €".format(resultat_net))
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    explain_resultat_2021()
