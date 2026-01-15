"""
Script pour comparer en détail backend vs frontend pour chaque ligne du compte de résultat.

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
    first_transaction = db.query(Transaction).order_by(Transaction.date.asc()).first()
    current_year = date.today().year
    start_year = 2020  # Valeur par défaut
    
    if first_transaction and first_transaction.date:
        start_year = first_transaction.date.year
    
    years = []
    for year in range(start_year, current_year + 1):
        years.append(year)
    
    return years


def simulate_frontend_get_amount(category, year, category_type, result):
    """Simule getAmount() du frontend pour une catégorie."""
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


def simulate_frontend_calculations(result, overrides_by_year, year, mappings):
    """Simule les calculs du frontend pour une année."""
    import json
    
    # Catégories prédéfinies (comme dans le frontend)
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
    
    CHARGES_INTERET = [
        'Coût du financement (hors remboursement du capital)',
    ]
    
    # Créer un map des mappings par catégorie
    mappings_by_category = {m.category_name: m for m in mappings}
    
    # Déterminer quelles catégories sont affichées (comme le frontend)
    categories_to_display = []
    
    # 1. Catégories spéciales (toujours affichées)
    for category in SPECIAL_CATEGORIES:
        if category in CHARGES_CATEGORIES:
            categories_to_display.append({
                "category": category,
                "type": "Charges d'exploitation"
            })
    
    # 2. Catégories prédéfinies avec mappings actifs
    for category in PRODUITS_CATEGORIES:
        mapping = mappings_by_category.get(category)
        if mapping and mapping.level_1_values:
            try:
                level_1_values = json.loads(mapping.level_1_values) if isinstance(mapping.level_1_values, str) else mapping.level_1_values
                if level_1_values and len(level_1_values) > 0:
                    categories_to_display.append({
                        "category": category,
                        "type": "Produits d'exploitation"
                    })
            except (json.JSONDecodeError, TypeError):
                pass
    
    for category in CHARGES_CATEGORIES:
        if category in SPECIAL_CATEGORIES:
            continue  # Déjà ajouté
        mapping = mappings_by_category.get(category)
        if mapping and mapping.level_1_values:
            try:
                level_1_values = json.loads(mapping.level_1_values) if isinstance(mapping.level_1_values, str) else mapping.level_1_values
                if level_1_values and len(level_1_values) > 0:
                    categories_to_display.append({
                        "category": category,
                        "type": "Charges d'exploitation"
                    })
            except (json.JSONDecodeError, TypeError):
                pass
    
    # 3. Catégories personnalisées (toujours affichées si elles ont un mapping)
    for mapping in mappings:
        if mapping.category_name not in PRODUITS_CATEGORIES and mapping.category_name not in CHARGES_CATEGORIES:
            categories_to_display.append({
                "category": mapping.category_name,
                "type": mapping.type
            })
    
    # Filtrer par type
    produits_categories = [c for c in categories_to_display if c["type"] == "Produits d'exploitation"]
    charges_categories = [c for c in categories_to_display if c["type"] == "Charges d'exploitation"]
    
    # Frontend : getTotalProduits
    total_produits_frontend = 0
    for cat_info in produits_categories:
        amount = simulate_frontend_get_amount(cat_info["category"], year, "Produits d'exploitation", result)
        if amount is not None:
            total_produits_frontend += amount
    
    # Frontend : getTotalCharges (exclut les charges d'intérêt)
    total_charges_frontend = 0
    for cat_info in charges_categories:
        if cat_info["category"] in CHARGES_INTERET:
            continue  # Exclure les charges d'intérêt
        amount = simulate_frontend_get_amount(cat_info["category"], year, "Charges d'exploitation", result)
        if amount is not None:
            total_charges_frontend += amount
    
    # Frontend : getTotalChargesInteret
    total_charges_interet_frontend = 0
    for cat_info in charges_categories:
        if cat_info["category"] in CHARGES_INTERET:
            amount = simulate_frontend_get_amount(cat_info["category"], year, "Charges d'exploitation", result)
            if amount is not None:
                total_charges_interet_frontend += amount
    
    # Frontend : getResultatExploitation
    resultat_exploitation_frontend = total_produits_frontend - total_charges_frontend
    
    # Frontend : getResultatNet
    resultat_net_frontend = resultat_exploitation_frontend - total_charges_interet_frontend
    
    # Override
    override_value = overrides_by_year.get(year)
    
    return {
        "total_produits": total_produits_frontend if total_produits_frontend != 0 else None,
        "total_charges": total_charges_frontend if total_charges_frontend != 0 else None,
        "resultat_exploitation": resultat_exploitation_frontend if resultat_exploitation_frontend != 0 else None,
        "total_charges_interet": total_charges_interet_frontend if total_charges_interet_frontend != 0 else None,
        "resultat_net": resultat_net_frontend if resultat_net_frontend != 0 else None,
        "override_value": override_value
    }


def compare_detailed():
    """Compare en détail backend vs frontend."""
    db = SessionLocal()
    
    try:
        # Récupérer les overrides en BDD
        overrides = db.query(CompteResultatOverride).order_by(CompteResultatOverride.year).all()
        overrides_by_year = {o.year: o.override_value for o in overrides}
        
        # Récupérer les mappings et config
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        
        # Récupérer les années à afficher
        years = get_years_to_display(db)
        
        print("=" * 120)
        print("COMPARAISON DÉTAILLÉE BACKEND vs FRONTEND")
        print("=" * 120)
        print()
        print(f"Années analysées : {', '.join(map(str, years))}")
        print(f"Nombre d'overrides en BDD : {len(overrides)}")
        if overrides:
            print(f"Années avec override : {', '.join(map(str, sorted(overrides_by_year.keys())))}")
        print()
        
        for year in years:
            print(f"📅 ANNÉE {year}:")
            print("-" * 120)
            
            # Calculer le compte de résultat (backend)
            result = calculate_compte_resultat(db, year, mappings, level_3_values)
            
            # Simuler les calculs frontend
            frontend = simulate_frontend_calculations(result, overrides_by_year, year, mappings)
            
            # Backend valeurs
            total_produits_backend = result.get("total_produits", 0) or 0
            total_charges_backend = result.get("total_charges", 0) or 0
            resultat_exploitation_backend = result.get("resultat_exploitation", 0) or 0
            cout_financement_backend = result.get("cout_financement", 0) or 0
            resultat_net_backend = result.get("resultat_net", 0) or 0
            
            # Frontend valeurs (convertir None en 0 pour comparaison)
            total_produits_frontend = frontend["total_produits"] or 0
            total_charges_frontend = frontend["total_charges"] or 0
            resultat_exploitation_frontend = frontend["resultat_exploitation"] or 0
            total_charges_interet_frontend = frontend["total_charges_interet"] or 0
            resultat_net_frontend = frontend["resultat_net"] or 0
            override_value = frontend["override_value"]
            
            # État de la checkbox (simulé : true si override existe)
            checkbox_override_ticked = override_value is not None
            
            # Valeur affichée en frontend (override si existe, sinon calculée)
            valeur_affichee_frontend = override_value if override_value is not None else resultat_net_frontend
            
            print(f"  📊 TOTAL DES PRODUITS D'EXPLOITATION:")
            print(f"     Backend  : {total_produits_backend:>15,.2f} €")
            print(f"     Frontend : {total_produits_frontend:>15,.2f} €")
            if abs(total_produits_backend - total_produits_frontend) < 0.01:
                print(f"     ✅ COHÉRENT")
            else:
                print(f"     ❌ DIFFÉRENCE : {abs(total_produits_backend - total_produits_frontend):,.2f} €")
            print()
            
            print(f"  📉 TOTAL DES CHARGES D'EXPLOITATION:")
            print(f"     Backend  : {abs(total_charges_backend):>15,.2f} €")
            print(f"     Frontend : {total_charges_frontend:>15,.2f} €")
            if abs(abs(total_charges_backend) - total_charges_frontend) < 0.01:
                print(f"     ✅ COHÉRENT")
            else:
                print(f"     ❌ DIFFÉRENCE : {abs(abs(total_charges_backend) - total_charges_frontend):,.2f} €")
            print()
            
            print(f"  💰 RÉSULTAT D'EXPLOITATION:")
            print(f"     Backend  : {resultat_exploitation_backend:>15,.2f} €")
            print(f"     Frontend : {resultat_exploitation_frontend:>15,.2f} €")
            if abs(resultat_exploitation_backend - resultat_exploitation_frontend) < 0.01:
                print(f"     ✅ COHÉRENT")
            else:
                print(f"     ❌ DIFFÉRENCE : {abs(resultat_exploitation_backend - resultat_exploitation_frontend):,.2f} €")
            print()
            
            print(f"  🎯 RÉSULTAT DE L'EXERCICE:")
            print(f"     Backend  : {resultat_net_backend:>15,.2f} €")
            print(f"     Frontend : {resultat_net_frontend:>15,.2f} €")
            if abs(resultat_net_backend - resultat_net_frontend) < 0.01:
                print(f"     ✅ COHÉRENT")
            else:
                print(f"     ❌ DIFFÉRENCE : {abs(resultat_net_backend - resultat_net_frontend):,.2f} €")
            print()
            
            print(f"  🔘 OVERRIDE RESULTAT:")
            print(f"     Checkbox ticked : {'✅ OUI' if checkbox_override_ticked else '❌ NON'}")
            if override_value is not None:
                print(f"     Résultat exercice (Override) : {override_value:>15,.2f} €")
                print(f"     Valeur affichée frontend      : {valeur_affichee_frontend:>15,.2f} €")
                print(f"     Différence (override - calc.)  : {(override_value - resultat_net_frontend):>15,.2f} €")
            else:
                print(f"     Résultat exercice (Override) : {'Aucun':>15}")
                print(f"     Valeur affichée frontend      : {valeur_affichee_frontend:>15,.2f} €")
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
    compare_detailed()
