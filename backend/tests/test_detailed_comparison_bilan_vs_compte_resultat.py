"""
Comparaison détaillée : Bilan vs Compte de Résultat
Compare tous les aspects techniques pour identifier les différences.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_detailed_comparison_bilan_vs_compte_resultat.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, CompteResultatMapping
from backend.api.services.bilan_service import calculate_bilan, get_mappings as get_bilan_mappings
from backend.api.services.compte_resultat_service import calculate_amounts_by_category_and_year, get_mappings as get_cr_mappings
import inspect

client = TestClient(app)
db = SessionLocal()


def compare_models():
    """Compare les modèles de données."""
    print("=" * 80)
    print("1. MODÈLES DE DONNÉES (Database Models)")
    print("=" * 80)
    print()
    
    # Récupérer un mapping de chaque type
    bilan_mapping = db.query(BilanMapping).first()
    cr_mapping = db.query(CompteResultatMapping).first()
    
    print("BILAN MAPPING:")
    if bilan_mapping:
        print(f"  - category_name: {bilan_mapping.category_name}")
        print(f"  - type: {bilan_mapping.type}")
        print(f"  - sub_category: {bilan_mapping.sub_category}")
        print(f"  - level_1_values: {bilan_mapping.level_1_values}")
        print(f"  - is_special: {bilan_mapping.is_special}")
        print(f"  - special_source: {bilan_mapping.special_source}")
        print(f"  - amortization_view_id: {bilan_mapping.amortization_view_id}")
        print()
        print("  Champs présents: category_name, type, sub_category, level_1_values, is_special, special_source, amortization_view_id")
    else:
        print("  ❌ Aucun mapping trouvé")
    print()
    
    print("COMPTE RÉSULTAT MAPPING:")
    if cr_mapping:
        print(f"  - category_name: {cr_mapping.category_name}")
        print(f"  - level_1_values: {cr_mapping.level_1_values}")
        print(f"  - level_2_values: {cr_mapping.level_2_values}")
        print(f"  - level_3_values: {cr_mapping.level_3_values}")
        print(f"  - amortization_view_id: {cr_mapping.amortization_view_id}")
        print(f"  - selected_loan_ids: {cr_mapping.selected_loan_ids}")
        print()
        print("  Champs présents: category_name, level_1_values, level_2_values, level_3_values, amortization_view_id, selected_loan_ids")
    else:
        print("  ❌ Aucun mapping trouvé")
    print()
    
    print("DIFFÉRENCES:")
    print("  ✅ Bilan a: type, sub_category, is_special, special_source")
    print("  ❌ Compte de résultat n'a PAS: type, sub_category, is_special, special_source")
    print("  ✅ Compte de résultat a: level_2_values, level_3_values, selected_loan_ids")
    print("  ❌ Bilan n'a PAS: level_2_values, level_3_values, selected_loan_ids")
    print()


def compare_services():
    """Compare les services de calcul."""
    print("=" * 80)
    print("2. SERVICES DE CALCUL")
    print("=" * 80)
    print()
    
    # Bilan service
    print("BILAN SERVICE (bilan_service.py):")
    bilan_func = calculate_bilan
    bilan_sig = inspect.signature(bilan_func)
    print(f"  Fonction: calculate_bilan")
    print(f"  Paramètres: {list(bilan_sig.parameters.keys())}")
    print(f"  Retourne: Dict avec categories, sub_category_totals, type_totals, equilibre")
    
    # Tester l'appel
    try:
        mappings = get_bilan_mappings(db)
        if mappings:
            result = calculate_bilan(2021, mappings, None, db)
            print(f"  ✅ Test réussi: {len(result.get('categories', {}))} catégorie(s) calculée(s)")
            print(f"     Sub-catégories: {len(result.get('sub_category_totals', {}))}")
            print(f"     Types: {len(result.get('type_totals', {}))}")
        else:
            print("  ⚠️  Aucun mapping pour tester")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    print()
    
    # Compte de résultat service
    print("COMPTE RÉSULTAT SERVICE (compte_resultat_service.py):")
    cr_func = calculate_amounts_by_category_and_year
    cr_sig = inspect.signature(cr_func)
    print(f"  Fonction: calculate_amounts_by_category_and_year")
    print(f"  Paramètres: {list(cr_sig.parameters.keys())}")
    print(f"  Retourne: Dict[int, Dict[str, float]] (year -> category -> amount)")
    
    # Tester l'appel
    try:
        result = calculate_amounts_by_category_and_year([2021], db)
        print(f"  ✅ Test réussi: {len(result)} année(s) calculée(s)")
        if result:
            year_data = list(result.values())[0]
            print(f"     Catégories pour 2021: {len(year_data)}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    print()
    
    print("DIFFÉRENCES:")
    print("  ✅ Bilan: Calcule pour 1 année, retourne structure hiérarchique complète")
    print("  ✅ Compte de résultat: Calcule pour plusieurs années, retourne dict simple")
    print()


def compare_api_models():
    """Compare les modèles Pydantic pour l'API."""
    print("=" * 80)
    print("3. MODÈLES PYDANTIC POUR L'API")
    print("=" * 80)
    print()
    
    from backend.api.models import BilanMappingBase, CompteResultatMappingBase
    
    print("BILAN MAPPING BASE:")
    bilan_fields = BilanMappingBase.model_fields
    for field_name, field_info in bilan_fields.items():
        print(f"  - {field_name}: {field_info.annotation}")
    print()
    
    print("COMPTE RÉSULTAT MAPPING BASE:")
    cr_fields = CompteResultatMappingBase.model_fields
    for field_name, field_info in cr_fields.items():
        print(f"  - {field_name}: {field_info.annotation}")
    print()
    
    print("DIFFÉRENCES:")
    bilan_field_names = set(bilan_fields.keys())
    cr_field_names = set(cr_fields.keys())
    only_bilan = bilan_field_names - cr_field_names
    only_cr = cr_field_names - bilan_field_names
    common = bilan_field_names & cr_field_names
    
    print(f"  Champs uniquement dans Bilan: {only_bilan}")
    print(f"  Champs uniquement dans Compte de résultat: {only_cr}")
    print(f"  Champs communs: {common}")
    print()


