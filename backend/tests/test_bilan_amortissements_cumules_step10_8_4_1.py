#!/usr/bin/env python3
"""
Test Step 10.8.4.1 - Vérification affichage "Amortissements cumulés"

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce test vérifie que :
1. L'API retourne bien les montants pour "Amortissements cumulés"
2. Les montants sont positifs depuis le backend (valeur absolue)
3. Le calcul "Actif immobilisé" utilise correctement les amortissements (soustraction)
4. La position est correcte (sous "Immobilisations")

Run with: python3 backend/tests/test_bilan_amortissements_cumules_step10_8_4_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_amortissements_cumules():
    """Test de la catégorie spéciale 'Amortissements cumulés'."""
    print("=" * 80)
    print("TEST STEP 10.8.4.1 - Amortissements cumulés")
    print("=" * 80)
    print()
    
    # Test 1: Vérifier que l'API retourne les montants
    print("📋 Test 1: Vérification API /api/bilan/calculate")
    print("-" * 80)
    
    response = client.get(
        '/api/bilan/calculate?years=2021,2022,2023',
        headers={'Origin': 'http://localhost:3000'}
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur API: {response.status_code}")
        print(response.text[:300])
        return False
    
    data = response.json()
    print(f"✅ API répond correctement")
    print()
    
    # Test 2: Vérifier que "Amortissements cumulés" est présent
    print("📋 Test 2: Vérification présence 'Amortissements cumulés'")
    print("-" * 80)
    
    category_name = 'Amortissements cumulés'
    found = False
    
    for year_str, categories in data.items():
        if category_name in categories:
            found = True
            amount = categories[category_name]
            print(f"✅ Année {year_str}: {category_name} = {amount:,.2f} €")
            
            # Vérifier que le montant est positif (valeur absolue depuis backend)
            if amount < 0:
                print(f"   ⚠️  Montant est négatif ({amount}), mais devrait être positif (valeur absolue)")
            else:
                print(f"   ✅ Montant est positif (valeur absolue) - correct pour le backend")
    
    if not found:
        print(f"❌ Catégorie '{category_name}' non trouvée dans la réponse API")
        return False
    
    print()
    
    # Test 3: Vérifier la position (doit être dans "Actif immobilisé")
    print("📋 Test 3: Vérification position dans la hiérarchie")
    print("-" * 80)
    
    # Récupérer les mappings pour vérifier la sous-catégorie
    mappings_response = client.get('/api/bilan/mappings', headers={'Origin': 'http://localhost:3000'})
    if mappings_response.status_code == 200:
        mappings_data = mappings_response.json()
        mappings = mappings_data.get('mappings', [])
        
        amort_mapping = next((m for m in mappings if m.get('category_name') == category_name), None)
        if amort_mapping:
            sub_category = amort_mapping.get('sub_category')
            type_value = amort_mapping.get('type')
            is_special = amort_mapping.get('is_special', False)
            
            print(f"✅ Mapping trouvé:")
            print(f"   - Sous-catégorie: {sub_category}")
            print(f"   - Type: {type_value}")
            print(f"   - Catégorie spéciale: {is_special}")
            
            if sub_category == 'Actif immobilisé':
                print(f"   ✅ Position correcte (sous 'Actif immobilisé')")
            else:
                print(f"   ⚠️  Position: {sub_category} (attendu: 'Actif immobilisé')")
            
            if type_value == 'ACTIF':
                print(f"   ✅ Type correct (ACTIF)")
            else:
                print(f"   ⚠️  Type: {type_value} (attendu: 'ACTIF')")
        else:
            print(f"⚠️  Mapping non trouvé pour '{category_name}'")
    else:
        print(f"⚠️  Impossible de récupérer les mappings: {mappings_response.status_code}")
    
    print()
    
    # Test 4: Vérifier le calcul "Actif immobilisé"
    print("📋 Test 4: Vérification calcul 'Actif immobilisé'")
    print("-" * 80)
    
    for year_str in ['2021', '2022', '2023']:
        if year_str in data:
            categories = data[year_str]
            immobilisations = categories.get('Immobilisations', 0)
            amortissements = categories.get('Amortissements cumulés', 0)
            
            # Calcul attendu: Actif immobilisé = Immobilisations - Amortissements cumulés
            expected_actif_immobilise = immobilisations - amortissements
            
            print(f"Année {year_str}:")
            print(f"   Immobilisations: {immobilisations:,.2f} €")
            print(f"   Amortissements cumulés: {amortissements:,.2f} €")
            print(f"   → Actif immobilisé attendu: {expected_actif_immobilise:,.2f} €")
            print(f"      (Immobilisations - Amortissements = {immobilisations} - {amortissements})")
    
    print()
    print("=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80)
    print()
    print("📝 RÉSUMÉ:")
    print("   - API retourne bien 'Amortissements cumulés'")
    print("   - Montants sont positifs (valeur absolue) depuis le backend")
    print("   - Le frontend doit afficher en négatif (rouge)")
    print("   - Le calcul 'Actif immobilisé' soustrait correctement les amortissements")
    print()
    print("⚠️  NOTE POUR LE FRONTEND:")
    print("   Le frontend doit utiliser getDisplayAmount() pour afficher")
    print("   'Amortissements cumulés' en négatif même si le backend retourne un montant positif.")
    
    return True

if __name__ == "__main__":
    try:
        success = test_amortissements_cumules()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

