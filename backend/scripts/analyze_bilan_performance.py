"""
Script d'analyse de performance détaillée pour le bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script analyse en détail chaque élément de configuration du bilan
et compare avec les calculs d'amortissement pour identifier les goulots d'étranglement.
"""

import sys
import os
import time
from datetime import date
from typing import Dict, List

# Ajouter le chemin du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from backend.database.connection import get_db
from backend.database.models import (
    BilanMapping,
    BilanConfig,
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatOverride
)
from backend.api.services.bilan_service import (
    get_mappings,
    get_level_3_values,
    calculate_normal_category,
    calculate_amortizations_cumul,
    calculate_compte_bancaire,
    calculate_resultat_exercice,
    calculate_report_a_nouveau,
    calculate_capital_restant_du,
    calculate_bilan
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat
from sqlalchemy import func, and_

def log_step(step_name: str, start_time: float, indent: int = 0):
    """Afficher un log avec timestamp et indentation."""
    elapsed = time.time() - start_time
    indent_str = "  " * indent
    print(f"{indent_str}⏱️  [{elapsed:7.3f}s] {step_name}")

def analyze_transaction_count(db, level_3_values: List[str], year: int):
    """Analyser le nombre de transactions pour les filtres."""
    start = time.time()
    end_date = date(year, 12, 31)
    
    # Compter les transactions avec level_3 dans level_3_values
    count_query = db.query(func.count(Transaction.id)).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            Transaction.date <= end_date
        )
    )
    total_count = count_query.scalar()
    
    log_step(f"Nombre total de transactions (level_3 in {level_3_values}, date <= {end_date}): {total_count}", start, 1)
    return total_count

def analyze_normal_category_performance(db, mapping: BilanMapping, level_3_values: List[str], year: int):
    """Analyser la performance d'une catégorie normale."""
    category_start = time.time()
    print(f"\n  📊 Analyse catégorie normale: {mapping.category_name}")
    
    # Analyser le parsing JSON
    parse_start = time.time()
    try:
        level_1_values = json.loads(mapping.level_1_values) if mapping.level_1_values else []
    except Exception as e:
        log_step(f"❌ Erreur parsing JSON: {e}", parse_start, 2)
        return None
    log_step(f"Parsing JSON: {len(level_1_values)} level_1 values", parse_start, 2)
    
    # Analyser la requête SQL
    query_start = time.time()
    end_date = date(year, 12, 31)
    
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            EnrichedTransaction.level_1.in_(level_1_values),
            Transaction.date <= end_date
        )
    )
    
    # Compter d'abord pour voir combien de lignes sont concernées
    count_query = db.query(func.count(Transaction.id)).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            EnrichedTransaction.level_1.in_(level_1_values),
            Transaction.date <= end_date
        )
    )
    row_count = count_query.scalar()
    log_step(f"Nombre de transactions concernées: {row_count}", query_start, 2)
    
    # Exécuter la requête de somme
    result = query.scalar()
    log_step(f"Requête SQL SUM: {abs(result) if result else 0:.2f}€", query_start, 2)
    
    total_time = time.time() - category_start
    log_step(f"✅ Total catégorie {mapping.category_name}: {abs(result) if result else 0:.2f}€", category_start, 2)
    
    return {
        'category_name': mapping.category_name,
        'time': total_time,
        'row_count': row_count,
        'amount': abs(result) if result else 0.0
    }

def analyze_special_category_performance(db, mapping: BilanMapping, year: int):
    """Analyser la performance d'une catégorie spéciale."""
    category_start = time.time()
    print(f"\n  🔧 Analyse catégorie spéciale: {mapping.category_name} (source: {mapping.special_source})")
    
    if mapping.special_source == "amortization_result":
        func_start = time.time()
        amount = calculate_amortizations_cumul(db, year)
        log_step(f"calculate_amortizations_cumul: {amount:.2f}€", func_start, 2)
        
    elif mapping.special_source == "transactions":
        func_start = time.time()
        amount = calculate_compte_bancaire(db, year)
        log_step(f"calculate_compte_bancaire: {amount:.2f}€", func_start, 2)
        
    elif mapping.special_source == "compte_resultat":
        func_start = time.time()
        amount = calculate_resultat_exercice(db, year, mapping.compte_resultat_view_id)
        log_step(f"calculate_resultat_exercice: {amount:.2f}€", func_start, 2)
        
    elif mapping.special_source == "compte_resultat_cumul":
        func_start = time.time()
        # Analyser en détail le report à nouveau
        print(f"    🔍 Analyse détaillée de calculate_report_a_nouveau pour {year}:")
        # La fonction optimisée calcule directement, on ne peut plus détailler année par année
        # mais on peut mesurer le temps total
        amount = calculate_report_a_nouveau(db, year)
        log_step(f"calculate_report_a_nouveau (total): {amount:.2f}€", func_start, 2)
        
    elif mapping.special_source == "loan_payments":
        func_start = time.time()
        amount = calculate_capital_restant_du(db, year)
        log_step(f"calculate_capital_restant_du: {amount:.2f}€", func_start, 2)
        
    else:
        amount = 0.0
        log_step(f"Source inconnue: {mapping.special_source}", category_start, 2)
    
    total_time = time.time() - category_start
    log_step(f"✅ Total catégorie {mapping.category_name}: {amount:.2f}€", category_start, 2)
    
    return {
        'category_name': mapping.category_name,
        'special_source': mapping.special_source,
        'time': total_time,
        'amount': amount
    }

