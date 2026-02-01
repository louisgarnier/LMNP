"""
Test d'isolation pour l'onglet Bilan - Phase 11 bis
Vérifie que les données de bilan sont correctement isolées par propriété.

⚠️ Before running, read: docs/workflow/BEST_PRACTICES.md
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def create_property(name: str) -> dict:
    """Créer une propriété."""
    response = requests.post(
        f"{BASE_URL}/api/properties",
        json={"name": name, "address": f"Adresse {name}"}
    )
    if response.status_code != 200 and response.status_code != 201:
        print(f"❌ Erreur création propriété {name}: {response.status_code} {response.text}")
        return None
    return response.json()


def delete_property(property_id: int) -> bool:
    """Supprimer une propriété."""
    response = requests.delete(f"{BASE_URL}/api/properties/{property_id}")
    return response.status_code == 204 or response.status_code == 200


def get_properties() -> list:
    """Récupérer toutes les propriétés."""
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code == 200:
        return response.json()
    return []


def test_bilan_isolation():
    """Test principal d'isolation des données Bilan."""
    print("=" * 80)
    print("🧪 TEST D'ISOLATION - ONGLET BILAN")
    print("=" * 80)
    
    # Créer deux propriétés de test
    print("\n📦 Création des propriétés de test...")
    prop1 = create_property("TestBilan_Prop1")
    prop2 = create_property("TestBilan_Prop2")
    
    if not prop1 or not prop2:
        print("❌ Échec de création des propriétés de test")
        return False
    
    prop1_id = prop1["id"]
    prop2_id = prop2["id"]
    print(f"  ✅ Propriété 1 créée: id={prop1_id}")
    print(f"  ✅ Propriété 2 créée: id={prop2_id}")
    
    try:
        success = True
        
        # ========== TEST MAPPINGS ==========
        print("\n" + "=" * 40)
        print("📋 TEST: Mappings Bilan")
        print("=" * 40)
        
        # Créer un mapping pour prop1
        mapping1_data = {
            "property_id": prop1_id,
            "category_name": "Test Immobilisations Prop1",
            "type": "ACTIF",
            "sub_category": "Actif immobilisé",
            "level_1_values": json.dumps(["LOYERS"]),
            "is_special": False
        }
        resp = requests.post(f"{BASE_URL}/api/bilan/mappings", json=mapping1_data)
        if resp.status_code == 201:
            mapping1_id = resp.json()["id"]
            print(f"  ✅ Mapping créé pour prop1: id={mapping1_id}")
        else:
            print(f"  ❌ Erreur création mapping prop1: {resp.status_code} {resp.text}")
            success = False
            mapping1_id = None
        
        # Créer un mapping pour prop2
        mapping2_data = {
            "property_id": prop2_id,
            "category_name": "Test Immobilisations Prop2",
            "type": "PASSIF",
            "sub_category": "Dettes financières",
            "level_1_values": json.dumps(["CHARGES"]),
            "is_special": False
        }
        resp = requests.post(f"{BASE_URL}/api/bilan/mappings", json=mapping2_data)
        if resp.status_code == 201:
            mapping2_id = resp.json()["id"]
            print(f"  ✅ Mapping créé pour prop2: id={mapping2_id}")
        else:
            print(f"  ❌ Erreur création mapping prop2: {resp.status_code} {resp.text}")
            success = False
            mapping2_id = None
        
        # Vérifier que prop1 ne voit que son mapping
        resp = requests.get(f"{BASE_URL}/api/bilan/mappings?property_id={prop1_id}")
        if resp.status_code == 200:
            mappings = resp.json()["items"]
            prop1_categories = [m["category_name"] for m in mappings]
            if "Test Immobilisations Prop1" in prop1_categories and "Test Immobilisations Prop2" not in prop1_categories:
                print(f"  ✅ Isolation mappings prop1: OK ({len(mappings)} mappings)")
            else:
                print(f"  ❌ Isolation mappings prop1: ÉCHEC - Catégories trouvées: {prop1_categories}")
                success = False
        else:
            print(f"  ❌ Erreur récupération mappings prop1: {resp.status_code}")
            success = False
        
        # Vérifier que prop2 ne voit que son mapping
        resp = requests.get(f"{BASE_URL}/api/bilan/mappings?property_id={prop2_id}")
        if resp.status_code == 200:
            mappings = resp.json()["items"]
            prop2_categories = [m["category_name"] for m in mappings]
            if "Test Immobilisations Prop2" in prop2_categories and "Test Immobilisations Prop1" not in prop2_categories:
                print(f"  ✅ Isolation mappings prop2: OK ({len(mappings)} mappings)")
            else:
                print(f"  ❌ Isolation mappings prop2: ÉCHEC - Catégories trouvées: {prop2_categories}")
                success = False
        else:
            print(f"  ❌ Erreur récupération mappings prop2: {resp.status_code}")
            success = False
        
        # ========== TEST CONFIG ==========
        print("\n" + "=" * 40)
        print("⚙️ TEST: Config Bilan")
        print("=" * 40)
        
        # Créer/modifier config pour prop1
        config1_data = {"property_id": prop1_id, "level_3_values": json.dumps(["PROP1_L3"])}
        resp = requests.put(f"{BASE_URL}/api/bilan/config", json=config1_data)
        if resp.status_code == 200:
            print(f"  ✅ Config mise à jour pour prop1")
        else:
            print(f"  ❌ Erreur config prop1: {resp.status_code} {resp.text}")
            success = False
        
        # Créer/modifier config pour prop2
        config2_data = {"property_id": prop2_id, "level_3_values": json.dumps(["PROP2_L3"])}
        resp = requests.put(f"{BASE_URL}/api/bilan/config", json=config2_data)
        if resp.status_code == 200:
            print(f"  ✅ Config mise à jour pour prop2")
        else:
            print(f"  ❌ Erreur config prop2: {resp.status_code} {resp.text}")
            success = False
        
        # Vérifier que prop1 a sa config
        resp = requests.get(f"{BASE_URL}/api/bilan/config?property_id={prop1_id}")
        if resp.status_code == 200:
            config = resp.json()
            if "PROP1_L3" in config.get("level_3_values", "") and "PROP2_L3" not in config.get("level_3_values", ""):
                print(f"  ✅ Isolation config prop1: OK")
            else:
                print(f"  ❌ Isolation config prop1: ÉCHEC - level_3_values: {config.get('level_3_values')}")
                success = False
        else:
            print(f"  ❌ Erreur récupération config prop1: {resp.status_code}")
            success = False
        
        # Vérifier que prop2 a sa config
        resp = requests.get(f"{BASE_URL}/api/bilan/config?property_id={prop2_id}")
        if resp.status_code == 200:
            config = resp.json()
            if "PROP2_L3" in config.get("level_3_values", "") and "PROP1_L3" not in config.get("level_3_values", ""):
                print(f"  ✅ Isolation config prop2: OK")
            else:
                print(f"  ❌ Isolation config prop2: ÉCHEC - level_3_values: {config.get('level_3_values')}")
                success = False
        else:
            print(f"  ❌ Erreur récupération config prop2: {resp.status_code}")
            success = False
        
        # ========== TEST CALCULATE ==========
        print("\n" + "=" * 40)
        print("🧮 TEST: Calcul Bilan")
        print("=" * 40)
        
        # Calculer le bilan pour prop1
        resp = requests.get(f"{BASE_URL}/api/bilan/calculate?property_id={prop1_id}&years=2023")
        if resp.status_code == 200:
            print(f"  ✅ Calcul bilan prop1: OK")
        else:
            print(f"  ❌ Erreur calcul bilan prop1: {resp.status_code} {resp.text}")
            success = False
        
        # Calculer le bilan pour prop2
        resp = requests.get(f"{BASE_URL}/api/bilan/calculate?property_id={prop2_id}&years=2023")
        if resp.status_code == 200:
            print(f"  ✅ Calcul bilan prop2: OK")
        else:
            print(f"  ❌ Erreur calcul bilan prop2: {resp.status_code} {resp.text}")
            success = False
        
        # ========== RÉSULTAT FINAL ==========
        print("\n" + "=" * 80)
        if success:
            print("✅ TOUS LES TESTS D'ISOLATION BILAN RÉUSSIS")
        else:
            print("❌ CERTAINS TESTS D'ISOLATION BILAN ONT ÉCHOUÉ")
        print("=" * 80)
        
        return success
        
    finally:
        # Nettoyage
        print("\n🧹 Nettoyage des propriétés de test...")
        if prop1_id:
            delete_property(prop1_id)
            print(f"  ✅ Propriété {prop1_id} supprimée")
        if prop2_id:
            delete_property(prop2_id)
            print(f"  ✅ Propriété {prop2_id} supprimée")


if __name__ == "__main__":
    success = test_bilan_isolation()
    sys.exit(0 if success else 1)
