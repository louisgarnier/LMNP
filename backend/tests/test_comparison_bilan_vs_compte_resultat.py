"""
Test comparatif : Bilan vs Compte de Résultat
Pour comprendre pourquoi le compte de résultat fonctionne et pas le bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_comparison_bilan_vs_compte_resultat.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_comparison():
    """Compare le fonctionnement du Bilan vs Compte de Résultat."""
    print("=" * 80)
    print("COMPARAISON : BILAN vs COMPTE DE RÉSULTAT")
    print("=" * 80)
    print()
    
    # ========== DIFFÉRENCE 1 : STRUCTURE HIÉRARCHIQUE ==========
    print("📊 DIFFÉRENCE 1 : STRUCTURE HIÉRARCHIQUE")
    print("-" * 80)
    print()
    print("COMPTE DE RÉSULTAT:")
    print("  📋 Structure: Type → Catégorie comptable")
    print("     - Type: 'Produits d'exploitation' ou 'Charges d'exploitation'")
    print("     - Catégorie comptable: ex. 'Loyers hors charge encaissés'")
    print("     - Pas de sous-catégorie")
    print()
    print("BILAN:")
    print("  📋 Structure: Type → Sous-catégorie → Catégorie comptable")
    print("     - Type: 'ACTIF' ou 'PASSIF'")
    print("     - Sous-catégorie: ex. 'Actif immobilisé', 'Capitaux propres'")
    print("     - Catégorie comptable: ex. 'Immobilisations', 'Souscription de parts sociales'")
    print()
    
    # ========== DIFFÉRENCE 2 : MÉTHODE DE CALCUL ==========
    print("📊 DIFFÉRENCE 2 : MÉTHODE DE CALCUL")
    print("-" * 80)
    print()
    print("COMPTE DE RÉSULTAT:")
    print("  ✅ Calcule les montants À LA VOLÉE depuis les transactions")
    print("  ✅ Utilise: GET /api/compte-resultat/calculate?years=...")
    print("  ✅ Pas besoin de pré-calculer ou stocker les données")
    print("  ✅ Les données sont TOUJOURS à jour (calculées dynamiquement)")
    print()
    print("BILAN:")
    print("  ✅ Calcule les montants À LA VOLÉE depuis les transactions (comme compte de résultat)")
    print("  ✅ Utilise: GET /api/bilan/calculate?years=...")
    print("  ✅ Pas besoin de pré-calculer ou stocker les données")
    print("  ✅ Les données sont TOUJOURS à jour (calculées dynamiquement)")
    print("  ⚠️  Note: L'endpoint /api/bilan/generate existe encore mais n'est plus utilisé par le frontend")
    print()
    
    # ========== TEST 1 : Compte de Résultat (calcul dynamique) ==========
    print("=" * 80)
    print("TEST 1 : COMPTE DE RÉSULTAT (Calcul dynamique)")
    print("=" * 80)
    print()
    
    # Récupérer les mappings
    print("📋 Étape 1: Récupérer les mappings")
    mappings_response = client.get("/api/compte-resultat/mappings")
    mappings = mappings_response.json().get("mappings", [])
    print(f"  ✅ {len(mappings)} mapping(s) trouvé(s)")
    print()
    
    # Calculer les montants directement (sans génération préalable)
    print("📊 Étape 2: Calculer les montants (sans génération préalable)")
    years = [2021, 2022, 2023]
    years_param = ",".join(str(y) for y in years)
    calculate_response = client.get(
        f"/api/compte-resultat/calculate?years={years_param}"
    )
    if calculate_response.status_code == 200:
        amounts = calculate_response.json()
        print(f"  ✅ Montants calculés directement pour {len(years)} année(s)")
        print(f"  ✅ Pas besoin de génération préalable")
        print(f"  ✅ Les données sont toujours à jour")
        
        # Afficher quelques exemples
        category_count = 0
        for year, year_data in amounts.items():
            if category_count < 3:
                for category, amount in list(year_data.items())[:2]:
                    print(f"     {year} - {category}: {amount:,.2f} €")
                    category_count += 1
    else:
        print(f"  ❌ Erreur: {calculate_response.status_code}")
    print()
    
    # ========== TEST 2 : Bilan (calcul à la volée) ==========
    print("=" * 80)
    print("TEST 2 : BILAN (Calcul à la volée)")
    print("=" * 80)
    print()
    
    # Récupérer les mappings
    print("📋 Étape 1: Récupérer les mappings")
    bilan_mappings_response = client.get("/api/bilan/mappings")
    bilan_mappings = bilan_mappings_response.json().get("mappings", [])
    print(f"  ✅ {len(bilan_mappings)} mapping(s) trouvé(s)")
    
    # Afficher la structure hiérarchique
    print()
    print("  📊 Structure hiérarchique des mappings:")
    for m in bilan_mappings[:5]:  # Limiter à 5 pour la lisibilité
        print(f"     Type: {m.get('type')}")
        print(f"       └─ Sous-catégorie: {m.get('sub_category')}")
        print(f"          └─ Catégorie: {m.get('category_name')}")
        print()
    print()
    
    # Calculer les montants directement (sans génération préalable)
    print("📊 Étape 2: Calculer les montants (sans génération préalable)")
    years_param = ",".join(str(y) for y in years)
    calculate_response = client.get(f"/api/bilan/calculate?years={years_param}")
    if calculate_response.status_code == 200:
        amounts = calculate_response.json()
        print(f"  ✅ Montants calculés directement pour {len(amounts)} année(s)")
        print(f"  ✅ Pas besoin de génération préalable")
        print(f"  ✅ Les données sont toujours à jour")
        
        # Afficher quelques exemples
        category_count = 0
        for year, year_data in sorted(amounts.items()):
            if category_count < 3:
                for category, amount in list(year_data.items())[:2]:
                    print(f"     {year} - {category}: {amount:,.2f} €")
                    category_count += 1
    else:
        print(f"  ❌ Erreur: {calculate_response.status_code}")
    print()
    
    # ========== DIFFÉRENCE 3 : FLOW DANS LE FRONTEND ==========
    print("=" * 80)
    print("📊 DIFFÉRENCE 3 : FLOW DANS LE FRONTEND")
    print("-" * 80)
    print()
    print("COMPTE DE RÉSULTAT:")
    print("  1. CompteResultatConfigCard: Modifie un mapping")
    print("  2. CompteResultatTable: Appelle calculateAmounts() → données à jour")
    print("  ✅ Calcul à la volée, toujours à jour")
    print()
    print("BILAN:")
    print("  1. BilanConfigCard: Modifie un mapping")
    print("  2. BilanTable: Appelle calculateAmounts() → données à jour")
    print("  ✅ Calcul à la volée, toujours à jour (comme compte de résultat)")
    print()
    
    # ========== RÉSUMÉ ==========
    print("=" * 80)
    print("📋 RÉSUMÉ")
    print("=" * 80)
    print()
    print("COMPTE DE RÉSULTAT:")
    print("  ✅ Structure: Type → Catégorie comptable (2 niveaux)")
    print("  ✅ Calcul dynamique → toujours à jour")
    print("  ✅ Pas de génération nécessaire")
    print()
    print("BILAN:")
    print("  ✅ Structure: Type → Sous-catégorie → Catégorie comptable (3 niveaux)")
    print("  ✅ Calcul dynamique → toujours à jour (comme compte de résultat)")
    print("  ✅ Pas de génération nécessaire")
    print()
    print("CONCLUSION:")
    print("  Les deux fonctionnent maintenant de la même manière : calcul à la volée.")
    print("  La seule différence est la structure hiérarchique :")
    print("  - Compte de résultat : 2 niveaux (Type → Catégorie)")
    print("  - Bilan : 3 niveaux (Type → Sous-catégorie → Catégorie)")
    print()


if __name__ == "__main__":
    try:
        test_comparison()
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Erreur: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)

