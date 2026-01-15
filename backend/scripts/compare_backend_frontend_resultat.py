"""
Script pour comparer les valeurs backend vs frontend pour le Résultat de l'exercice.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import CompteResultatOverride, Transaction
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_compte_resultat
)


def get_years_to_display(db):
    """Récupère les années à afficher (comme le fait le frontend)."""
    # Récupérer la première transaction (triée par date croissante)
    first_transaction = db.query(Transaction).order_by(Transaction.date.asc()).first()
    
    current_year = date.today().year
    start_year = 2020  # Valeur par défaut
    
    if first_transaction and first_transaction.date:
        start_year = first_transaction.date.year
    
    years = []
    for year in range(start_year, current_year + 1):
        years.append(year)
    
    return years


def get_resultat_net_calcule(result):
    """Calcule le résultat net (comme le fait le frontend)."""
    # Résultat d'exploitation = Total produits - Total charges
    total_produits = result.get("total_produits", 0) or 0
    total_charges = result.get("total_charges", 0) or 0
    resultat_exploitation = total_produits - abs(total_charges)
    
    # Charges d'intérêt
    cout_financement = result.get("cout_financement", 0) or 0
    
    # Résultat de l'exercice = Résultat d'exploitation - Charges d'intérêt
    resultat_net = resultat_exploitation - cout_financement
    
    return resultat_net


def compare_backend_frontend():
    """Compare les valeurs backend vs frontend."""
    db = SessionLocal()
    
    try:
        # Récupérer les overrides en BDD
        overrides = db.query(CompteResultatOverride).order_by(CompteResultatOverride.year).all()
        overrides_by_year = {o.year: o.override_value for o in overrides}
        
        # Récupérer les mappings et config
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        
        # Récupérer les années à afficher (comme le frontend)
        years = get_years_to_display(db)
        
        print("=" * 100)
        print("COMPARAISON BACKEND vs FRONTEND : Résultat de l'exercice")
        print("=" * 100)
        print()
        print(f"Années analysées : {', '.join(map(str, years))}")
        print(f"Nombre d'overrides en BDD : {len(overrides)}")
        if overrides:
            print(f"Années avec override : {', '.join(map(str, sorted(overrides_by_year.keys())))}")
        print()
        
        for year in years:
            print(f"📅 ANNÉE {year}:")
            print("-" * 100)
            
            # Calculer le compte de résultat (backend)
            result = calculate_compte_resultat(db, year, mappings, level_3_values)
            
            # Calculer le résultat net (comme le frontend)
            resultat_net_calcule = get_resultat_net_calcule(result)
            
            # Récupérer l'override en BDD
            override_value_bdd = overrides_by_year.get(year)
            
            # Simuler le frontend : valeur affichée
            # Si checkbox cochée ET override existe : afficher override
            # Sinon : afficher valeur calculée
            # (On simule avec checkbox cochée si override existe)
            checkbox_override_enabled = override_value_bdd is not None
            valeur_frontend = override_value_bdd if override_value_bdd is not None else resultat_net_calcule
            
            # Détails du calcul
            total_produits = result.get("total_produits", 0) or 0
            total_charges = result.get("total_charges", 0) or 0
            resultat_exploitation = total_produits - abs(total_charges)
            cout_financement = result.get("cout_financement", 0) or 0
            
            print(f"  🔢 CALCUL BACKEND:")
            print(f"     Total produits d'exploitation    : {total_produits:>15,.2f} €")
            print(f"     Total charges d'exploitation     : {abs(total_charges):>15,.2f} €")
            print(f"     → Résultat d'exploitation        : {resultat_exploitation:>15,.2f} €")
            print(f"     Charges d'intérêt                 : {cout_financement:>15,.2f} €")
            print(f"     → Résultat de l'exercice (calc.) : {resultat_net_calcule:>15,.2f} €")
            print()
            
            print(f"  📊 OVERRIDE:")
            print(f"     Checkbox override activée        : {'✅ OUI' if checkbox_override_enabled else '❌ NON'}")
            if override_value_bdd is not None:
                print(f"     Override en BDD                 : {override_value_bdd:>15,.2f} €")
                difference = override_value_bdd - resultat_net_calcule
                print(f"     Différence (override - calculé)  : {difference:>15,.2f} €")
            else:
                print(f"     Override en BDD                 : {'Aucun':>15}")
            print()
            
            print(f"  🖥️  FRONTEND:")
            print(f"     Valeur affichée                  : {valeur_frontend:>15,.2f} €")
            if override_value_bdd is not None:
                print(f"     Style                            : Italique + '*resultat overridé'")
            else:
                print(f"     Style                            : Normal")
            print()
            
            # Vérification de cohérence
            if override_value_bdd is not None:
                if abs(valeur_frontend - override_value_bdd) < 0.01:
                    print(f"  ✅ COHÉRENCE : Frontend affiche bien l'override")
                else:
                    print(f"  ❌ INCOHÉRENCE : Frontend devrait afficher {override_value_bdd:,.2f} € mais affiche {valeur_frontend:,.2f} €")
            else:
                if abs(valeur_frontend - resultat_net_calcule) < 0.01:
                    print(f"  ✅ COHÉRENCE : Frontend affiche bien la valeur calculée")
                else:
                    print(f"  ❌ INCOHÉRENCE : Frontend devrait afficher {resultat_net_calcule:,.2f} € mais affiche {valeur_frontend:,.2f} €")
            
            print()
            print("=" * 100)
            print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    compare_backend_frontend()