def analyze_amortization_performance(db, year: int):
    """Analyser la performance du calcul d'amortissement pour comparaison."""
    print(f"\n  📈 Analyse calcul amortissements (pour comparaison):")
    start = time.time()
    
    # Analyser calculate_amortizations_cumul en détail
    query_start = time.time()
    end_date = date(year, 12, 31)
    
    # Compter les résultats d'amortissement
    count_query = db.query(func.count(AmortizationResult.id)).filter(
        AmortizationResult.date <= end_date
    )
    row_count = count_query.scalar()
    log_step(f"Nombre de résultats d'amortissement: {row_count}", query_start, 2)
    
    # Calculer la somme
    sum_query = db.query(func.sum(AmortizationResult.amount)).filter(
        AmortizationResult.year <= year
    )
    total = sum_query.scalar()
    amount = abs(total) if total else 0.0
    log_step(f"Somme des amortissements: {amount:.2f}€", query_start, 2)
    
    total_time = time.time() - start
    log_step(f"✅ Total calcul amortissements: {amount:.2f}€", start, 2)
    
    return {
        'time': total_time,
        'row_count': row_count,
        'amount': amount
    }

def analyze_compte_resultat_performance(db, year: int):
    """Analyser la performance du calcul de compte de résultat."""
    print(f"\n  📊 Analyse calcul compte de résultat (pour comparaison):")
    start = time.time()
    
    result = calculate_compte_resultat(db, year)
    elapsed = time.time() - start
    
    log_step(f"calculate_compte_resultat: {elapsed:.3f}s", start, 2)
    log_step(f"Résultat net: {result.get('resultat_net', 0):.2f}€", start, 2)
    
    return {
        'time': elapsed,
        'resultat_net': result.get('resultat_net', 0)
    }

