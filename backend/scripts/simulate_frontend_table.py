"""
Script pour simuler exactement ce que le frontend affiche dans CompteResultatTable.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script reproduit exactement la logique du frontend pour afficher le tableau.
"""

import sys
from pathlib import Path
from datetime import date
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.api.services.compte_resultat_service import calculate_compte_resultat, get_mappings
from backend.database.models import CompteResultatMapping

init_database()
db = SessionLocal()

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

def formatAmount(amount):
    """Formate un montant comme le frontend (sans décimales)"""
    if amount is None:
        return '-'
    return f"{amount:,.0f} €".replace(',', ' ')

def getAmount(category, yearData, type_category):
    """
    Simule exactement la fonction getAmount() du frontend.
    """
    # Catégories spéciales
    if category == "Charges d'amortissements":
        return abs(yearData["amortissements"]) if yearData["amortissements"] != 0 else None
    
    if category == "Coût du financement (hors remboursement du capital)":
        cout = yearData["cout_financement"]
        if cout is None or cout == 0:
            return None
        return abs(cout)
    
    # Catégories normales
    if type_category == 'Produits d\'exploitation':
        return yearData["produits"].get(category)
    else:
        # Les charges peuvent être stockées en négatif, prendre la valeur absolue pour l'affichage
        amount = yearData["charges"].get(category)
        return abs(amount) if amount is not None else None

def getCategoriesToDisplay(mappings):
    """
    Simule exactement la fonction getCategoriesToDisplay() du frontend.
    """
    categoriesToDisplay = []
    
    # Créer un Map des catégories avec leurs mappings et types
    categoriesMap = {}
    for mapping in mappings:
        hasLevel1Values = False
        if mapping.level_1_values:
            try:
                import json
                level1Values = json.loads(mapping.level_1_values)
                if isinstance(level1Values, list) and len(level1Values) > 0:
                    hasLevel1Values = True
            except:
                pass
        
        categoriesMap[mapping.category_name] = {
            'hasLevel1Values': hasLevel1Values,
            'type': mapping.type,
        }
    
    # Ajouter les catégories Produits d'exploitation prédéfinies qui ont des mappings
    for category in PRODUITS_CATEGORIES:
        mappingInfo = categoriesMap.get(category)
        if mappingInfo and (mappingInfo['hasLevel1Values'] or category in SPECIAL_CATEGORIES):
            categoriesToDisplay.append({
                'type': 'Produits d\'exploitation',
                'category': category,
                'hasMapping': mappingInfo['hasLevel1Values'] if mappingInfo else False,
            })
    
    # Ajouter les catégories Charges d'exploitation prédéfinies qui ont des mappings
    for category in CHARGES_CATEGORIES:
        mappingInfo = categoriesMap.get(category)
        # Les catégories spéciales sont TOUJOURS affichées, même sans mapping
        if category in SPECIAL_CATEGORIES:
            categoriesToDisplay.append({
                'type': 'Charges d\'exploitation',
                'category': category,
                'hasMapping': mappingInfo['hasLevel1Values'] if mappingInfo else False,
            })
        elif mappingInfo and mappingInfo['hasLevel1Values']:
            # Les autres catégories nécessitent un mapping avec des level_1_values
            categoriesToDisplay.append({
                'type': 'Charges d\'exploitation',
                'category': category,
                'hasMapping': True,
            })
    
    # Ajouter les catégories personnalisées
    for mapping in mappings:
        isPredefined = mapping.category_name in PRODUITS_CATEGORIES or mapping.category_name in CHARGES_CATEGORIES
        if not isPredefined:
            type_cat = 'Produits d\'exploitation' if mapping.type == "Produits d'exploitation" else 'Charges d\'exploitation'
            mappingInfo = categoriesMap.get(mapping.category_name)
            if mappingInfo and (mappingInfo['hasLevel1Values'] or mapping.category_name in SPECIAL_CATEGORIES):
                categoriesToDisplay.append({
                    'type': type_cat,
                    'category': mapping.category_name,
                    'hasMapping': mappingInfo['hasLevel1Values'] if mappingInfo else False,
                })
    
    return categoriesToDisplay

