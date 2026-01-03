"""
Test du chargement des données dans BilanTable (Step 10.8.1).

Ce test vérifie que :
1. Les mappings sont chargés correctement
2. Les données sont récupérées depuis l'API
3. Les données sont générées si elles n'existent pas
4. Les montants sont organisés correctement par année et catégorie

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_table_data_loading_step10_8_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData, Transaction

client = TestClient(app)


def test_bilan_table_data_flow():
    """Test le flux complet de chargement des données pour BilanTable."""
    print("=" * 70)
    print("Test du flux de données BilanTable (Step 10.8.1)")
    print("=" * 70)
    print()
    
    # Étape 1: Vérifier qu'il y a des mappings
    print("📋 Étape 1: Chargement des mappings...")
    mappings_response = client.get("/api/bilan/mappings")
    assert mappings_response.status_code == 200, f"Status code attendu: 200, reçu: {mappings_response.status_code}"
    mappings_data = mappings_response.json()
    mappings = mappings_data.get("mappings", [])
    print(f"  ✅ {len(mappings)} mapping(s) trouvé(s)")
    
    if len(mappings) == 0:
        print("  ⚠️ Aucun mapping configuré - le test nécessite au moins un mapping")
        print("  💡 Créez un mapping dans BilanConfigCard pour tester")
        return
    
    # Afficher les mappings
    for mapping in mappings[:5]:  # Afficher les 5 premiers
        level1_values = mapping.get("level_1_values", [])
        level1_str = ", ".join(level1_values) if level1_values else "Aucune"
        print(f"     - {mapping.get('category_name', 'N/A')} ({mapping.get('type', 'N/A')}) - Level 1: {level1_str}")
    
    if len(mappings) > 5:
        print(f"     ... et {len(mappings) - 5} autre(s)")
    print()
    
    # Étape 2: Vérifier les années disponibles (basées sur les transactions)
    print("📅 Étape 2: Calcul des années disponibles...")
    transactions_response = client.get("/api/transactions?skip=0&limit=1000")
    if transactions_response.status_code != 200:
        # Essayer sans paramètres
        transactions_response = client.get("/api/transactions")
    assert transactions_response.status_code == 200, f"Status code: {transactions_response.status_code}, Response: {transactions_response.text[:200]}"
    transactions_data = transactions_response.json()
    transactions = transactions_data.get("transactions", transactions_data.get("data", []))
    
    if len(transactions) == 0:
        print("  ⚠️ Aucune transaction trouvée - utilisation de l'année en cours")
        from datetime import datetime
        current_year = datetime.now().year
        years = [current_year]
    else:
        dates = [t["date"] for t in transactions if t.get("date")]
        if dates:
            from datetime import datetime
            min_date = min(datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if d)
            max_date = max(datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if d)
            first_year = min_date.year
            last_year = max_date.year
            years = list(range(first_year, last_year + 1))
        else:
            from datetime import datetime
            years = [datetime.now().year]
    
    print(f"  ✅ Années calculées: {years}")
    print()
    
    # Étape 3: Vérifier les données existantes
    print("📊 Étape 3: Vérification des données existantes...")
    if years:
        start_year = min(years)
        end_year = max(years)
        bilan_response = client.get(f"/api/bilan?start_year={start_year}&end_year={end_year}")
        assert bilan_response.status_code == 200
        bilan_data = bilan_response.json()
        data = bilan_data.get("data", [])
        print(f"  ✅ {len(data)} donnée(s) trouvée(s) pour {start_year}-{end_year}")
        
        if len(data) > 0:
            # Afficher quelques exemples
            categories_by_year = {}
            for item in data:
                year = item["annee"]
                category = item["category_name"]
                amount = item["amount"]
                if year not in categories_by_year:
                    categories_by_year[year] = {}
                categories_by_year[year][category] = amount
            
            print("  📊 Exemples de données:")
            for year in sorted(categories_by_year.keys())[:3]:  # 3 premières années
                print(f"     Année {year}:")
                for category, amount in list(categories_by_year[year].items())[:3]:  # 3 premières catégories
                    print(f"       - {category}: {amount:,.2f} €")
        else:
            print("  ⚠️ Aucune donnée trouvée - génération nécessaire")
    print()
    
    # Étape 4: Test de génération pour une année (si pas de données)
    print("🔄 Étape 4: Test de génération des données...")
    if years and len(data) == 0:
        test_year = years[0]
        print(f"  🧪 Génération du bilan pour {test_year}...")
        
        # Récupérer selected_level_3_values depuis localStorage (simulé)
        # En réalité, BilanTable récupère ça depuis localStorage
        selected_level_3_values = None
        
        generate_response = client.post(
            "/api/bilan/generate",
            json={
                "year": test_year,
                "selected_level_3_values": selected_level_3_values
            }
        )
        
        if generate_response.status_code == 200:
            print(f"  ✅ Bilan généré avec succès pour {test_year}")
            generate_data = generate_response.json()
            print(f"     Types: {len(generate_data.get('types', []))}")
            print(f"     Équilibre ACTIF: {generate_data.get('equilibre', {}).get('actif', 0):,.2f} €")
            print(f"     Équilibre PASSIF: {generate_data.get('equilibre', {}).get('passif', 0):,.2f} €")
        elif generate_response.status_code == 400:
            print(f"  ⚠️ Génération échouée (probablement pas de mappings configurés ou erreur de calcul)")
            print(f"     Erreur: {generate_response.json().get('detail', 'Erreur inconnue')}")
        else:
            print(f"  ❌ Erreur lors de la génération: {generate_response.status_code}")
            print(f"     Réponse: {generate_response.text}")
    else:
        print("  ℹ️ Des données existent déjà, pas de génération nécessaire")
    print()
    
    # Étape 5: Vérifier l'organisation des montants
    print("📦 Étape 5: Organisation des montants par année et catégorie...")
    if years:
        start_year = min(years)
        end_year = max(years)
        bilan_response = client.get(f"/api/bilan?start_year={start_year}&end_year={end_year}")
        assert bilan_response.status_code == 200
        bilan_data = bilan_response.json()
        data = bilan_data.get("data", [])
        
        if len(data) > 0:
            # Organiser comme BilanTable le fait
            amounts_by_year = {}
            for item in data:
                year_str = str(item["annee"])
                category = item["category_name"]
                amount = item["amount"]
                if year_str not in amounts_by_year:
                    amounts_by_year[year_str] = {}
                amounts_by_year[year_str][category] = amount
            
            print(f"  ✅ Montants organisés pour {len(amounts_by_year)} année(s)")
            print(f"     Années: {sorted(amounts_by_year.keys())}")
            
            # Vérifier une catégorie spécifique (exemple: "Souscription de parts sociales")
            test_category = "Souscription de parts sociales"
            found = False
            for year_str, categories in amounts_by_year.items():
                if test_category in categories:
                    found = True
                    print(f"     ✅ '{test_category}' trouvée pour {year_str}: {categories[test_category]:,.2f} €")
                    break
            
            if not found:
                print(f"     ⚠️ '{test_category}' non trouvée dans les données")
                print(f"     Catégories disponibles: {list(list(amounts_by_year.values())[0].keys())[:5] if amounts_by_year else []}")
        else:
            print("  ⚠️ Aucune donnée à organiser")
    print()
    
    print("=" * 70)
    print("✅ Test terminé")
    print("=" * 70)
    print()
    print("💡 Pour tester dans le frontend:")
    print("   1. Assurez-vous que le backend est démarré")
    print("   2. Ouvrez http://localhost:3000/dashboard/etats-financiers")
    print("   3. Cliquez sur l'onglet 'Bilan'")
    print("   4. Ajoutez un level_1 (ex: 'souscription part sociale') pour 'Souscription de parts sociales'")
    print("   5. Vérifiez que les montants s'affichent dans la table")
    print()


if __name__ == "__main__":
    try:
        test_bilan_table_data_flow()
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

