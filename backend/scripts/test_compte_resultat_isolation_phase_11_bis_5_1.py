"""
Test d'isolation du Compte de Résultat - Phase 11 bis 5.1

Ce script vérifie l'isolation des données entre propriétés pour le Compte de Résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def create_test_properties():
    """Créer deux propriétés de test."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    props = []
    for i in [1, 2]:
        name = f"Test Compte Resultat {i}_{timestamp}"
        response = requests.post(f"{BASE_URL}/api/properties", json={"name": name})
        if response.status_code in [200, 201]:
            props.append(response.json())
            log_success(f"Propriété {i} créée: {props[-1]['id']} - {name}")
        else:
            log_error(f"Impossible de créer la propriété {i}: {response.status_code}")
            return None
    return props

def test_compte_resultat_mappings_isolation(prop1_id, prop2_id):
    """Tester l'isolation des mappings du Compte de Résultat."""
    log_info("=== Test isolation des mappings ===")
    
    # Créer un mapping pour prop1
    mapping1_data = {
        "category_name": "Test Catégorie Prop1",
        "type": "Produits d'exploitation",
        "level_1_values": '["TEST1", "TEST2"]',
        "property_id": prop1_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/mappings", json=mapping1_data)
    if response.status_code != 201:
        log_error(f"Impossible de créer le mapping pour prop1: {response.status_code} {response.text}")
        return False
    mapping1 = response.json()
    log_success(f"Mapping créé pour prop1: {mapping1['id']}")
    
    # Créer un mapping pour prop2
    mapping2_data = {
        "category_name": "Test Catégorie Prop2",
        "type": "Charges d'exploitation",
        "level_1_values": '["TEST3"]',
        "property_id": prop2_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/mappings", json=mapping2_data)
    if response.status_code != 201:
        log_error(f"Impossible de créer le mapping pour prop2: {response.status_code} {response.text}")
        return False
    mapping2 = response.json()
    log_success(f"Mapping créé pour prop2: {mapping2['id']}")
    
    # Vérifier que prop1 ne voit que ses mappings
    response = requests.get(f"{BASE_URL}/api/compte-resultat/mappings?property_id={prop1_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer les mappings de prop1: {response.status_code}")
        return False
    prop1_mappings = response.json()
    if any(m['id'] == mapping2['id'] for m in prop1_mappings['items']):
        log_error("ISOLATION ÉCHOUÉE: prop1 voit les mappings de prop2!")
        return False
    log_success(f"prop1 ne voit que ses {prop1_mappings['total']} mappings")
    
    # Vérifier que prop2 ne voit que ses mappings
    response = requests.get(f"{BASE_URL}/api/compte-resultat/mappings?property_id={prop2_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer les mappings de prop2: {response.status_code}")
        return False
    prop2_mappings = response.json()
    if any(m['id'] == mapping1['id'] for m in prop2_mappings['items']):
        log_error("ISOLATION ÉCHOUÉE: prop2 voit les mappings de prop1!")
        return False
    log_success(f"prop2 ne voit que ses {prop2_mappings['total']} mappings")
    
    # Tester qu'on ne peut pas modifier un mapping d'une autre propriété
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/mappings/{mapping1['id']}?property_id={prop2_id}",
        json={"category_name": "HACK"}
    )
    if response.status_code == 200:
        log_error("ISOLATION ÉCHOUÉE: prop2 peut modifier les mappings de prop1!")
        return False
    log_success("prop2 ne peut pas modifier les mappings de prop1")
    
    # Tester qu'on ne peut pas supprimer un mapping d'une autre propriété
    response = requests.delete(f"{BASE_URL}/api/compte-resultat/mappings/{mapping1['id']}?property_id={prop2_id}")
    if response.status_code == 204:
        log_error("ISOLATION ÉCHOUÉE: prop2 peut supprimer les mappings de prop1!")
        return False
    log_success("prop2 ne peut pas supprimer les mappings de prop1")
    
    return True

def test_compte_resultat_config_isolation(prop1_id, prop2_id):
    """Tester l'isolation de la config du Compte de Résultat."""
    log_info("=== Test isolation de la config ===")
    
    # Mettre à jour la config de prop1
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/config?property_id={prop1_id}",
        json={"level_3_values": '["Actif"]'}
    )
    if response.status_code != 200:
        log_error(f"Impossible de mettre à jour la config de prop1: {response.status_code} {response.text}")
        return False
    log_success("Config prop1 mise à jour avec level_3_values=['Actif']")
    
    # Mettre à jour la config de prop2
    response = requests.put(
        f"{BASE_URL}/api/compte-resultat/config?property_id={prop2_id}",
        json={"level_3_values": '["Passif"]'}
    )
    if response.status_code != 200:
        log_error(f"Impossible de mettre à jour la config de prop2: {response.status_code} {response.text}")
        return False
    log_success("Config prop2 mise à jour avec level_3_values=['Passif']")
    
    # Vérifier que prop1 a sa propre config
    response = requests.get(f"{BASE_URL}/api/compte-resultat/config?property_id={prop1_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer la config de prop1: {response.status_code}")
        return False
    config1 = response.json()
    if 'Actif' not in config1['level_3_values']:
        log_error("ISOLATION ÉCHOUÉE: Config prop1 incorrecte!")
        return False
    log_success(f"Config prop1 correcte: {config1['level_3_values']}")
    
    # Vérifier que prop2 a sa propre config (différente de prop1)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/config?property_id={prop2_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer la config de prop2: {response.status_code}")
        return False
    config2 = response.json()
    if 'Passif' not in config2['level_3_values']:
        log_error("ISOLATION ÉCHOUÉE: Config prop2 incorrecte!")
        return False
    log_success(f"Config prop2 correcte: {config2['level_3_values']}")
    
    return True

