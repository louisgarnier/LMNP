"""
Script de test pour comparer les données BDD vs ce que le frontend devrait afficher.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script :
1. Vérifie en BDD ce qui existe pour chaque propriété (AmortizationType et AmortizationResult)
2. Simule les appels API frontend pour voir ce qui serait retourné
3. Compare les deux pour identifier les incohérences

Usage:
    python3 backend/scripts/test_amortizations_bdd_vs_frontend_phase_11_bis_3_2.py
"""

import sys
import requests
import json
from pathlib import Path
from collections import defaultdict

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Property, AmortizationType, AmortizationResult, Transaction

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Affiche un titre de section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def get_bdd_data(property_id):
    """Récupère les données en BDD pour une propriété."""
    db = SessionLocal()
    try:
        # Types d'amortissement
        types = db.query(AmortizationType).filter(AmortizationType.property_id == property_id).all()
        type_names = [t.name for t in types]
        
        # Résultats d'amortissement (via Transaction)
        results = db.query(AmortizationResult).join(
            Transaction, AmortizationResult.transaction_id == Transaction.id
        ).filter(Transaction.property_id == property_id).all()
        
        # Catégories dans les résultats
        result_categories = set([r.category for r in results])
        
        # Agréger par catégorie
        by_category = defaultdict(float)
        for r in results:
            by_category[r.category] += abs(r.amount)
        
        return {
            'types': type_names,
            'types_count': len(types),
            'results_count': len(results),
            'result_categories': sorted(result_categories),
            'by_category': dict(by_category)
        }
    finally:
        db.close()