def simulateFrontendTable(years):
    """
    Simule exactement ce que le frontend affiche dans la table.
    """
    print("=" * 100)
    print("📊 SIMULATION EXACTE DE CE QUE LE FRONTEND AFFICHE")
    print("=" * 100)
    print()
    
    # Charger les mappings
    mappings = get_mappings(db)
    
    # Calculer les données pour chaque année
    all_data = {}
    for year in years:
        result = calculate_compte_resultat(db, year)
        all_data[year] = {
            'produits': result['produits'],
            'charges': result['charges'],
            'amortissements': result['amortissements'],
            'cout_financement': result['cout_financement'],
            'total_produits': result['total_produits'],
            'total_charges': result['total_charges'],
            'resultat_exploitation': result['resultat_exploitation'],
            'resultat_net': result['resultat_net'],
        }
    
    # Déterminer les catégories à afficher
    categoriesToDisplay = getCategoriesToDisplay(mappings)
    produitsCategories = [c for c in categoriesToDisplay if c['type'] == 'Produits d\'exploitation']
    chargesCategories = [c for c in categoriesToDisplay if c['type'] == 'Charges d\'exploitation']
    
    print(f"📋 Catégories à afficher: {len(categoriesToDisplay)}")
    print(f"   - Produits: {len(produitsCategories)}")
    print(f"   - Charges: {len(chargesCategories)}")
    print()
    
    # Afficher le tableau comme le frontend
    print("TABLEAU (comme affiché dans le frontend):")
    print("-" * 100)
    print(f"{'Catégorie':<50}", end="")
    for year in years:
        print(f"{year:>15}", end="")
    print()
    print("-" * 100)
    
    # Produits d'exploitation
    if produitsCategories:
        total_produits_label = 'Total des produits d\'exploitation'
        print(f"{total_produits_label:<50}", end="")
        for year in years:
            total = 0
            for cat_info in produitsCategories:
                amount = getAmount(cat_info['category'], all_data[year], 'Produits d\'exploitation')
                if amount is not None:
                    total += amount
            print(f"{formatAmount(total) if total != 0 else '-':>15}", end="")
        print()
        
        for cat_info in produitsCategories:
            print(f"  {cat_info['category']:<48}", end="")
            for year in years:
                amount = getAmount(cat_info['category'], all_data[year], 'Produits d\'exploitation')
                print(f"{formatAmount(amount):>15}", end="")
            print()
    
    # Charges d'exploitation
    if chargesCategories:
        total_charges_label = 'Total des charges d\'exploitation'
        print(f"{total_charges_label:<50}", end="")
        for year in years:
            total = 0
            for cat_info in chargesCategories:
                amount = getAmount(cat_info['category'], all_data[year], 'Charges d\'exploitation')
                if amount is not None:
                    total += amount
            print(f"{formatAmount(total) if total != 0 else '-':>15}", end="")
        print()
        
        for cat_info in chargesCategories:
            print(f"  {cat_info['category']:<48}", end="")
            for year in years:
                amount = getAmount(cat_info['category'], all_data[year], 'Charges d\'exploitation')
                # Debug pour 2023 et "Coût du financement"
                if year == 2023 and cat_info['category'] == "Coût du financement (hors remboursement du capital)":
                    print(f"{formatAmount(amount):>15} [DEBUG: {amount:,.2f}]", end="")
                else:
                    print(f"{formatAmount(amount):>15}", end="")
            print()
    
    # Résultat d'exploitation
    resultat_label = 'Résultat d\'exploitation'
    print(f"{resultat_label:<50}", end="")
    for year in years:
        total_produits = 0
        total_charges = 0
        for cat_info in produitsCategories:
            amount = getAmount(cat_info['category'], all_data[year], 'Produits d\'exploitation')
            if amount is not None:
                total_produits += amount
        for cat_info in chargesCategories:
            amount = getAmount(cat_info['category'], all_data[year], 'Charges d\'exploitation')
            if amount is not None:
                total_charges += amount
        resultat = total_produits - total_charges
        print(f"{formatAmount(resultat) if resultat != 0 else '-':>15}", end="")
    print()
    
    # Résultat net
    resultat_net_label = 'Résultat net de l\'exercice'
    print(f"{resultat_net_label:<50}", end="")
    for year in years:
        total_produits = 0
        total_charges = 0
        for cat_info in produitsCategories:
            amount = getAmount(cat_info['category'], all_data[year], 'Produits d\'exploitation')
            if amount is not None:
                total_produits += amount
        for cat_info in chargesCategories:
            amount = getAmount(cat_info['category'], all_data[year], 'Charges d\'exploitation')
            if amount is not None:
                total_charges += amount
        resultat = total_produits - total_charges
        print(f"{formatAmount(resultat) if resultat != 0 else '-':>15}", end="")
    print()
    
    print()
    print("=" * 100)
    print("🔍 DÉTAIL POUR TOUTES LES ANNÉES - COÛT DU FINANCEMENT:")
    print("=" * 100)
    print()
    print(f"{'Année':<10} {'Backend cout_financement':<25} {'getAmount() retourne':<25} {'Affiché (formatAmount)':<25} {'Différence':<15}")
    print("-" * 100)
    for year in years:
        yearData = all_data[year]
        cout_backend = yearData['cout_financement']
        cout_getAmount = getAmount("Coût du financement (hors remboursement du capital)", yearData, 'Charges d\'exploitation')
        cout_formatted = formatAmount(cout_getAmount)
        diff = abs(cout_backend - cout_getAmount) if cout_getAmount is not None else None
        diff_str = f"{diff:,.2f} €" if diff is not None and diff > 0.01 else "OK"
        cout_backend_str = f"{cout_backend:>20,.2f} €" if cout_backend else "N/A"
        cout_getAmount_str = f"{cout_getAmount:>20,.2f} €" if cout_getAmount is not None else "None"
        print(f"{year:<10} {cout_backend_str:<25} {cout_getAmount_str:<25} {cout_formatted:>25} {diff_str:<15}")
    
    print()
    print("=" * 100)
    print("🔍 DÉTAIL POUR 2023 (BUG DÉTECTÉ):")
    print("=" * 100)
    print()
    
    year = 2023
    yearData = all_data[year]
    
    print(f"Données brutes du backend pour {year}:")
    print(f"  cout_financement: {yearData['cout_financement']:,.2f} €")
    print(f"  amortissements: {yearData['amortissements']:,.2f} €")
    print()
    
    print("Ce que getAmount() retourne pour chaque catégorie de charges:")
    for cat_info in chargesCategories:
        amount = getAmount(cat_info['category'], yearData, 'Charges d\'exploitation')
        print(f"  {cat_info['category']:<50} {formatAmount(amount):>15}")
        if cat_info['category'] == "Coût du financement (hors remboursement du capital)":
            print(f"    ⚠️  VALEUR CALCULÉE: {amount:,.2f} €")
            print(f"    ⚠️  VALEUR BACKEND: {yearData['cout_financement']:,.2f} €")
            print(f"    ⚠️  VALEUR DANS CHARGES: {yearData['charges'].get(cat_info['category'], 'N/A')}")
    
    print()
    print("Total des charges calculé par le frontend:")
    total_charges_frontend = 0
    for cat_info in chargesCategories:
        amount = getAmount(cat_info['category'], yearData, 'Charges d\'exploitation')
        if amount is not None:
            total_charges_frontend += amount
            print(f"  + {cat_info['category']:<45} {formatAmount(amount):>15}")
    print(f"  = TOTAL: {formatAmount(total_charges_frontend):>15}")
    print()
    print(f"Total des charges du backend: {yearData['total_charges']:,.2f} €")
    
    print()
    print("=" * 100)

if __name__ == "__main__":
    # Années à afficher (comme le frontend)
    current_year = date.today().year
    years = list(range(2020, current_year + 1))
    
    simulateFrontendTable(years)
    
    db.close()
