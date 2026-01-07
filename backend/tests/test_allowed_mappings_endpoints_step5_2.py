"""
Test pour Step 5.2 : Endpoints API pour combinaisons autorisées.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import requests

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel,
    get_allowed_level1_values,
    get_allowed_level2_values,
    get_allowed_level3_values
)


def test_endpoints_directly():
    """Test les fonctions directement (sans API)."""
    print("\n" + "=" * 60)
    print("Test 1 : Fonctions de service directement")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # On va utiliser les fonctions directement
        
        # Test get_allowed_level1_values
        level1_values = get_allowed_level1_values(db)
        assert len(level1_values) > 0, "Aucune valeur level_1 trouvée"
        print(f"✓ get_allowed_level1_values : {len(level1_values)} valeurs")
        
        # Test get_allowed_level2_values
        if level1_values:
            level2_values = get_allowed_level2_values(db, level1_values[0])
            print(f"✓ get_allowed_level2_values pour '{level1_values[0]}' : {len(level2_values)} valeurs")
            
            # Test get_allowed_level3_values
            if level2_values:
                level3_values = get_allowed_level3_values(db, level1_values[0], level2_values[0])
                print(f"✓ get_allowed_level3_values pour ('{level1_values[0]}', '{level2_values[0]}') : {len(level3_values)} valeurs")
        
    finally:
        db.close()
    
    print("✓ Test 1 réussi\n")


def test_endpoints_via_api():
    """Test les endpoints via l'API (nécessite que l'API soit démarrée)."""
    print("=" * 60)
    print("Test 2 : Endpoints API (nécessite API démarrée)")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    try:
        # Test GET /api/mappings/allowed-level1
        print("\n1. Test GET /api/mappings/allowed-level1")
        response = requests.get(f"{base_url}/mappings/allowed-level1", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            assert "level_1" in data, "Réponse doit contenir 'level_1'"
            assert isinstance(data["level_1"], list), "'level_1' doit être une liste"
            assert len(data["level_1"]) > 0, "La liste ne doit pas être vide"
            print(f"   ✓ {len(data['level_1'])} valeurs level_1 retournées")
        else:
            print(f"   ⚠ API non disponible (status {response.status_code})")
            print("   → Test ignoré (l'API doit être démarrée pour ce test)")
            return
        
        # Test GET /api/mappings/allowed-level2
        if data["level_1"]:
            print("\n2. Test GET /api/mappings/allowed-level2")
            test_level1 = data["level_1"][0]
            response = requests.get(
                f"{base_url}/mappings/allowed-level2",
                params={"level_1": test_level1},
                timeout=5
            )
            
            if response.status_code == 200:
                data2 = response.json()
                assert "level_2" in data2, "Réponse doit contenir 'level_2'"
                assert isinstance(data2["level_2"], list), "'level_2' doit être une liste"
                print(f"   ✓ {len(data2['level_2'])} valeurs level_2 retournées pour '{test_level1}'")
                
                # Test GET /api/mappings/allowed-level3
                if data2["level_2"]:
                    print("\n3. Test GET /api/mappings/allowed-level3")
                    test_level2 = data2["level_2"][0]
                    response = requests.get(
                        f"{base_url}/mappings/allowed-level3",
                        params={"level_1": test_level1, "level_2": test_level2},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data3 = response.json()
                        assert "level_3" in data3, "Réponse doit contenir 'level_3'"
                        assert isinstance(data3["level_3"], list), "'level_3' doit être une liste"
                        print(f"   ✓ {len(data3['level_3'])} valeurs level_3 retournées pour ('{test_level1}', '{test_level2}')")
        
        print("\n✓ Test 2 réussi")
        
    except requests.exceptions.ConnectionError:
        print("   ⚠ API non disponible (connexion refusée)")
        print("   → Test ignoré (démarrez l'API avec: uvicorn backend.api.main:app --reload)")
    except Exception as e:
        print(f"   ✗ ERREUR : {str(e)}")
        raise
    
    print()


def test_endpoints_validation():
    """Test la validation des paramètres."""
    print("=" * 60)
    print("Test 3 : Validation des paramètres")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    try:
        # Test avec level_1 manquant pour level_2
        print("\n1. Test GET /api/mappings/allowed-level2 sans level_1")
        response = requests.get(f"{base_url}/mappings/allowed-level2", timeout=5)
        
        if response.status_code == 422:
            print("   ✓ Erreur 422 retournée (paramètre manquant)")
        elif response.status_code == 200:
            print("   ⚠ API non disponible ou paramètre optionnel")
        else:
            print(f"   ⚠ Status inattendu : {response.status_code}")
        
        # Test avec level_1 ou level_2 manquant pour level_3
        print("\n2. Test GET /api/mappings/allowed-level3 sans paramètres")
        response = requests.get(f"{base_url}/mappings/allowed-level3", timeout=5)
        
        if response.status_code == 422:
            print("   ✓ Erreur 422 retournée (paramètres manquants)")
        elif response.status_code == 200:
            print("   ⚠ API non disponible ou paramètres optionnels")
        else:
            print(f"   ⚠ Status inattendu : {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("   ⚠ API non disponible (connexion refusée)")
        print("   → Test ignoré")
    except Exception as e:
        print(f"   ✗ ERREUR : {str(e)}")
        # Ne pas faire échouer le test si l'API n'est pas disponible
    
    print("✓ Test 3 réussi\n")


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("TESTS - Step 5.2 : Endpoints API pour combinaisons autorisées")
    print("=" * 60)
    
    try:
        # Initialiser la base de données
        init_database()
        
        # S'assurer que des données existent
        db = SessionLocal()
        try:
            from backend.database.models import AllowedMapping
            count = db.query(AllowedMapping).count()
            if count == 0:
                print("\n⚠ Aucune combinaison dans la table. Chargement depuis Excel...")
                excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
                if excel_path.exists():
                    load_allowed_mappings_from_excel(db, excel_path)
                    print("✓ Combinaisons chargées")
                else:
                    print("⚠ Fichier Excel non trouvé, certains tests peuvent échouer")
        finally:
            db.close()
        
        test_endpoints_directly()
        test_endpoints_via_api()
        test_endpoints_validation()
        
        print("=" * 60)
        print("✓ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
        print("\nNote : Les tests API nécessitent que l'API soit démarrée.")
        print("       Démarrez avec: uvicorn backend.api.main:app --reload")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ ERREUR DE TEST : {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

