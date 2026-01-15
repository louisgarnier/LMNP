"""
Script de debug pour comparer catégorie par catégorie backend vs frontend.

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
    """Récupère les années à afficher."""
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
    """Détermine quelles catégories le frontend devrait afficher."""
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
                    "type": mapping.type
                })
    
    return categories_to_display


def debug_categories():
    """Debug catégorie par catégorie."""
    db = SessionLocal()
    
    try:
        # Récupérer les données
        mappings = get_mappings(db)
        level_3_values = get_level_3_values(db)
        years = get_years_to_display(db)
        overrides = db.query(CompteResultatOverride).all()
        overrides_by_year = {o.year: o.override_value for o in overrides}
        
        print("=" * 120)
        print("DEBUG CATÉGORIE PAR CATÉGORIE : BACKEND vs FRONTEND")
        print("=" * 120)
        print()
        print(f"Mappings en BDD : {len(mappings)}")
        print(f"Level 3 values configurés : {len(level_3_values)}")
        print(f"Overrides en BDD : {len(overrides)}")
        print()
        
        # Déterminer les catégories que le frontend devrait afficher
        frontend_categories = get_frontend_categories_to_display(mappings)
        print(f"Catégories que le frontend devrait afficher : {len(frontend_categories)}")
        for cat in frontend_categories:
            print(f"  - {cat['category']} ({cat['type']})")
        print()
        
        for year in years:
            print(f"📅 ANNÉE {year}:")
            print("-" * 120)
            
            # Calculer le compte de résultat (backend)
            result = calculate_compte_resultat(db, year, mappings, level_3_values)
            
            backend_produits = result.get("produits", {})
            backend_charges = result.get("charges", {})
            backend_amortissements = result.get("amortissements", 0) or 0
            backend_cout_financement = result.get("cout_financement", 0) or 0
            
            print(f"\n  🔵 BACKEND CALCULÉ:")
            print(f"     Produits ({len(backend_produits)} catégories):")
            for cat_name, amount in sorted(backend_produits.items()):
                print(f"       - {cat_name}: {amount:>15,.2f} €")
            
            print(f"\n     Charges ({len(backend_charges)} catégories):")
            for cat_name, amount in sorted(backend_charges.items()):
                print(f"       - {cat_name}: {amount:>15,.2f} €")
            
            if backend_amortissements != 0:
                print(f"\n     Amortissements: {backend_amortissements:>15,.2f} €")
            if backend_cout_financement != 0:
                print(f"     Coût financement: {backend_cout_financement:>15,.2f} €")
            
            print(f"\n  🟢 FRONTEND DEVRAIT AFFICHER:")
            frontend_produits = []
            frontend_charges = []
            
            for cat_info in frontend_categories:
                cat_name = cat_info["category"]
                cat_type = cat_info["type"]
                
                if cat_type == "Produits d'exploitation":
                    amount = backend_produits.get(cat_name)
                    if amount is not None:
                        frontend_produits.append((cat_name, amount))
                    else:
                        print(f"       ⚠️  {cat_name}: PAS DE DONNÉE EN BACKEND")
                else:
                    if cat_name == "Charges d'amortissements":
                        amount = backend_amortissements
                    elif cat_name == "Coût du financement (hors remboursement du capital)":
                        amount = backend_cout_financement
                    else:
                        amount = backend_charges.get(cat_name)
                    
                    if amount is not None and amount != 0:
                        frontend_charges.append((cat_name, abs(amount)))
                    else:
                        print(f"       ⚠️  {cat_name}: PAS DE DONNÉE EN BACKEND")
            
            print(f"     Produits ({len(frontend_produits)} catégories):")
            for cat_name, amount in sorted(frontend_produits):
                print(f"       - {cat_name}: {amount:>15,.2f} €")
            
            print(f"\n     Charges ({len(frontend_charges)} catégories):")
            for cat_name, amount in sorted(frontend_charges):
                print(f"       - {cat_name}: {amount:>15,.2f} €")
            
            # Calculer les totaux
            total_produits_backend = sum(backend_produits.values())
            total_charges_backend = sum(backend_charges.values())
            
            total_produits_frontend = sum(amount for _, amount in frontend_produits)
            total_charges_frontend = sum(amount for _, amount in frontend_charges)
            
            # Exclure les charges d'intérêt du total des charges (frontend)
            charges_interet_frontend = backend_cout_financement if backend_cout_financement != 0 else 0
            total_charges_exploitation_frontend = total_charges_frontend - abs(charges_interet_frontend)
            
            resultat_exploitation_backend = total_produits_backend - total_charges_backend
            resultat_exploitation_frontend = total_produits_frontend - total_charges_exploitation_frontend
            
            resultat_net_backend = resultat_exploitation_backend - backend_cout_financement
            resultat_net_frontend = resultat_exploitation_frontend - abs(charges_interet_frontend)
            
            print(f"\n  📊 TOTAUX:")
            print(f"     Backend Total produits  : {total_produits_backend:>15,.2f} €")
            print(f"     Frontend Total produits  : {total_produits_frontend:>15,.2f} €")
            print(f"     {'✅' if abs(total_produits_backend - total_produits_frontend) < 0.01 else '❌'} Différence: {abs(total_produits_backend - total_produits_frontend):,.2f} €")
            
            print(f"\n     Backend Total charges  : {abs(total_charges_backend):>15,.2f} €")
            print(f"     Frontend Total charges  : {total_charges_exploitation_frontend:>15,.2f} €")
            print(f"     {'✅' if abs(abs(total_charges_backend) - total_charges_exploitation_frontend) < 0.01 else '❌'} Différence: {abs(abs(total_charges_backend) - total_charges_exploitation_frontend):,.2f} €")
            
            print(f"\n     Backend Résultat exploitation  : {resultat_exploitation_backend:>15,.2f} €")
            print(f"     Frontend Résultat exploitation  : {resultat_exploitation_frontend:>15,.2f} €")
            print(f"     {'✅' if abs(resultat_exploitation_backend - resultat_exploitation_frontend) < 0.01 else '❌'} Différence: {abs(resultat_exploitation_backend - resultat_exploitation_frontend):,.2f} €")
            
            print(f"\n     Backend Résultat exercice  : {resultat_net_backend:>15,.2f} €")
            print(f"     Frontend Résultat exercice  : {resultat_net_frontend:>15,.2f} €")
            print(f"     {'✅' if abs(resultat_net_backend - resultat_net_frontend) < 0.01 else '❌'} Différence: {abs(resultat_net_backend - resultat_net_frontend):,.2f} €")
            
            override_value = overrides_by_year.get(year)
            if override_value is not None:
                print(f"\n     Override en BDD : {override_value:>15,.2f} €")
            
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
    debug_categories()