def main():
    """Fonction principale d'analyse."""
    print("=" * 80)
    print("🔍 ANALYSE DE PERFORMANCE DÉTAILLÉE - BILAN")
    print("=" * 80)
    
    db = next(get_db())
    
    # Années à analyser
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    
    # Charger la configuration
    print("\n📋 CHARGEMENT DE LA CONFIGURATION")
    print("-" * 80)
    config_start = time.time()
    
    level_3_values = get_level_3_values(db)
    log_step(f"Level 3 values: {level_3_values}", config_start, 0)
    
    mappings = get_mappings(db)
    log_step(f"Nombre de mappings: {len(mappings)}", config_start, 0)
    
    # Séparer les mappings normaux et spéciaux
    normal_mappings = [m for m in mappings if not m.is_special]
    special_mappings = [m for m in mappings if m.is_special]
    
    log_step(f"Mappings normaux: {len(normal_mappings)}", config_start, 0)
    log_step(f"Mappings spéciaux: {len(special_mappings)}", config_start, 0)
    
    print(f"\n⏱️  Temps total chargement config: {time.time() - config_start:.3f}s")
    
    # Analyser pour chaque année
    for year in years:
        print("\n" + "=" * 80)
        print(f"📅 ANALYSE POUR L'ANNÉE {year}")
        print("=" * 80)
        
        year_start = time.time()
        
        # Analyser le nombre de transactions
        print(f"\n📊 ANALYSE DES TRANSACTIONS")
        print("-" * 80)
        analyze_transaction_count(db, level_3_values, year)
        
        # Analyser les catégories normales
        print(f"\n📋 ANALYSE DES CATÉGORIES NORMALES")
        print("-" * 80)
        normal_results = []
        for mapping in normal_mappings:
            result = analyze_normal_category_performance(db, mapping, level_3_values, year)
            if result:
                normal_results.append(result)
        
        # Analyser les catégories spéciales
        print(f"\n🔧 ANALYSE DES CATÉGORIES SPÉCIALES")
        print("-" * 80)
        special_results = []
        for mapping in special_mappings:
            result = analyze_special_category_performance(db, mapping, year)
            if result:
                special_results.append(result)
        
        # Analyser les amortissements (pour comparaison)
        print(f"\n📈 ANALYSE DES AMORTISSEMENTS (COMPARAISON)")
        print("-" * 80)
        amortization_result = analyze_amortization_performance(db, year)
        
        # Analyser le compte de résultat (pour comparaison)
        print(f"\n📊 ANALYSE DU COMPTE DE RÉSULTAT (COMPARAISON)")
        print("-" * 80)
        compte_resultat_result = analyze_compte_resultat_performance(db, year)
        
        # Calculer le bilan complet
        print(f"\n🎯 CALCUL COMPLET DU BILAN")
        print("-" * 80)
        bilan_start = time.time()
        bilan_result = calculate_bilan(db, year, mappings, level_3_values)
        bilan_time = time.time() - bilan_start
        log_step(f"calculate_bilan complet: {bilan_time:.3f}s", bilan_start, 0)
        
        # Résumé
        print(f"\n📊 RÉSUMÉ POUR {year}")
        print("-" * 80)
        total_normal_time = sum(r['time'] for r in normal_results)
        total_special_time = sum(r['time'] for r in special_results)
        
        print(f"  Catégories normales:")
        print(f"    - Nombre: {len(normal_results)}")
        print(f"    - Temps total: {total_normal_time:.3f}s")
        print(f"    - Temps moyen par catégorie: {total_normal_time / len(normal_results) if normal_results else 0:.3f}s")
        
        print(f"  Catégories spéciales:")
        print(f"    - Nombre: {len(special_results)}")
        print(f"    - Temps total: {total_special_time:.3f}s")
        print(f"    - Temps moyen par catégorie: {total_special_time / len(special_results) if special_results else 0:.3f}s")
        
        print(f"  Amortissements (comparaison):")
        print(f"    - Temps: {amortization_result['time']:.3f}s")
        print(f"    - Lignes: {amortization_result['row_count']}")
        
        print(f"  Compte de résultat (comparaison):")
        print(f"    - Temps: {compte_resultat_result['time']:.3f}s")
        
        print(f"  Bilan complet:")
        print(f"    - Temps: {bilan_time:.3f}s")
        print(f"    - Nombre de catégories: {len(bilan_result['categories'])}")
        
        year_total = time.time() - year_start
        print(f"\n⏱️  Temps total pour {year}: {year_total:.3f}s")
        
        # Détail par catégorie normale (top 5 plus lentes)
        if normal_results:
            print(f"\n🐌 TOP 5 CATÉGORIES NORMALES LES PLUS LENTES:")
            sorted_normal = sorted(normal_results, key=lambda x: x['time'], reverse=True)[:5]
            for i, result in enumerate(sorted_normal, 1):
                print(f"  {i}. {result['category_name']}: {result['time']:.3f}s ({result['row_count']} transactions, {result['amount']:.2f}€)")
        
        # Détail par catégorie spéciale
        if special_results:
            print(f"\n🔧 DÉTAIL CATÉGORIES SPÉCIALES:")
            for result in special_results:
                print(f"  - {result['category_name']} ({result['special_source']}): {result['time']:.3f}s ({result['amount']:.2f}€)")
    
    # Analyse globale
    print("\n" + "=" * 80)
    print("📊 ANALYSE GLOBALE")
    print("=" * 80)
    
    # Calculer pour toutes les années en une fois (comme le frontend)
    print(f"\n🎯 CALCUL POUR TOUTES LES ANNÉES (comme le frontend)")
    print("-" * 80)
    all_years_start = time.time()
    
    for year in years:
        year_start = time.time()
        result = calculate_bilan(db, year, mappings, level_3_values)
        year_time = time.time() - year_start
        print(f"  Année {year}: {year_time:.3f}s ({len(result['categories'])} catégories)")
    
    all_years_time = time.time() - all_years_start
    print(f"\n⏱️  Temps total pour {len(years)} années: {all_years_time:.3f}s")
    print(f"⏱️  Temps moyen par année: {all_years_time / len(years):.3f}s")
    
    db.close()
    print("\n✅ Analyse terminée")

if __name__ == "__main__":
    import json
    main()
