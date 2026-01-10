#!/usr/bin/env python3
"""
Script pour afficher le tableau d'amortissement tel qu'il apparaît dans l'interface.

Ce script affiche les données d'amortissement sous forme de tableau croisé :
- Catégories en lignes
- Années en colonnes
- Ligne Total en bas
- Colonne Total à droite
- Ligne Cumulé

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from collections import defaultdict
from datetime import date

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationResult

def format_amount(amount: float) -> str:
    """Formate un montant avec 2 décimales et le symbole EUR."""
    return f"{amount:,.2f} €"

def display_table():
    """Affiche le tableau d'amortissement."""
    print("=" * 100)
    print("📊 TABLEAU D'AMORTISSEMENT - Données en base de données")
    print("=" * 100)
    print()
    
    init_database()
    db = SessionLocal()
    
    try:
        # Récupérer tous les résultats
        results = db.query(AmortizationResult).all()
        
        if not results:
            print("ℹ️  Aucun résultat d'amortissement en base de données.")
            print("   Configurez les amortissements dans l'interface pour générer des résultats.")
            return
        
        print(f"📈 Total de résultats: {len(results)}")
        print()
        
        # Collecter toutes les catégories et années uniques
        # Filtrer pour n'afficher que jusqu'à l'année en cours (comme check_amortization_state.py)
        current_year = date.today().year
        categories_set = set()
        years_set = set()
        
        for result in results:
            categories_set.add(result.category)
            # Ne garder que les années jusqu'à l'année en cours
            if result.year <= current_year:
                years_set.add(result.year)
        
        categories = sorted(list(categories_set))
        years = sorted(list(years_set))
        
        if not categories or not years:
            print("⚠️  Aucune catégorie ou année trouvée.")
            return
        
        print(f"📋 Catégories: {len(categories)}")
        print(f"📅 Années: {min(years)} - {max(years)} ({len(years)} années)")
        print()
        
        # Créer un dictionnaire pour accès rapide
        data_dict = defaultdict(lambda: defaultdict(float))
        
        for result in results:
            data_dict[result.category][result.year] += result.amount
        
        # Créer la matrice de données
        data = []
        totals_by_category = {}
        totals_by_year = defaultdict(float)
        
        for category in categories:
            row = []
            category_total = 0.0
            
            for year in years:
                amount = data_dict[category].get(year, 0.0)
                row.append(amount)
                category_total += amount
                totals_by_year[year] += amount
            
            data.append(row)
            totals_by_category[category] = category_total
        
        # Calculer le total général
        grand_total = sum(totals_by_category.values())
        
        # Afficher l'en-tête
        print(" " * 30, end="")
        for year in years:
            print(f"{year:>12}", end="")
        print(f"{'Total':>15}")
        print("-" * 100)
        
        # Afficher les lignes de catégories
        for i, category in enumerate(categories):
            # Nom de la catégorie (tronqué à 28 caractères)
            category_display = category[:28] if len(category) <= 28 else category[:25] + "..."
            print(f"{category_display:30}", end="")
            
            # Montants par année
            for j, year in enumerate(years):
                amount = data[i][j]
                color_marker = "🔴" if amount < 0 else "  "
                print(f"{color_marker}{format_amount(amount):>13}", end="")
            
            # Total de la ligne
            row_total = totals_by_category[category]
            color_marker = "🔴" if row_total < 0 else "  "
            print(f"{color_marker}{format_amount(row_total):>14}")
        
        # Ligne Total
        print("-" * 100)
        print(f"{'Total':30}", end="")
        for year in years:
            year_total = totals_by_year[year]
            color_marker = "🔴" if year_total < 0 else "  "
            print(f"{color_marker}{format_amount(year_total):>13}", end="")
        
        color_marker = "🔴" if grand_total < 0 else "  "
        print(f"{color_marker}{format_amount(grand_total):>14}")
        
        # Ligne Cumulé
        print("-" * 100)
        print(f"{'Cumulé':30}", end="")
        cumulative = 0.0
        for year in years:
            cumulative += totals_by_year[year]
            color_marker = "🔴" if cumulative < 0 else "  "
            print(f"{color_marker}{format_amount(cumulative):>13}", end="")
        
        color_marker = "🔴" if grand_total < 0 else "  "
        print(f"{color_marker}{format_amount(grand_total):>14}")
        
        print("=" * 100)
        print()
        
        # Afficher un résumé détaillé
        print("📊 RÉSUMÉ DÉTAILLÉ")
        print("-" * 100)
        print(f"Grand total: {format_amount(grand_total)}")
        print()
        
        print("Par catégorie:")
        for category in categories:
            total = totals_by_category[category]
            print(f"  • {category}: {format_amount(total)}")
        print()
        
        print("Par année:")
        for year in years:
            total = totals_by_year[year]
            print(f"  • {year}: {format_amount(total)}")
        print()
        
        # Compter les résultats par catégorie
        from sqlalchemy import func
        category_counts = db.query(
            AmortizationResult.category,
            func.count(AmortizationResult.id).label('count')
        ).group_by(AmortizationResult.category).all()
        
        print("Nombre de résultats par catégorie:")
        for category, count in category_counts:
            print(f"  • {category}: {count} résultats")
        print()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Fonction principale."""
    display_table()

if __name__ == "__main__":
    main()