def test_compte_resultat_overrides_isolation(prop1_id, prop2_id):
    """Tester l'isolation des overrides du Compte de Résultat."""
    log_info("=== Test isolation des overrides ===")
    
    # Créer un override pour prop1
    override1_data = {
        "year": 2023,
        "override_value": 12345.67,
        "property_id": prop1_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/override", json=override1_data)
    if response.status_code != 201:
        log_error(f"Impossible de créer l'override pour prop1: {response.status_code} {response.text}")
        return False
    override1 = response.json()
    log_success(f"Override créé pour prop1: year={override1['year']}, value={override1['override_value']}")
    
    # Créer un override pour prop2 (même année, valeur différente)
    override2_data = {
        "year": 2023,
        "override_value": 98765.43,
        "property_id": prop2_id
    }
    response = requests.post(f"{BASE_URL}/api/compte-resultat/override", json=override2_data)
    if response.status_code != 201:
        log_error(f"Impossible de créer l'override pour prop2: {response.status_code} {response.text}")
        return False
    override2 = response.json()
    log_success(f"Override créé pour prop2: year={override2['year']}, value={override2['override_value']}")
    
    # Vérifier que prop1 a son override
    response = requests.get(f"{BASE_URL}/api/compte-resultat/override/2023?property_id={prop1_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer l'override de prop1: {response.status_code}")
        return False
    prop1_override = response.json()
    if abs(prop1_override['override_value'] - 12345.67) > 0.01:
        log_error(f"ISOLATION ÉCHOUÉE: Override prop1 incorrect: {prop1_override['override_value']}")
        return False
    log_success(f"Override prop1 correct: {prop1_override['override_value']}")
    
    # Vérifier que prop2 a son override (différent de prop1)
    response = requests.get(f"{BASE_URL}/api/compte-resultat/override/2023?property_id={prop2_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer l'override de prop2: {response.status_code}")
        return False
    prop2_override = response.json()
    if abs(prop2_override['override_value'] - 98765.43) > 0.01:
        log_error(f"ISOLATION ÉCHOUÉE: Override prop2 incorrect: {prop2_override['override_value']}")
        return False
    log_success(f"Override prop2 correct: {prop2_override['override_value']}")
    
    # Vérifier que la liste des overrides est isolée
    response = requests.get(f"{BASE_URL}/api/compte-resultat/override?property_id={prop1_id}")
    if response.status_code != 200:
        log_error(f"Impossible de récupérer les overrides de prop1: {response.status_code}")
        return False
    prop1_overrides = response.json()
    if any(o['override_value'] == override2['override_value'] for o in prop1_overrides):
        log_error("ISOLATION ÉCHOUÉE: prop1 voit les overrides de prop2!")
        return False
    log_success(f"prop1 ne voit que ses {len(prop1_overrides)} overrides")
    
    return True

def test_compte_resultat_calculate_isolation(prop1_id, prop2_id):
    """Tester l'isolation du calcul du Compte de Résultat."""
    log_info("=== Test isolation du calcul ===")
    
    # Appeler le calcul pour chaque propriété
    response1 = requests.get(f"{BASE_URL}/api/compte-resultat/calculate?property_id={prop1_id}&years=2023")
    if response1.status_code != 200:
        log_error(f"Impossible de calculer pour prop1: {response1.status_code} {response1.text}")
        return False
    log_success(f"Calcul prop1 réussi")
    
    response2 = requests.get(f"{BASE_URL}/api/compte-resultat/calculate?property_id={prop2_id}&years=2023")
    if response2.status_code != 200:
        log_error(f"Impossible de calculer pour prop2: {response2.status_code} {response2.text}")
        return False
    log_success(f"Calcul prop2 réussi")
    
    return True

def cleanup(prop_ids):
    """Supprimer les propriétés de test."""
    log_info("=== Nettoyage ===")
    for prop_id in prop_ids:
        response = requests.delete(f"{BASE_URL}/api/properties/{prop_id}")
        if response.status_code in [200, 204]:
            log_success(f"Propriété {prop_id} supprimée")
        else:
            log_error(f"Impossible de supprimer la propriété {prop_id}: {response.status_code}")

def main():
    print("\n" + "="*60)
    print("TEST D'ISOLATION - COMPTE DE RÉSULTAT - PHASE 11 bis 5.1")
    print("="*60 + "\n")
    
    # Créer les propriétés de test
    props = create_test_properties()
    if not props:
        log_error("Impossible de créer les propriétés de test")
        return 1
    
    prop1_id = props[0]['id']
    prop2_id = props[1]['id']
    
    all_passed = True
    
    try:
        # Test isolation des mappings
        if not test_compte_resultat_mappings_isolation(prop1_id, prop2_id):
            all_passed = False
        
        # Test isolation de la config
        if not test_compte_resultat_config_isolation(prop1_id, prop2_id):
            all_passed = False
        
        # Test isolation des overrides
        if not test_compte_resultat_overrides_isolation(prop1_id, prop2_id):
            all_passed = False
        
        # Test isolation du calcul
        if not test_compte_resultat_calculate_isolation(prop1_id, prop2_id):
            all_passed = False
        
    finally:
        # Nettoyage
        cleanup([prop1_id, prop2_id])
    
    print("\n" + "="*60)
    if all_passed:
        log_success("TOUS LES TESTS D'ISOLATION SONT PASSÉS ✓")
        return 0
    else:
        log_error("CERTAINS TESTS ONT ÉCHOUÉ ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