def compare_endpoints():
    """Compare les endpoints API."""
    print("=" * 80)
    print("4. ENDPOINTS API")
    print("=" * 80)
    print()
    
    print("BILAN ENDPOINTS:")
    bilan_endpoints = [
        ("GET", "/api/bilan/mappings", "Récupère tous les mappings"),
        ("GET", "/api/bilan/mappings/{id}", "Récupère un mapping"),
        ("POST", "/api/bilan/mappings", "Crée un mapping"),
        ("PUT", "/api/bilan/mappings/{id}", "Met à jour un mapping"),
        ("DELETE", "/api/bilan/mappings/{id}", "Supprime un mapping"),
        ("GET", "/api/bilan/calculate", "Calcule à la volée (NOUVEAU)"),
        ("POST", "/api/bilan/generate", "Génère et stocke (ANCIEN)"),
        ("GET", "/api/bilan", "Récupère données stockées (ANCIEN)"),
    ]
    
    for method, path, desc in bilan_endpoints:
        print(f"  {method:6} {path:40} - {desc}")
    print()
    
    print("COMPTE RÉSULTAT ENDPOINTS:")
    cr_endpoints = [
        ("GET", "/api/compte-resultat/mappings", "Récupère tous les mappings"),
        ("GET", "/api/compte-resultat/mappings/{id}", "Récupère un mapping"),
        ("POST", "/api/compte-resultat/mappings", "Crée un mapping"),
        ("PUT", "/api/compte-resultat/mappings/{id}", "Met à jour un mapping"),
        ("DELETE", "/api/compte-resultat/mappings/{id}", "Supprime un mapping"),
        ("GET", "/api/compte-resultat/calculate", "Calcule à la volée"),
        ("GET", "/api/compte-resultat/data", "Récupère données stockées (optionnel)"),
    ]
    
    for method, path, desc in cr_endpoints:
        print(f"  {method:6} {path:40} - {desc}")
    print()
    
    print("DIFFÉRENCES:")
    print("  ✅ Bilan a: /api/bilan/generate (POST) - génération avec stockage")
    print("  ❌ Compte de résultat n'a PAS: endpoint generate")
    print("  ✅ Les deux ont: /calculate (GET) - calcul à la volée")
    print()


def compare_api_client():
    """Compare l'API client frontend."""
    print("=" * 80)
    print("5. API CLIENT FRONTEND")
    print("=" * 80)
    print()
    
    # Lire les fichiers
    try:
        with open('frontend/src/api/client.ts', 'r') as f:
            client_content = f.read()
        
        # Extraire les méthodes pour bilan
        bilan_methods = []
        in_bilan_api = False
        for line in client_content.split('\n'):
            if 'export const bilanAPI' in line:
                in_bilan_api = True
            elif in_bilan_api and line.strip().startswith('};'):
                break
            elif in_bilan_api and ':' in line and 'async' in line:
                method_name = line.split(':')[0].strip()
                if method_name and not method_name.startswith('//'):
                    bilan_methods.append(method_name)
        
        print("BILAN API CLIENT:")
        for method in bilan_methods:
            print(f"  - {method}")
        print()
        
        # Extraire les méthodes pour compte de résultat
        cr_methods = []
        in_cr_api = False
        for line in client_content.split('\n'):
            if 'export const compteResultatAPI' in line:
                in_cr_api = True
            elif in_cr_api and line.strip().startswith('};'):
                break
            elif in_cr_api and ':' in line and 'async' in line:
                method_name = line.split(':')[0].strip()
                if method_name and not method_name.startswith('//'):
                    cr_methods.append(method_name)
        
        print("COMPTE RÉSULTAT API CLIENT:")
        for method in cr_methods:
            print(f"  - {method}")
        print()
        
        print("DIFFÉRENCES:")
        only_bilan = set(bilan_methods) - set(cr_methods)
        only_cr = set(cr_methods) - set(bilan_methods)
        common = set(bilan_methods) & set(cr_methods)
        
        print(f"  Méthodes uniquement dans Bilan: {only_bilan}")
        print(f"  Méthodes uniquement dans Compte de résultat: {only_cr}")
        print(f"  Méthodes communes: {common}")
        print()
        
    except Exception as e:
        print(f"  ❌ Erreur lors de la lecture: {e}")
        print()


