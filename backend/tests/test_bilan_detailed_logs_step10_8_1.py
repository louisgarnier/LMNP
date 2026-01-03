"""
Test détaillé avec logs complets pour comprendre pourquoi les montants ne s'affichent pas.

Test avec deux mappings :
1. "Souscription de parts sociales" avec level_1 "souscription part sociale"
2. "Immobilisations" avec level_1 "Immeuble (hors terrain)"

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_detailed_logs_step10_8_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData, Transaction

client = TestClient(app)


def test_detailed_flow():
    """Test détaillé avec logs complets."""
    print("=" * 80)
    print("TEST DÉTAILLÉ - Logs Backend et Frontend")
    print("=" * 80)
    print()
    
    # ========== ÉTAPE 1: Vérifier les mappings ==========
    print("📋 ÉTAPE 1: Vérification des mappings")
    print("-" * 80)
    mappings_response = client.get("/api/bilan/mappings")
    assert mappings_response.status_code == 200
    mappings = mappings_response.json().get("mappings", [])
    print(f"✅ {len(mappings)} mapping(s) trouvé(s)")
    print()
    
    # Chercher les deux mappings de test
    mapping_souscription = None
    mapping_immobilisations = None
    
    for mapping in mappings:
        cat_name = mapping.get("category_name", "")
        if "Souscription de parts sociales" in cat_name:
            mapping_souscription = mapping
        if "Immobilisations" == cat_name:
            mapping_immobilisations = mapping
    
    print("🔍 Mappings de test:")
    if mapping_souscription:
        print(f"  ✅ 'Souscription de parts sociales' (ID {mapping_souscription['id']})")
        print(f"     Level 1: {mapping_souscription.get('level_1_values', [])}")
        print(f"     Type: {mapping_souscription.get('type')}")
        print(f"     Sous-catégorie: {mapping_souscription.get('sub_category')}")
        print(f"     Is special: {mapping_souscription.get('is_special')}")
    else:
        print(f"  ❌ 'Souscription de parts sociales' NON TROUVÉ")
    
    if mapping_immobilisations:
        print(f"  ✅ 'Immobilisations' (ID {mapping_immobilisations['id']})")
        print(f"     Level 1: {mapping_immobilisations.get('level_1_values', [])}")
        print(f"     Type: {mapping_immobilisations.get('type')}")
        print(f"     Sous-catégorie: {mapping_immobilisations.get('sub_category')}")
        print(f"     Is special: {mapping_immobilisations.get('is_special')}")
    else:
        print(f"  ❌ 'Immobilisations' NON TROUVÉ")
    print()
    
    # ========== ÉTAPE 2: Vérifier les transactions correspondantes ==========
    print("📊 ÉTAPE 2: Vérification des transactions")
    print("-" * 80)
    
    # Récupérer toutes les transactions
    transactions_response = client.get("/api/transactions?skip=0&limit=1000")
    if transactions_response.status_code != 200:
        transactions_response = client.get("/api/transactions")
    assert transactions_response.status_code == 200
    transactions_data = transactions_response.json()
    transactions = transactions_data.get("transactions", transactions_data.get("data", []))
    print(f"✅ {len(transactions)} transaction(s) trouvée(s)")
    
    # Chercher les transactions avec les level_1 de test
    level1_souscription = "souscription part sociale"
    level1_immobilisations = "Immeuble (hors terrain)"
    
    transactions_souscription = [
        t for t in transactions 
        if t.get("level_1", "").lower() == level1_souscription.lower()
    ]
    transactions_immobilisations = [
        t for t in transactions 
        if t.get("level_1", "").lower() == level1_immobilisations.lower()
    ]
    
    print(f"🔍 Transactions pour '{level1_souscription}': {len(transactions_souscription)}")
    if transactions_souscription:
        for t in transactions_souscription[:3]:
            print(f"     - {t.get('date', 'N/A')}: {t.get('nom', 'N/A')} = {t.get('quantite', 0):,.2f} €")
    
    print(f"🔍 Transactions pour '{level1_immobilisations}': {len(transactions_immobilisations)}")
    if transactions_immobilisations:
        for t in transactions_immobilisations[:3]:
            print(f"     - {t.get('date', 'N/A')}: {t.get('nom', 'N/A')} = {t.get('quantite', 0):,.2f} €")
    print()
    
    # ========== ÉTAPE 3: Vérifier les données existantes ==========
    print("📊 ÉTAPE 3: Vérification des données BilanData existantes")
    print("-" * 80)
    years = [2021, 2022, 2023, 2024, 2025]
    start_year = min(years)
    end_year = max(years)
    
    bilan_response = client.get(f"/api/bilan?start_year={start_year}&end_year={end_year}")
    assert bilan_response.status_code == 200
    data_existing = bilan_response.json().get("data", [])
    print(f"✅ {len(data_existing)} donnée(s) existante(s)")
    
    if data_existing:
        categories_existing = set(d.get("category_name") for d in data_existing)
        print(f"   Catégories: {sorted(categories_existing)}")
        
        if mapping_souscription:
            data_souscription = [d for d in data_existing if d.get("category_name") == mapping_souscription.get("category_name")]
            print(f"   Données pour 'Souscription de parts sociales': {len(data_souscription)}")
            for d in data_souscription:
                print(f"     {d.get('annee')}: {d.get('amount'):,.2f} €")
        
        if mapping_immobilisations:
            data_immobilisations = [d for d in data_existing if d.get("category_name") == mapping_immobilisations.get("category_name")]
            print(f"   Données pour 'Immobilisations': {len(data_immobilisations)}")
            for d in data_immobilisations:
                print(f"     {d.get('annee')}: {d.get('amount'):,.2f} €")
    print()
    
    # ========== ÉTAPE 4: Invalider et régénérer ==========
    print("🔄 ÉTAPE 4: Invalidation et régénération")
    print("-" * 80)
    
    # Simuler l'invalidation en modifiant un mapping (même valeur pour déclencher invalidation)
    if mapping_souscription:
        print(f"🔄 Modification du mapping 'Souscription de parts sociales' pour déclencher invalidation...")
        update_response = client.put(
            f"/api/bilan/mappings/{mapping_souscription['id']}",
            json={
                "category_name": mapping_souscription.get("category_name"),
                "level_1_values": mapping_souscription.get("level_1_values", []),
            }
        )
        if update_response.status_code == 200:
            print("  ✅ Mapping mis à jour (invalidation déclenchée)")
        else:
            print(f"  ❌ Erreur: {update_response.status_code}")
    
    # Vérifier que les données sont invalidées
    bilan_response_after = client.get(f"/api/bilan?start_year={start_year}&end_year={end_year}")
    data_after = bilan_response_after.json().get("data", [])
    print(f"📊 Données après invalidation: {len(data_after)}")
    print()
    
    # Régénérer pour toutes les années
    print("🔄 Génération pour toutes les années...")
    generation_results = {}
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
                generate_data = generate_response.json()
                generation_results[year] = {
                    "success": True,
                    "types": len(generate_data.get("types", [])),
                    "equilibre": generate_data.get("equilibre", {})
                }
                print(f"  ✅ {year}: Généré ({generation_results[year]['types']} type(s))")
            else:
                generation_results[year] = {
                    "success": False,
                    "error": f"Status {generate_response.status_code}",
                    "detail": generate_response.json().get("detail", "")[:100] if generate_response.status_code != 200 else ""
                }
                print(f"  ❌ {year}: Échec - {generation_results[year]['error']}")
        except Exception as e:
            generation_results[year] = {
                "success": False,
                "error": str(e)[:100]
            }
            print(f"  ❌ {year}: Exception - {generation_results[year]['error']}")
    print()
    
    # ========== ÉTAPE 5: Vérifier les données après génération ==========
    print("📊 ÉTAPE 5: Vérification des données après génération")
    print("-" * 80)
    
    bilan_response_final = client.get(f"/api/bilan?start_year={start_year}&end_year={end_year}")
    assert bilan_response_final.status_code == 200
    data_final = bilan_response_final.json().get("data", [])
    print(f"✅ {len(data_final)} donnée(s) après génération")
    
    if data_final:
        categories_final = set(d.get("category_name") for d in data_final)
        print(f"   Catégories générées: {sorted(categories_final)}")
        print()
        
        # Détails pour "Souscription de parts sociales"
        if mapping_souscription:
            cat_name = mapping_souscription.get("category_name")
            data_cat = [d for d in data_final if d.get("category_name") == cat_name]
            print(f"📊 Données pour '{cat_name}':")
            if data_cat:
                for d in sorted(data_cat, key=lambda x: x.get("annee", 0)):
                    print(f"     {d.get('annee')}: {d.get('amount'):,.2f} €")
                non_zero = [d for d in data_cat if abs(d.get("amount", 0)) > 0.01]
                print(f"   ✅ {len(non_zero)}/{len(data_cat)} année(s) avec montants non nuls")
            else:
                print(f"   ❌ AUCUNE donnée générée pour cette catégorie")
                print(f"   💡 Vérifier que le mapping a bien des level_1_values configurés")
                print(f"      Level 1 configurés: {mapping_souscription.get('level_1_values', [])}")
            print()
        
        # Détails pour "Immobilisations"
        if mapping_immobilisations:
            cat_name = mapping_immobilisations.get("category_name")
            data_cat = [d for d in data_final if d.get("category_name") == cat_name]
            print(f"📊 Données pour '{cat_name}':")
            if data_cat:
                for d in sorted(data_cat, key=lambda x: x.get("annee", 0)):
                    print(f"     {d.get('annee')}: {d.get('amount'):,.2f} €")
                non_zero = [d for d in data_cat if abs(d.get("amount", 0)) > 0.01]
                print(f"   ✅ {len(non_zero)}/{len(data_cat)} année(s) avec montants non nuls")
            else:
                print(f"   ❌ AUCUNE donnée générée pour cette catégorie")
                print(f"   💡 Vérifier que le mapping a bien des level_1_values configurés")
                print(f"      Level 1 configurés: {mapping_immobilisations.get('level_1_values', [])}")
            print()
    
    # ========== RÉSUMÉ ==========
    print("=" * 80)
    print("📋 RÉSUMÉ")
    print("=" * 80)
    print(f"Mappings trouvés: {len(mappings)}")
    print(f"  - 'Souscription de parts sociales': {'✅' if mapping_souscription else '❌'}")
    print(f"  - 'Immobilisations': {'✅' if mapping_immobilisations else '❌'}")
    print()
    print(f"Transactions trouvées:")
    print(f"  - '{level1_souscription}': {len(transactions_souscription)}")
    print(f"  - '{level1_immobilisations}': {len(transactions_immobilisations)}")
    print()
    print(f"Génération:")
    success_count = sum(1 for r in generation_results.values() if r.get("success"))
    print(f"  - Réussies: {success_count}/{len(years)}")
    print()
    print(f"Données finales: {len(data_final)} élément(s)")
    if mapping_souscription:
        data_souscription_final = [d for d in data_final if d.get("category_name") == mapping_souscription.get("category_name")]
        print(f"  - 'Souscription de parts sociales': {len(data_souscription_final)} donnée(s)")
    if mapping_immobilisations:
        data_immobilisations_final = [d for d in data_final if d.get("category_name") == mapping_immobilisations.get("category_name")]
        print(f"  - 'Immobilisations': {len(data_immobilisations_final)} donnée(s)")
    print()


if __name__ == "__main__":
    try:
        test_detailed_flow()
    except AssertionError as e:
        print()
        print("=" * 80)
        print(f"❌ Test échoué: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)

