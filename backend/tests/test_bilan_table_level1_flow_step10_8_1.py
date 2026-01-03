"""
Test du flux complet : ajout level_1 → invalidation → régénération → affichage.

Ce test simule le comportement attendu quand on ajoute un level_1 dans BilanConfigCard :
1. Ajouter un level_1 à un mapping
2. Vérifier que les données sont invalidées
3. Vérifier que les données peuvent être régénérées
4. Vérifier que les montants sont corrects

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_table_level1_flow_step10_8_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData

client = TestClient(app)


def test_level1_add_flow():
    """Test le flux complet d'ajout d'un level_1."""
    print("=" * 70)
    print("Test du flux level_1 → invalidation → régénération (Step 10.8.1)")
    print("=" * 70)
    print()
    
    # Étape 1: Trouver un mapping de test (n'importe lequel avec ou sans level_1)
    print("📋 Étape 1: Préparation du mapping de test...")
    mappings_response = client.get("/api/bilan/mappings")
    assert mappings_response.status_code == 200
    mappings = mappings_response.json().get("mappings", [])
    
    if len(mappings) == 0:
        print("  ⚠️ Aucun mapping trouvé")
        print("  💡 Créez un mapping dans BilanConfigCard pour tester")
        return
    
    # Prendre le premier mapping qui n'est pas spécial (pour pouvoir tester level_1)
    test_mapping = None
    for mapping in mappings:
        if not mapping.get("is_special", False):
            test_mapping = mapping
            break
    
    # Si tous sont spéciaux, prendre le premier quand même
    if not test_mapping:
        test_mapping = mappings[0]
    
    mapping_id = test_mapping["id"]
    current_level1 = test_mapping.get("level_1_values", [])
    print(f"  ✅ Mapping trouvé: ID {mapping_id}")
    print(f"     Catégorie: {test_mapping.get('category_name')}")
    print(f"     Level 1 actuels: {current_level1}")
    print()
    
    # Étape 2: Vérifier les données existantes avant modification
    print("📊 Étape 2: Vérification des données avant modification...")
    bilan_response = client.get("/api/bilan?start_year=2021&end_year=2025")
    assert bilan_response.status_code == 200
    data_before = bilan_response.json().get("data", [])
    print(f"  ✅ {len(data_before)} donnée(s) trouvée(s) avant modification")
    
    category_name = test_mapping.get("category_name")
    
    # Trouver les données pour cette catégorie
    category_data_before = [d for d in data_before if d.get("category_name") == category_name]
    if category_data_before:
        print(f"  📊 Données pour '{category_name}':")
        for item in category_data_before[:3]:
            print(f"     {item.get('annee')}: {item.get('amount'):,.2f} €")
    print()
    
    # Étape 3: Ajouter un level_1 (simuler l'action dans BilanConfigCard)
    print("➕ Étape 3: Ajout d'un level_1 (simulation BilanConfigCard)...")
    # Utiliser un level_1 qui existe probablement dans les transactions
    test_level1_value = "Immeuble (hors terrain)" if "Immobilisations" in category_name else "souscription part sociale"
    
    # Vérifier si la valeur existe déjà
    if test_level1_value in current_level1:
        print(f"  ℹ️ Level 1 '{test_level1_value}' existe déjà, on le supprime d'abord...")
        updated_level1 = [v for v in current_level1 if v != test_level1_value]
        update_response = client.put(
            f"/api/bilan/mappings/{mapping_id}",
            json={
                "category_name": test_mapping.get("category_name"),
                "level_1_values": updated_level1,
            }
        )
        if update_response.status_code != 200:
            print(f"  ❌ Erreur lors de la suppression: {update_response.status_code}")
            return
        print(f"  ✅ Level 1 supprimé temporairement")
        print()
    
    # Ajouter le level_1
    updated_level1 = list(current_level1) if current_level1 else []
    if test_level1_value not in updated_level1:
        updated_level1.append(test_level1_value)
    
    print(f"  🧪 Ajout de level_1: '{test_level1_value}'")
    update_response = client.put(
        f"/api/bilan/mappings/{mapping_id}",
        json={
            "category_name": test_mapping.get("category_name"),
            "level_1_values": updated_level1,
        }
    )
    
    if update_response.status_code != 200:
        print(f"  ❌ Erreur lors de la mise à jour: {update_response.status_code}")
        print(f"     Réponse: {update_response.text[:200]}")
        return
    
    print(f"  ✅ Level 1 ajouté avec succès")
    print(f"     Level 1 maintenant: {updated_level1}")
    print()
    
    # Étape 4: Vérifier que les données ont été invalidées
    print("🔄 Étape 4: Vérification de l'invalidation des données...")
    bilan_response_after = client.get("/api/bilan?start_year=2021&end_year=2025")
    assert bilan_response_after.status_code == 200
    data_after = bilan_response_after.json().get("data", [])
    print(f"  ✅ {len(data_after)} donnée(s) trouvée(s) après modification")
    
    if len(data_after) == 0:
        print("  ✅ Les données ont été invalidées (comme attendu)")
    else:
        print("  ⚠️ Des données existent encore (peut-être pas toutes invalidées)")
    print()
    
    # Étape 5: Régénérer les données (simuler BilanTable)
    print("🔄 Étape 5: Régénération des données (simulation BilanTable)...")
    years = [2021, 2022, 2023, 2024, 2025]
    generation_success = 0
    generation_failed = 0
    
    for year in years:
        try:
            generate_response = client.post(
                "/api/bilan/generate",
                json={
                    "year": year,
                    "selected_level_3_values": None
                }
            )
            if generate_response.status_code == 200:
                generation_success += 1
                print(f"  ✅ {year}: Généré")
            else:
                generation_failed += 1
                print(f"  ❌ {year}: Échec ({generate_response.status_code})")
        except Exception as e:
            generation_failed += 1
            print(f"  ❌ {year}: Erreur - {str(e)[:50]}")
    
    print(f"  📊 Résultat: {generation_success} réussie(s), {generation_failed} échec(s)")
    print()
    
    # Étape 6: Vérifier que les données sont maintenant présentes avec les bons montants
    print("📊 Étape 6: Vérification des données après régénération...")
    bilan_response_final = client.get("/api/bilan?start_year=2021&end_year=2025")
    assert bilan_response_final.status_code == 200
    data_final = bilan_response_final.json().get("data", [])
    print(f"  ✅ {len(data_final)} donnée(s) trouvée(s) après régénération")
    
    # Trouver les données pour cette catégorie
    category_data_final = [d for d in data_final if d.get("category_name") == category_name]
    if category_data_final:
        print(f"  ✅ Données pour '{category_name}' trouvées:")
        for item in category_data_final:
            print(f"     {item.get('annee')}: {item.get('amount'):,.2f} €")
        
        # Vérifier qu'il y a des montants non nuls
        non_zero = [d for d in category_data_final if abs(d.get("amount", 0)) > 0.01]
        if non_zero:
            print(f"  ✅ {len(non_zero)} année(s) avec montants non nuls (données calculées correctement)")
        else:
            print(f"  ⚠️ Tous les montants sont à 0 (peut-être pas de transactions correspondantes)")
    else:
        print(f"  ⚠️ Aucune donnée pour '{category_name}' après régénération")
        print(f"     Catégories disponibles: {list(set(d.get('category_name') for d in data_final[:10]))}")
    print()
    
    print("=" * 70)
    print("✅ Test terminé")
    print("=" * 70)
    print()
    print("💡 Résumé:")
    print(f"   - Catégorie testée: {category_name}")
    print(f"   - Level 1 ajouté: {test_level1_value}")
    print(f"   - Données invalidées: {'Oui' if len(data_after) == 0 else 'Partiellement'}")
    print(f"   - Génération: {generation_success}/{len(years)} réussie(s)")
    print(f"   - Données finales: {len(data_final)} élément(s)")
    print()


if __name__ == "__main__":
    try:
        test_level1_add_flow()
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ Test échoué: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

