"""
Script de test pour vérifier que les endpoints Amortizations fonctionnent avec property_id.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script teste tous les endpoints d'amortissement pour vérifier :
- Que property_id est obligatoire
- Que le filtrage par property_id fonctionne
- Que l'isolation entre propriétés est respectée

Usage:
    python3 backend/scripts/test_amortizations_backend_phase_11_bis_3_1.py
"""

import sys
import requests
import json
from datetime import datetime, date
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Affiche un titre de section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_endpoint(method, endpoint, description, data=None, params=None, expected_status=200):
    """Teste un endpoint et affiche le résultat."""
    print(f"\n📌 {description}")
    print(f"   {method} {endpoint}")
    if params:
        print(f"   Params: {params}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2, default=str)}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=5)
        elif method == "POST":
            if data and isinstance(data, dict):
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", data=data, timeout=5)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, params=params, timeout=5)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", params=params, timeout=5)
        else:
            print(f"   ❌ Méthode {method} non supportée")
            return None, False
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ Succès (status attendu: {expected_status})")
            if response.content:
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(str(result)) < 500:
                        print(f"   Réponse: {json.dumps(result, indent=2, default=str)}")
                    else:
                        print(f"   Réponse: {type(result).__name__} ({len(result) if isinstance(result, (list, dict)) else 'N/A'} éléments)")
                except:
                    print(f"   Réponse: {response.text[:200]}")
            return response.json() if response.content else None, True
        else:
            print(f"   ❌ Erreur: Status {response.status_code} (attendu: {expected_status})")
            try:
                error = response.json()
                print(f"   Détail: {error.get('detail', response.text)}")
            except:
                print(f"   Détail: {response.text[:200]}")
            return None, False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur: Impossible de se connecter au serveur")
        print(f"   💡 Assurez-vous que le serveur backend est démarré: python3 -m uvicorn backend.api.main:app --reload --port 8000")
        return None, False
    except Exception as e:
        print(f"   ❌ Erreur: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def main():
    """Exécute tous les tests."""
    print("=" * 80)
    print("Tests Backend - Endpoints Amortizations avec property_id")
    print("=" * 80)
    print("\n⚠️  Vérification que le serveur backend est démarré...")
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Serveur backend accessible")
        else:
            print("❌ Serveur backend répond mais avec une erreur")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Serveur backend non accessible")
        print("   Démarrez-le avec: python3 -m uvicorn backend.api.main:app --reload --port 8000")
        sys.exit(1)
    
    print_section("1. Création de 2 propriétés de test")
    
    # Créer 2 propriétés de test
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prop1_name = f"Test Property Amort 1_{timestamp}"
    prop2_name = f"Test Property Amort 2_{timestamp}"
    
    prop1_data = {"name": prop1_name}
    prop2_data = {"name": prop2_name}
    
    prop1_response, success1 = test_endpoint("POST", "/properties", "Créer prop1", prop1_data, expected_status=201)
    if not success1 or not prop1_response:
        print("❌ ERREUR: Impossible de créer prop1")
        sys.exit(1)
    prop1_id = prop1_response.get("id")
    print(f"✅ prop1 créée: id={prop1_id}")
    
    prop2_response, success2 = test_endpoint("POST", "/properties", "Créer prop2", prop2_data, expected_status=201)
    if not success2 or not prop2_response:
        print("❌ ERREUR: Impossible de créer prop2")
        sys.exit(1)
    prop2_id = prop2_response.get("id")
    print(f"✅ prop2 créée: id={prop2_id}")
    
    print_section("2. Tests GET /api/amortization/types (avec property_id)")
    
    # Test sans property_id (doit échouer)
    _, success = test_endpoint("GET", "/amortization/types", "GET types SANS property_id (doit échouer)", expected_status=422)
    if success:
        print("✅ Validation property_id obligatoire fonctionne")
    
    # Test avec property_id=prop1
    types1, success = test_endpoint("GET", "/amortization/types", "GET types pour prop1", params={"property_id": prop1_id})
    if success and types1:
        print(f"✅ {types1.get('total', 0)} types retournés pour prop1")
    
    # Test avec property_id=prop2
    types2, success = test_endpoint("GET", "/amortization/types", "GET types pour prop2", params={"property_id": prop2_id})
    if success and types2:
        print(f"✅ {types2.get('total', 0)} types retournés pour prop2")
    
    print_section("3. Tests POST /api/amortization/types (création avec property_id)")
    
    # Créer 2 types pour prop1
    type1_data = {
        "property_id": prop1_id,
        "name": "Type Amort Prop1 Test 1",
        "level_2_value": "ammortissements",
        "level_1_values": ["Test Level 1"],
        "duration": 10.0
    }
    type1_response, success = test_endpoint("POST", "/amortization/types", "Créer type 1 pour prop1", type1_data, expected_status=201)
    if not success or not type1_response:
        print("❌ ERREUR: Impossible de créer type1")
        sys.exit(1)
    type1_id = type1_response.get("id")
    print(f"✅ Type1 créé: id={type1_id}, property_id={prop1_id}")
    
    type2_data = {
        "property_id": prop1_id,
        "name": "Type Amort Prop1 Test 2",
        "level_2_value": "ammortissements",
        "level_1_values": ["Test Level 1"],
        "duration": 5.0
    }
    type2_response, success = test_endpoint("POST", "/amortization/types", "Créer type 2 pour prop1", type2_data, expected_status=201)
    if not success or not type2_response:
        print("❌ ERREUR: Impossible de créer type2")
        sys.exit(1)
    type2_id = type2_response.get("id")
    print(f"✅ Type2 créé: id={type2_id}, property_id={prop1_id}")
    
    # Créer 1 type pour prop2
    type3_data = {
        "property_id": prop2_id,
        "name": "Type Amort Prop2 Test 1",
        "level_2_value": "ammortissements",
        "level_1_values": ["Test Level 1"],
        "duration": 7.0
    }
    type3_response, success = test_endpoint("POST", "/amortization/types", "Créer type 1 pour prop2", type3_data, expected_status=201)
    if not success or not type3_response:
        print("❌ ERREUR: Impossible de créer type3")
        sys.exit(1)
    type3_id = type3_response.get("id")
    print(f"✅ Type3 créé: id={type3_id}, property_id={prop2_id}")
    
    print_section("4. Tests GET /api/amortization/types (vérification isolation)")
    
    # Vérifier que prop1 voit uniquement ses 2 types
    types1, success = test_endpoint("GET", "/amortization/types", "GET types pour prop1 (doit retourner 2 types)", params={"property_id": prop1_id})
    if success and types1:
        count1 = types1.get('total', 0)
        if count1 == 2:
            print(f"✅ Isolation OK: prop1 voit {count1} types (attendu: 2)")
        else:
            print(f"❌ Isolation KO: prop1 voit {count1} types (attendu: 2)")
    
    # Vérifier que prop2 voit uniquement son 1 type
    types2, success = test_endpoint("GET", "/amortization/types", "GET types pour prop2 (doit retourner 1 type)", params={"property_id": prop2_id})
    if success and types2:
        count2 = types2.get('total', 0)
        if count2 == 1:
            print(f"✅ Isolation OK: prop2 voit {count2} types (attendu: 1)")
        else:
            print(f"❌ Isolation KO: prop2 voit {count2} types (attendu: 1)")
    
    print_section("5. Tests GET /api/amortization/types/{id} (avec property_id)")
    
    # Test sans property_id (doit échouer)
    _, success = test_endpoint("GET", f"/amortization/types/{type1_id}", "GET type SANS property_id (doit échouer)", expected_status=422)
    if success:
        print("✅ Validation property_id obligatoire fonctionne")
    
    # Test avec property_id correct
    type1_get, success = test_endpoint("GET", f"/amortization/types/{type1_id}", "GET type1 avec property_id=prop1", params={"property_id": prop1_id})
    if success and type1_get:
        print(f"✅ Type1 récupéré: {type1_get.get('name')}")
    
    # Test cross-property (doit retourner 404)
    _, success = test_endpoint("GET", f"/amortization/types/{type1_id}", "GET type1 avec property_id=prop2 (cross-property, doit échouer)", params={"property_id": prop2_id}, expected_status=404)
    if success:
        print("✅ Protection cross-property fonctionne (404 retourné)")
    
    print_section("6. Tests PUT /api/amortization/types/{id} (avec property_id)")
    
    # Modifier type1 avec property_id correct
    update_data = {"name": "Type Amort Prop1 Test 1 MODIFIÉ"}
    type1_updated, success = test_endpoint("PUT", f"/amortization/types/{type1_id}", "PUT type1 avec property_id=prop1", update_data, params={"property_id": prop1_id})
    if success and type1_updated:
        print(f"✅ Type1 modifié: {type1_updated.get('name')}")
    
    # Test cross-property (doit retourner 404)
    _, success = test_endpoint("PUT", f"/amortization/types/{type1_id}", "PUT type1 avec property_id=prop2 (cross-property, doit échouer)", update_data, params={"property_id": prop2_id}, expected_status=404)
    if success:
        print("✅ Protection cross-property fonctionne (404 retourné)")
    
    print_section("7. Tests GET /api/amortization/types/{id}/amount (avec property_id)")
    
    # Test avec property_id correct
    amount_response, success = test_endpoint("GET", f"/amortization/types/{type1_id}/amount", "GET amount pour type1", params={"property_id": prop1_id})
    if success and amount_response:
        print(f"✅ Amount récupéré: {amount_response.get('amount', 0)}")
    
    print_section("8. Tests GET /api/amortization/results (avec property_id)")
    
    # Test sans property_id (doit échouer)
    _, success = test_endpoint("GET", "/amortization/results", "GET results SANS property_id (doit échouer)", expected_status=422)
    if success:
        print("✅ Validation property_id obligatoire fonctionne")
    
    # Test avec property_id
    results, success = test_endpoint("GET", "/amortization/results", "GET results pour prop1", params={"property_id": prop1_id})
    if success and results:
        print(f"✅ Results récupérés pour prop1")
    
    print_section("9. Tests POST /api/amortization/recalculate (avec property_id)")
    
    # Test sans property_id (doit échouer)
    _, success = test_endpoint("POST", "/amortization/recalculate", "POST recalculate SANS property_id (doit échouer)", expected_status=422)
    if success:
        print("✅ Validation property_id obligatoire fonctionne")
    
    # Test avec property_id
    recalc_response, success = test_endpoint("POST", "/amortization/recalculate", "POST recalculate pour prop1", data={"property_id": prop1_id})
    if success and recalc_response:
        print(f"✅ Recalcul terminé: {recalc_response.get('results_created', 0)} résultats créés")
    
    print_section("10. Nettoyage - Suppression des propriétés de test")
    
    # Supprimer les propriétés (cascade supprimera les types)
    test_endpoint("DELETE", f"/properties/{prop1_id}", "Supprimer prop1", expected_status=204)
    test_endpoint("DELETE", f"/properties/{prop2_id}", "Supprimer prop2", expected_status=204)
    
    print("\n" + "=" * 80)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("=" * 80)

if __name__ == "__main__":
    main()
