"""
Script pour comparer les valeurs calculées, overrides en BDD, et affichage frontend.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import CompteResultatOverride
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_compte_resultat
)


def compare_resultat_override():
    """Compare les valeurs calculées, overrides en BDD, et affichage frontend."""
    db = SessionLocal()
    
    try:
        # Récupérer tous les overrides en BDD
        overrides = db.query(CompteResultatOverride).order_by(CompteResultatOverride.year).all()
        
        print("=" * 80)
        print("COMPARAISON : Valeurs calculées vs Overrides en BDD")
        print("=" * 80)
        print()
        
        if not overrides:
            print("ℹ️  Aucun override en base de données")
            print()
        
        # Récupérer les mappings et config
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        
        # Récupérer les années depuis les transactions (comme le fait le frontend)
        from backend.database.models import Transaction
        
        # Récupérer la première transaction (triée par date croissante)
        first_transaction = db.query(Transaction).order_by(Transaction.date.asc()).first()
        
        current_year = date.today().year
        start_year = 2020  # Valeur par défaut
        
        if first_transaction and first_transaction.date:
            start_year = first_transaction.date.year
        
        # Années à comparer (années avec overrides + années depuis la première transaction jusqu'à aujourd'hui)
        years_to_check = set()
        for override in overrides:
            years_to_check.add(override.year)
        
        # Ajouter les années depuis la première transaction jusqu'à aujourd'hui
        for year in range(start_year, current_year + 1):
            years_to_check.add(year)
        
        years_to_check = sorted(years_to_check)
        
        print(f"Années à comparer : {', '.join(map(str, years_to_check))}")
        print()
        
        for year in years_to_check:
            print(f"📅 Année {year}:")
            print("-" * 80)
            
            # Calculer le résultat de l'exercice
            result = calculate_compte_resultat(db, year, mappings, level_3_values)
            resultat_net_calcule = result.get("resultat_net", 0)
            
            # Récupérer l'override en BDD
            override = db.query(CompteResultatOverride).filter(
                CompteResultatOverride.year == year
            ).first()
            
            override_value_bdd = override.override_value if override else None
            
            # Valeur affichée en frontend (override si existe, sinon calculée)
            valeur_frontend = override_value_bdd if override_value_bdd is not None else resultat_net_calcule
            
            print(f"  Calculé (backend)     : {resultat_net_calcule:,.2f} €" if resultat_net_calcule is not None else f"  Calculé (backend)     : null")
            print(f"  Override (BDD)        : {override_value_bdd:,.2f} €" if override_value_bdd is not None else "  Override (BDD)        : null")
            print(f"  Affiché (frontend)    : {valeur_frontend:,.2f} €" if valeur_frontend is not None else "  Affiché (frontend)    : null")
            
            if override_value_bdd is not None:
                difference = override_value_bdd - (resultat_net_calcule or 0)
                print(f"  Différence            : {difference:+,.2f} €")
                print(f"  ✅ Override actif (affiché en italique avec '*resultat overridé')")
            else:
                print(f"  ℹ️  Pas d'override (valeur calculée affichée)")
            
            print()
        
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print(f"Nombre d'overrides en BDD : {len(overrides)}")
        print(f"Années avec override      : {', '.join(map(str, [o.year for o in overrides])) if overrides else 'Aucune'}")
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    compare_resultat_override()