def test_calculate_endpoints():
    """Test les endpoints calculate."""
    print("=" * 80)
    print("6. TEST DES ENDPOINTS CALCULATE")
    print("=" * 80)
    print()
    
    years = [2021, 2022, 2023]
    years_param = ",".join(str(y) for y in years)
    
    # Test Bilan
    print("TEST BILAN /api/bilan/calculate:")
    try:
        response = client.get(f"/api/bilan/calculate?years={years_param}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réussi: {len(data)} année(s)")
            for year, categories in sorted(data.items()):
                print(f"     {year}: {len(categories)} catégorie(s)")
        else:
            print(f"  ❌ Erreur: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    print()
    
    # Test Compte de résultat
    print("TEST COMPTE RÉSULTAT /api/compte-resultat/calculate:")
    try:
        response = client.get(f"/api/compte-resultat/calculate?years={years_param}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Réussi: {len(data)} année(s)")
            for year, categories in sorted(data.items()):
                print(f"     {year}: {len(categories)} catégorie(s)")
        else:
            print(f"  ❌ Erreur: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    print()


def compare_frontend_components():
    """Compare les composants frontend."""
    print("=" * 80)
    print("7. COMPOSANTS FRONTEND")
    print("=" * 80)
    print()
    
    try:
        # Lire BilanTable
        with open('frontend/src/components/BilanTable.tsx', 'r') as f:
            bilan_table = f.read()
        
        # Lire CompteResultatTable
        with open('frontend/src/components/CompteResultatTable.tsx', 'r') as f:
            cr_table = f.read()
        
        print("BILAN TABLE:")
        if 'calculateAmounts' in bilan_table:
            print("  ✅ Utilise calculateAmounts()")
        else:
            print("  ❌ N'utilise PAS calculateAmounts()")
        
        if 'getBilan' in bilan_table:
            print("  ⚠️  Utilise aussi getBilan() (ancien)")
        
        if 'generate' in bilan_table:
            print("  ⚠️  Utilise generate() (ancien)")
        print()
        
        print("COMPTE RÉSULTAT TABLE:")
        if 'calculateAmounts' in cr_table:
            print("  ✅ Utilise calculateAmounts()")
        else:
            print("  ❌ N'utilise PAS calculateAmounts()")
        
        if 'generate' in cr_table:
            print("  ⚠️  Utilise generate()")
        print()
        
        print("DIFFÉRENCES:")
        if 'calculateAmounts' in bilan_table and 'calculateAmounts' in cr_table:
            print("  ✅ Les deux utilisent calculateAmounts()")
        else:
            print("  ❌ Différence dans l'utilisation de calculateAmounts()")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    print()


def main():
    """Fonction principale."""
    print("=" * 80)
    print("COMPARAISON DÉTAILLÉE : BILAN vs COMPTE DE RÉSULTAT")
    print("=" * 80)
    print()
    
    compare_models()
    compare_services()
    compare_api_models()
    compare_endpoints()
    compare_api_client()
    test_calculate_endpoints()
    compare_frontend_components()
    
    print("=" * 80)
    print("RÉSUMÉ DES DIFFÉRENCES")
    print("=" * 80)
    print()
    print("1. MODÈLES DE DONNÉES:")
    print("   - Bilan a: type, sub_category, is_special, special_source")
    print("   - Compte de résultat a: level_2_values, level_3_values, selected_loan_ids")
    print()
    print("2. SERVICES:")
    print("   - Bilan: calculate_bilan(year, mappings, ...) → structure hiérarchique")
    print("   - Compte de résultat: calculate_amounts_by_category_and_year(years, ...) → dict simple")
    print()
    print("3. ENDPOINTS:")
    print("   - Les deux ont maintenant /calculate (GET)")
    print("   - Bilan a aussi /generate (POST) et /bilan (GET) pour compatibilité")
    print()
    print("4. FRONTEND:")
    print("   - Les deux devraient utiliser calculateAmounts()")
    print("   - Vérifier que BilanTable utilise bien calculateAmounts() et pas getBilan()")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Erreur: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

