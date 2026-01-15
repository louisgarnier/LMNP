"""
Script pour comparer les données BACKEND (Base de données) vs FRONTEND (Affiché dans l'app).

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import json
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
    first_transaction = db.query(Transaction).order_by(Transaction.date.asc()).first()
    current_year = date.today().year
    start_year = 2020
    
    if first_transaction and first_transaction.date:
        start_year = first_transaction.date.year
    
    years = []
    for year in range(start_year, current_year + 1):
        years.append(year)
    
    return years


def get_frontend_categories_to_display(mappings):
    """Détermine quelles catégories le frontend affiche."""
    PRODUITS_CATEGORIES = [
        'Loyers hors charge encaissés',
        'Charges locatives payées par locataires',
        'Autres revenus',
    ]
    
    CHARGES_CATEGORIES = [
        'Charges de copropriété hors fonds travaux',
        'Fluides non refacturés',
        'Assurances',
        'Honoraires',
        'Travaux et mobilier',
        'Impôts et taxes',
        'Charges d\'amortissements',
        'Autres charges diverses',
        'Coût du financement (hors remboursement du capital)',
    ]
    
    SPECIAL_CATEGORIES = [
        'Charges d\'amortissements',
        'Coût du financement (hors remboursement du capital)',
    ]
    
    # Créer un map des mappings
    categories_map = {}
    for mapping in mappings:
        has_level_1_values = False
        if mapping.level_1_values:
            try:
                level_1_values = json.loads(mapping.level_1_values) if isinstance(mapping.level_1_values, str) else mapping.level_1_values
                has_level_1_values = bool(level_1_values and len(level_1_values) > 0)
            except (json.JSONDecodeError, TypeError):
                pass
        
        categories_map[mapping.category_name] = {
            "hasLevel1Values": has_level_1_values,
            "type": mapping.type
        }
    
    categories_to_display = []
    
    # Produits prédéfinis
    for category in PRODUITS_CATEGORIES:
        mapping_info = categories_map.get(category)
        if mapping_info and (mapping_info["hasLevel1Values"] or category in SPECIAL_CATEGORIES):
            categories_to_display.append({
                "category": category,
                "type": "Produits d'exploitation"
            })
    
    # Charges prédéfinies
    for category in CHARGES_CATEGORIES:
        mapping_info = categories_map.get(category)
        if category in SPECIAL_CATEGORIES:
            categories_to_display.append({
                "category": category,
                "type": "Charges d'exploitation"
            })
        elif mapping_info and mapping_info["hasLevel1Values"]:
            categories_to_display.append({
                "category": category,
                "type": "Charges d'exploitation"
            })
    
    # Catégories personnalisées
    for mapping in mappings:
        if mapping.category_name not in PRODUITS_CATEGORIES and mapping.category_name not in CHARGES_CATEGORIES:
            mapping_info = categories_map.get(mapping.category_name)
            if mapping_info and (mapping_info["hasLevel1Values"] or mapping.category_name in SPECIAL_CATEGORIES):
                categories_to_display.append({
                    "category": mapping.category_name,
                    "type": mapping.type or "Charges d'exploitation"
                })
    
    return categories_to_display


def get_frontend_amount(category, year, category_type, result):
    """Simule getAmount() du frontend."""
    # Catégories spéciales
    if category == "Charges d'amortissements":
        amortissements = result.get("amortissements", 0) or 0
        return abs(amortissements) if amortissements else None
    
    if category == "Coût du financement (hors remboursement du capital)":
        cout = result.get("cout_financement", 0) or 0
        return abs(cout) if cout else None
    
    # Catégories normales
    if category_type == "Produits d'exploitation":
        produits = result.get("produits", {})
        amount = produits.get(category)
        return amount if amount is not None else None
    else:
        charges = result.get("charges", {})
        amount = charges.get(category)
        return abs(amount) if amount is not None and amount != 0 else None


def calculate_frontend_totals(result, frontend_categories, year):
    """Calcule les totaux comme le frontend."""
    produits_categories = [c for c in frontend_categories if c["type"] == "Produits d'exploitation"]
    charges_categories = [c for c in frontend_categories if c["type"] == "Charges d'exploitation"]
    
    CHARGES_INTERET = ['Coût du financement (hors remboursement du capital)']
    
    # Total produits
    total_produits = 0
    for cat_info in produits_categories:
        amount = get_frontend_amount(cat_info["category"], year, "Produits d'exploitation", result)
        if amount is not None:
            total_produits += amount
    
    # Total charges (exclut charges d'intérêt)
    total_charges = 0
    for cat_info in charges_categories:
        if cat_info["category"] in CHARGES_INTERET:
            continue
        amount = get_frontend_amount(cat_info["category"], year, "Charges d'exploitation", result)
        if amount is not None:
            total_charges += amount
    
    # Total charges d'intérêt
    total_charges_interet = 0
    for cat_info in charges_categories:
        if cat_info["category"] in CHARGES_INTERET:
            amount = get_frontend_amount(cat_info["category"], year, "Charges d'exploitation", result)
            if amount is not None:
                total_charges_interet += amount
    
    # Résultat d'exploitation
    resultat_exploitation = total_produits - total_charges
    
    # Résultat net
    resultat_net = resultat_exploitation - total_charges_interet
    
    return {
        "total_produits": total_produits if total_produits != 0 else None,
        "total_charges": total_charges if total_charges != 0 else None,
        "total_charges_interet": total_charges_interet if total_charges_interet != 0 else None,
        "resultat_exploitation": resultat_exploitation if resultat_exploitation != 0 else None,
        "resultat_net": resultat_net if resultat_net != 0 else None
    }


def compare_bdd_vs_frontend():
    """Compare BDD vs Frontend."""
    db = SessionLocal()
    
    try:
        # Récupérer les données
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        years = get_years_to_display(db)
        overrides = db.query(CompteResultatOverride).all()
        overrides_by_year = {o.year: o.override_value for o in overrides}
        
        # Déterminer les catégories affichées par le frontend
        frontend_categories = get_frontend_categories_to_display(mappings)
        
        print("=" * 120)
        print("COMPARAISON BDD (Backend) vs FRONTEND (Appli)")
        print("=" * 120)
        print()
        print(f"📊 Configuration:")
        print(f"   - Mappings en BDD: {len(mappings)}")
        print(f"   - Level 3 configurés: {len(level_3_values)} ({', '.join(level_3_values)})")
        print(f"   - Catégories affichées dans l'app: {len(frontend_categories)}")
        print(f"   - Overrides en BDD: {len(overrides)}")
        if overrides:
            print(f"   - Années avec override: {', '.join(map(str, sorted(overrides_by_year.keys())))}")
        print()
        
        for year in years:
            print(f"📅 ANNÉE {year}")
            print("-" * 120)
            
            # Calculer le compte de résultat (backend)
            result = calculate_compte_resultat(db, year, mappings, level_3_values)
            
            # Calculer les totaux frontend
            frontend_totals = calculate_frontend_totals(result, frontend_categories, year)
            
            # Backend valeurs
            total_produits_backend = result.get("total_produits", 0) or 0
            total_charges_exploitation_backend = result.get("total_charges_exploitation", 0) or 0
            resultat_exploitation_backend = result.get("resultat_exploitation", 0) or 0
            cout_financement_backend = result.get("cout_financement", 0) or 0
            resultat_net_backend = result.get("resultat_net", 0) or 0
            
            # Frontend valeurs
            total_produits_frontend = frontend_totals["total_produits"] or 0
            total_charges_frontend = frontend_totals["total_charges"] or 0
            total_charges_interet_frontend = frontend_totals["total_charges_interet"] or 0
            resultat_exploitation_frontend = frontend_totals["resultat_exploitation"] or 0
            resultat_net_frontend = frontend_totals["resultat_net"] or 0
            
            # Override
            override_value = overrides_by_year.get(year)
            checkbox_override = override_value is not None
            valeur_affichee = override_value if override_value is not None else resultat_net_frontend
            
            # Calculer le résultat cumulé (somme année après année)
            cumul_backend = 0
            cumul_frontend = 0
            for y in years:
                if y > year:
                    break
                # Backend : utiliser override si disponible, sinon calculé
                override_y = overrides_by_year.get(y)
                if override_y is not None:
                    cumul_backend += override_y
                else:
                    result_y = calculate_compte_resultat(db, y, mappings, level_3_values)
                    cumul_backend += result_y.get("resultat_net", 0) or 0
                
                # Frontend : utiliser override si disponible, sinon calculé
                frontend_totals_y = calculate_frontend_totals(
                    calculate_compte_resultat(db, y, mappings, level_3_values),
                    frontend_categories,
                    y
                )
                override_y_frontend = overrides_by_year.get(y)
                if override_y_frontend is not None:
                    cumul_frontend += override_y_frontend
                else:
                    cumul_frontend += frontend_totals_y["resultat_net"] or 0
            
            print(f"\n  🔵 BDD (Backend calculé):")
            print(f"     Total produits d'exploitation    : {total_produits_backend:>15,.2f} €")
            print(f"     Total charges d'exploitation     : {total_charges_exploitation_backend:>15,.2f} €")
            print(f"     Résultat d'exploitation          : {resultat_exploitation_backend:>15,.2f} €")
            print(f"     Charges d'intérêt                : {cout_financement_backend:>15,.2f} €")
            print(f"     Résultat de l'exercice (calculé): {resultat_net_backend:>15,.2f} €")
            print(f"     Résultat cumulé                  : {cumul_backend:>15,.2f} €")
            
            print(f"\n  🟢 FRONTEND (Affiché dans l'app):")
            print(f"     Total produits d'exploitation    : {total_produits_frontend:>15,.2f} €")
            print(f"     Total charges d'exploitation     : {total_charges_frontend:>15,.2f} €")
            print(f"     Résultat d'exploitation          : {resultat_exploitation_frontend:>15,.2f} €")
            print(f"     Charges d'intérêt                : {total_charges_interet_frontend:>15,.2f} €")
            print(f"     Résultat de l'exercice          : {resultat_net_frontend:>15,.2f} €")
            print(f"     Résultat cumulé                  : {cumul_frontend:>15,.2f} €")
            
            if checkbox_override:
                print(f"\n  🔘 OVERRIDE:")
                print(f"     Checkbox activée               : ✅ OUI")
                print(f"     Override en BDD                : {override_value:>15,.2f} €")
                print(f"     Valeur affichée (override)     : {valeur_affichee:>15,.2f} €")
            else:
                print(f"\n  🔘 OVERRIDE:")
                print(f"     Checkbox activée               : ❌ NON")
                print(f"     Override en BDD                : {'Aucun':>15}")
                print(f"     Valeur affichée (calculée)     : {valeur_affichee:>15,.2f} €")
            
            print(f"\n  ✅ VÉRIFICATION:")
            checks = []
            checks.append(("Produits", abs(total_produits_backend - total_produits_frontend) < 0.01))
            checks.append(("Charges exploitation", abs(total_charges_exploitation_backend - total_charges_frontend) < 0.01))
            checks.append(("Résultat exploitation", abs(resultat_exploitation_backend - resultat_exploitation_frontend) < 0.01))
            checks.append(("Charges intérêt", abs(cout_financement_backend - total_charges_interet_frontend) < 0.01))
            checks.append(("Résultat exercice", abs(resultat_net_backend - resultat_net_frontend) < 0.01))
            checks.append(("Résultat cumulé", abs(cumul_backend - cumul_frontend) < 0.01))
            
            all_ok = True
            for label, ok in checks:
                status = "✅" if ok else "❌"
                print(f"     {status} {label}")
                if not ok:
                    all_ok = False
            
            if all_ok:
                print(f"\n  ✅ TOUT EST COHÉRENT !")
            else:
                print(f"\n  ❌ INCOHÉRENCES DÉTECTÉES !")
            
            print()
            print("=" * 120)
            print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    compare_bdd_vs_frontend()
