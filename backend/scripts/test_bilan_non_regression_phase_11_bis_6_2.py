"""
Test de non-régression pour l'onglet Bilan - Phase 11 bis
Vérifie que toutes les fonctionnalités existantes fonctionnent correctement.

⚠️ Before running, read: docs/workflow/BEST_PRACTICES.md
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def get_first_property() -> dict:
    """Récupérer la première propriété."""
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code == 200:
        data = response.json()
        # Handle both list and object with 'items' key
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict):
            items = data.get("items", data.get("properties", []))
            if isinstance(items, list) and len(items) > 0:
                return items[0]
    return None


def test_bilan_non_regression():
    """Test de non-régression pour les fonctionnalités Bilan."""
    print("=" * 80)
    print("🧪 TEST DE NON-RÉGRESSION - ONGLET BILAN")
    print("=" * 80)
    
    # Récupérer la première propriété
    prop = get_first_property()
    if not prop:
        print("❌ Aucune propriété trouvée. Veuillez créer une propriété d'abord.")
        return False
    
    property_id = prop["id"]
    print(f"\n📦 Utilisation de la propriété: {prop['name']} (id={property_id})")
    
    success = True
    created_mapping_id = None
    
    try:
        # ========== TEST MAPPINGS CRUD ==========
        print("\n" + "=" * 40)
        print("📋 TEST: CRUD Mappings Bilan")
        print("=" * 40)
        
        # GET /api/bilan/mappings
        print("\n  🔹 GET /api/bilan/mappings")
        resp = requests.get(f"{BASE_URL}/api/bilan/mappings?property_id={property_id}")
        if resp.status_code == 200:
            mappings = resp.json()
            print(f"    ✅ Liste des mappings: {mappings['total']} mappings")
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # POST /api/bilan/mappings
        print("\n  🔹 POST /api/bilan/mappings")
        new_mapping = {
            "property_id": property_id,
            "category_name": "Test Non-Regression Bilan",
            "type": "ACTIF",
            "sub_category": "Actif immobilisé",
            "level_1_values": json.dumps(["TEST_L1"]),
            "is_special": False
        }
        resp = requests.post(f"{BASE_URL}/api/bilan/mappings", json=new_mapping)
        if resp.status_code == 201:
            created_mapping_id = resp.json()["id"]
            print(f"    ✅ Mapping créé: id={created_mapping_id}")
        else:
            print(f"    ❌ Erreur création: {resp.status_code} {resp.text}")
            success = False
        
        # GET /api/bilan/mappings/{id}
        if created_mapping_id:
            print("\n  🔹 GET /api/bilan/mappings/{id}")
            resp = requests.get(f"{BASE_URL}/api/bilan/mappings/{created_mapping_id}?property_id={property_id}")
            if resp.status_code == 200:
                mapping = resp.json()
                print(f"    ✅ Mapping récupéré: {mapping['category_name']}")
            else:
                print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
                success = False
        
        # PUT /api/bilan/mappings/{id}
        if created_mapping_id:
            print("\n  🔹 PUT /api/bilan/mappings/{id}")
            update_data = {"category_name": "Test Non-Regression Bilan Updated"}
            resp = requests.put(
                f"{BASE_URL}/api/bilan/mappings/{created_mapping_id}?property_id={property_id}",
                json=update_data
            )
            if resp.status_code == 200:
                updated = resp.json()
                if updated["category_name"] == "Test Non-Regression Bilan Updated":
                    print(f"    ✅ Mapping mis à jour: {updated['category_name']}")
                else:
                    print(f"    ❌ Valeur non mise à jour correctement")
                    success = False
            else:
                print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
                success = False
        
        # ========== TEST CONFIG ==========
        print("\n" + "=" * 40)
        print("⚙️ TEST: Config Bilan")
        print("=" * 40)
        
        # GET /api/bilan/config
        print("\n  🔹 GET /api/bilan/config")
        resp = requests.get(f"{BASE_URL}/api/bilan/config?property_id={property_id}")
        if resp.status_code == 200:
            config = resp.json()
            print(f"    ✅ Config récupérée: id={config['id']}")
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # PUT /api/bilan/config
        print("\n  🔹 PUT /api/bilan/config")
        update_config = {
            "property_id": property_id,
            "level_3_values": json.dumps(["TEST_L3_VALUE"])
        }
        resp = requests.put(f"{BASE_URL}/api/bilan/config", json=update_config)
        if resp.status_code == 200:
            config = resp.json()
            if "TEST_L3_VALUE" in config.get("level_3_values", ""):
                print(f"    ✅ Config mise à jour")
            else:
                print(f"    ❌ Valeur non mise à jour correctement")
                success = False
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # ========== TEST CALCULATE ==========
        print("\n" + "=" * 40)
        print("🧮 TEST: Calcul Bilan")
        print("=" * 40)
        
        # GET /api/bilan/calculate (multiple years)
        print("\n  🔹 GET /api/bilan/calculate (multiple years)")
        resp = requests.get(f"{BASE_URL}/api/bilan/calculate?property_id={property_id}&years=2022,2023")
        if resp.status_code == 200:
            result = resp.json()
            years = result.get("years", [])
            print(f"    ✅ Calcul multi-années: {years}")
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # POST /api/bilan/calculate (single year)
        print("\n  🔹 POST /api/bilan/calculate (single year)")
        calc_request = {
            "property_id": property_id,
            "year": 2023,
            "selected_level_3_values": None
        }
        resp = requests.post(f"{BASE_URL}/api/bilan/calculate", json=calc_request)
        if resp.status_code == 200:
            result = resp.json()
            print(f"    ✅ Calcul année 2023: ACTIF={result.get('actif_total', 0):.2f}, PASSIF={result.get('passif_total', 0):.2f}")
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # ========== TEST GET BILAN DATA ==========
        print("\n" + "=" * 40)
        print("📊 TEST: Données Bilan")
        print("=" * 40)
        
        # GET /api/bilan
        print("\n  🔹 GET /api/bilan")
        resp = requests.get(f"{BASE_URL}/api/bilan?property_id={property_id}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    ✅ Données bilan: {data.get('total', 0)} entrées")
        else:
            print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
            success = False
        
        # DELETE /api/bilan/mappings/{id}
        if created_mapping_id:
            print("\n  🔹 DELETE /api/bilan/mappings/{id}")
            resp = requests.delete(f"{BASE_URL}/api/bilan/mappings/{created_mapping_id}?property_id={property_id}")
            if resp.status_code == 204 or resp.status_code == 200:
                print(f"    ✅ Mapping supprimé: id={created_mapping_id}")
                created_mapping_id = None  # Marqué comme supprimé
            else:
                print(f"    ❌ Erreur: {resp.status_code} {resp.text}")
                success = False
        
        # ========== RÉSULTAT FINAL ==========
        print("\n" + "=" * 80)
        if success:
            print("✅ TOUS LES TESTS DE NON-RÉGRESSION BILAN RÉUSSIS")
        else:
            print("❌ CERTAINS TESTS DE NON-RÉGRESSION BILAN ONT ÉCHOUÉ")
        print("=" * 80)
        
        return success
        
    finally:
        # Nettoyage si nécessaire
        if created_mapping_id:
            print(f"\n🧹 Nettoyage: suppression du mapping {created_mapping_id}")
            requests.delete(f"{BASE_URL}/api/bilan/mappings/{created_mapping_id}?property_id={property_id}")


if __name__ == "__main__":
    success = test_bilan_non_regression()
    sys.exit(0 if success else 1)