def get_api_data(property_id, level_2_value=None):
    """Récupère les données via API pour une propriété."""
    try:
        # GET /api/amortization/types
        params = {'property_id': property_id}
        if level_2_value:
            params['level_2_value'] = level_2_value
        
        response = requests.get(f"{BASE_URL}/amortization/types", params=params, timeout=5)
        if response.status_code != 200:
            return {'error': f"GET types failed: {response.status_code} - {response.text[:200]}"}
        
        types_data = response.json()
        type_names = [t['name'] for t in types_data.get('items', [])]
        
        # GET /api/amortization/results/aggregated
        response = requests.get(f"{BASE_URL}/amortization/results/aggregated", params={'property_id': property_id}, timeout=5)
        if response.status_code != 200:
            return {'error': f"GET results failed: {response.status_code} - {response.text[:200]}"}
        
        results_data = response.json()
        categories = results_data.get('categories', [])
        grand_total = results_data.get('grand_total', 0)
        
        return {
            'types': type_names,
            'types_count': len(type_names),
            'categories': categories,
            'categories_count': len(categories),
            'grand_total': grand_total
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    """Exécute la comparaison."""
    print("=" * 80)
    print("Test BDD vs Frontend - Amortizations")
    print("=" * 80)
    print("\n⚠️  Vérification que le serveur backend est démarré...")
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("❌ Serveur backend répond mais avec une erreur")
            sys.exit(1)
        print("✅ Serveur backend accessible")
    except requests.exceptions.RequestException:
        print("❌ Serveur backend non accessible")
        print("   Démarrez-le avec: python3 -m uvicorn backend.api.main:app --reload --port 8000")
        sys.exit(1)
    
    # Récupérer toutes les propriétés
    db = SessionLocal()
    try:
        properties = db.query(Property).order_by(Property.id).all()
    finally:
        db.close()
    
    print(f"\n📋 {len(properties)} propriété(s) trouvée(s)")
    
    # Tester chaque propriété
    for prop in properties:
        print_section(f"Property {prop.id} : {prop.name}")
        
        # Données BDD
        print("\n📊 DONNÉES EN BASE DE DONNÉES:")
        bdd_data = get_bdd_data(prop.id)
        print(f"  Types d'amortissement configurés: {bdd_data['types_count']}")
        if bdd_data['types']:
            print(f"  Noms des types: {bdd_data['types']}")
        else:
            print(f"  ⚠️  AUCUN TYPE CONFIGURÉ")
        
        print(f"  Résultats d'amortissement: {bdd_data['results_count']}")
        if bdd_data['result_categories']:
            print(f"  Catégories dans résultats: {bdd_data['result_categories']}")
            print(f"  Montants par catégorie:")
            for cat, amount in bdd_data['by_category'].items():
                print(f"    - {cat}: {amount:,.2f} €")
        else:
            print(f"  ⚠️  AUCUN RÉSULTAT")
        
        # Données API (ce que le frontend verrait)
        print("\n🌐 DONNÉES VIA API (ce que le frontend verrait):")
        api_data = get_api_data(prop.id)
        
        if 'error' in api_data:
            print(f"  ❌ ERREUR: {api_data['error']}")
            continue
        
        print(f"  Types retournés par API: {api_data['types_count']}")
        if api_data['types']:
            print(f"  Noms des types: {api_data['types']}")
        else:
            print(f"  ⚠️  AUCUN TYPE RETOURNÉ")
        
        print(f"  Catégories dans résultats agrégés: {api_data['categories_count']}")
        if api_data['categories']:
            print(f"  Catégories: {api_data['categories']}")
        else:
            print(f"  ⚠️  AUCUNE CATÉGORIE")
        
        print(f"  Grand total: {api_data['grand_total']:,.2f} €")
        
        # Comparaison
        print("\n🔍 COMPARAISON:")
        
        # Comparer les types
        bdd_types_set = set(bdd_data['types'])
        api_types_set = set(api_data['types'])
        
        if bdd_types_set == api_types_set:
            print(f"  ✅ Types: Identiques ({len(bdd_types_set)} types)")
        else:
            print(f"  ❌ Types: DIFFÉRENTS")
            only_bdd = bdd_types_set - api_types_set
            only_api = api_types_set - bdd_types_set
            if only_bdd:
                print(f"    ⚠️  En BDD mais pas dans API: {only_bdd}")
            if only_api:
                print(f"    ⚠️  Dans API mais pas en BDD: {only_api}")
        
        # Comparer les catégories
        bdd_categories_set = set(bdd_data['result_categories'])
        api_categories_set = set(api_data['categories'])
        
        if bdd_categories_set == api_categories_set:
            print(f"  ✅ Catégories: Identiques ({len(bdd_categories_set)} catégories)")
        else:
            print(f"  ❌ Catégories: DIFFÉRENTES")
            only_bdd = bdd_categories_set - api_categories_set
            only_api = api_categories_set - bdd_categories_set
            if only_bdd:
                print(f"    ⚠️  En BDD mais pas dans API: {only_bdd}")
            if only_api:
                print(f"    ⚠️  Dans API mais pas en BDD: {only_api}")
        
        # Vérifier les incohérences
        print("\n⚠️  VÉRIFICATIONS:")
        
        # 1. Si aucun type configuré mais des résultats existent
        if bdd_data['types_count'] == 0 and bdd_data['results_count'] > 0:
            print(f"  ❌ PROBLÈME: Aucun type configuré mais {bdd_data['results_count']} résultats existent")
            print(f"     → Les résultats ne devraient pas s'afficher dans la card table")
        
        # 2. Si des catégories dans résultats ne correspondent à aucun type
        orphan_categories = bdd_categories_set - bdd_types_set
        if orphan_categories:
            print(f"  ❌ PROBLÈME: Catégories orphelines (pas de type correspondant): {orphan_categories}")
            print(f"     → Ces catégories ne devraient pas s'afficher car aucun type n'est configuré")
        
        # 3. Si des types configurés mais aucun résultat
        if bdd_data['types_count'] > 0 and bdd_data['results_count'] == 0:
            print(f"  ℹ️  INFO: {bdd_data['types_count']} type(s) configuré(s) mais aucun résultat")
            print(f"     → Normal si aucune transaction ne correspond aux types")
        
        # 4. Si grand_total > 0 mais aucun type configuré
        if api_data['grand_total'] > 0 and bdd_data['types_count'] == 0:
            print(f"  ❌ PROBLÈME: Grand total = {api_data['grand_total']:,.2f} € mais aucun type configuré")
            print(f"     → Le frontend ne devrait pas afficher de valeurs")
        
        # 5. Si des catégories dans API ne correspondent à aucun type configuré
        if api_categories_set and bdd_types_set:
            orphan_in_api = api_categories_set - bdd_types_set
            if orphan_in_api:
                print(f"  ❌ PROBLÈME: Catégories dans API sans type correspondant: {orphan_in_api}")
                print(f"     → Ces catégories ne devraient pas s'afficher dans la card table")

if __name__ == "__main__":
    main()
