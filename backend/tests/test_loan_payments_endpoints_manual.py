"""
Test manuel pour les endpoints API des mensualités (loan payments).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_loan_payments_endpoints_manual.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
from datetime import date

# Configuration
API_BASE_URL = "http://localhost:8000"

def print_section(title):
    """Affiche une section de test."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success, message):
    """Affiche le résultat d'un test."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def test_get_loan_payments():
    """Test GET /api/loan-payments"""
    print_section("Test 1: GET /api/loan-payments (Liste)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/loan-payments")
        if response.status_code == 200:
            data = response.json()
            print(f"Total: {data.get('total', 0)}")
            print(f"Payments: {len(data.get('payments', []))}")
            print_result(True, f"Liste récupérée: {data.get('total', 0)} mensualité(s)")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_create_loan_payment():
    """Test POST /api/loan-payments"""
    print_section("Test 2: POST /api/loan-payments (Création)")
    try:
        payment_data = {
            "date": "2024-01-01",
            "capital": 1000.0,
            "interest": 200.0,
            "insurance": 50.0,
            "total": 1250.0,
            "loan_name": "Prêt principal"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/loan-payments",
            json=payment_data
        )
        if response.status_code == 200:
            data = response.json()
            print(f"ID créé: {data.get('id')}")
            print(f"Date: {data.get('date')}")
            print(f"Capital: {data.get('capital')}")
            print(f"Total: {data.get('total')}")
            print_result(True, f"Mensualité créée avec ID {data.get('id')}")
            return data.get('id')
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return None

def test_get_loan_payment_by_id(payment_id):
    """Test GET /api/loan-payments/{id}"""
    print_section(f"Test 3: GET /api/loan-payments/{payment_id} (Détail)")
    if not payment_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        response = requests.get(f"{API_BASE_URL}/api/loan-payments/{payment_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"ID: {data.get('id')}")
            print(f"Date: {data.get('date')}")
            print(f"Capital: {data.get('capital')}")
            print_result(True, f"Mensualité récupérée")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_update_loan_payment(payment_id):
    """Test PUT /api/loan-payments/{id}"""
    print_section(f"Test 4: PUT /api/loan-payments/{payment_id} (Mise à jour)")
    if not payment_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        update_data = {
            "capital": 1200.0,
            "interest": 250.0,
            "insurance": 50.0
            # total sera recalculé automatiquement
        }
        response = requests.put(
            f"{API_BASE_URL}/api/loan-payments/{payment_id}",
            json=update_data
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Capital mis à jour: {data.get('capital')}")
            print(f"Total recalculé: {data.get('total')}")
            print_result(True, f"Mensualité mise à jour")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_preview_excel():
    """Test POST /api/loan-payments/preview"""
    print_section("Test 5: POST /api/loan-payments/preview (Preview Excel)")
    try:
        # Chemin vers le fichier Excel de test
        excel_file_path = project_root / "scripts" / "tableau_ammort_taxes copy 2.xlsx"
        
        if not excel_file_path.exists():
            print_result(False, f"Fichier Excel non trouvé: {excel_file_path}")
            return False
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': ('tableau_ammort_taxes.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{API_BASE_URL}/api/loan-payments/preview?loan_name=Prêt principal",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Fichier: {data.get('filename')}")
            print(f"Années détectées: {len(data.get('detected_years', []))}")
            print(f"Années: {data.get('detected_years', [])[:10]}...")  # Premières 10
            print(f"Mensualités existantes: {data.get('existing_payments_count', 0)}")
            print(f"Avertissements: {len(data.get('warnings', []))}")
            if data.get('warnings'):
                for warning in data.get('warnings', [])[:3]:  # Premiers 3
                    print(f"  - {warning}")
            print(f"Erreurs de validation: {len(data.get('validation_errors', []))}")
            print(f"Preview: {len(data.get('preview', []))} années")
            print_result(True, f"Preview réussi: {len(data.get('detected_years', []))} années détectées")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_import_excel():
    """Test POST /api/loan-payments/import"""
    print_section("Test 6: POST /api/loan-payments/import (Import Excel)")
    try:
        # Chemin vers le fichier Excel de test
        excel_file_path = project_root / "scripts" / "tableau_ammort_taxes copy 2.xlsx"
        
        if not excel_file_path.exists():
            print_result(False, f"Fichier Excel non trouvé: {excel_file_path}")
            return False
        
        # Demander confirmation
        print("⚠️  Cette opération va supprimer toutes les mensualités existantes pour 'Prêt principal'")
        confirm = input("Continuer ? (oui/non): ").strip().lower()
        if confirm not in ['oui', 'o', 'yes', 'y']:
            print("Import annulé")
            return False
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': ('tableau_ammort_taxes.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{API_BASE_URL}/api/loan-payments/import?loan_name=Prêt principal&confirm_replace=true",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            print(f"Importées: {data.get('imported_count', 0)}")
            print(f"Avertissements: {len(data.get('warnings', []))}")
            if data.get('warnings'):
                for warning in data.get('warnings', [])[:5]:  # Premiers 5
                    print(f"  - {warning}")
            print(f"Erreurs: {len(data.get('errors', []))}")
            if data.get('errors'):
                for error in data.get('errors', [])[:5]:  # Premiers 5
                    print(f"  - {error}")
            print_result(True, f"Import réussi: {data.get('imported_count', 0)} mensualité(s)")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_delete_loan_payment(payment_id):
    """Test DELETE /api/loan-payments/{id}"""
    print_section(f"Test 7: DELETE /api/loan-payments/{payment_id} (Suppression)")
    if not payment_id:
        print_result(False, "ID manquant, test ignoré")
        return False
    try:
        response = requests.delete(f"{API_BASE_URL}/api/loan-payments/{payment_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            print_result(True, f"Mensualité supprimée")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_filters():
    """Test GET /api/loan-payments avec filtres"""
    print_section("Test 8: GET /api/loan-payments avec filtres")
    try:
        # Test avec filtre loan_name
        response = requests.get(f"{API_BASE_URL}/api/loan-payments?loan_name=Prêt principal&limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"Total avec filtre: {data.get('total', 0)}")
            print(f"Payments retournés: {len(data.get('payments', []))}")
            print_result(True, f"Filtres fonctionnent")
            return True
        else:
            print_result(False, f"Erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("  TESTS MANUELS - Endpoints API Loan Payments")
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print("⚠️  Assurez-vous que le serveur backend est démarré (uvicorn backend.api.main:app)")
    
    results = []
    
    # Test 1: Liste
    results.append(("GET Liste", test_get_loan_payments()))
    
    # Test 2: Création
    payment_id = test_create_loan_payment()
    results.append(("POST Création", payment_id is not None))
    
    # Test 3: Détail
    results.append(("GET Détail", test_get_loan_payment_by_id(payment_id)))
    
    # Test 4: Mise à jour
    results.append(("PUT Mise à jour", test_update_loan_payment(payment_id)))
    
    # Test 5: Preview Excel
    results.append(("POST Preview Excel", test_preview_excel()))
    
    # Test 6: Import Excel (optionnel, demande confirmation)
    print("\n⚠️  Test d'import Excel - nécessite confirmation")
    import_choice = input("Tester l'import Excel ? (oui/non): ").strip().lower()
    if import_choice in ['oui', 'o', 'yes', 'y']:
        results.append(("POST Import Excel", test_import_excel()))
    else:
        print("Test d'import ignoré")
        results.append(("POST Import Excel", None))
    
    # Test 7: Suppression
    results.append(("DELETE Suppression", test_delete_loan_payment(payment_id)))
    
    # Test 8: Filtres
    results.append(("GET Filtres", test_filters()))
    
    # Résumé
    print_section("RÉSUMÉ DES TESTS")
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print_result(True, test_name)
            passed += 1
        elif result is False:
            print_result(False, test_name)
            failed += 1
        else:
            print(f"⏭️  {test_name} (ignoré)")
            skipped += 1
    
    print(f"\n✅ Réussis: {passed}")
    print(f"❌ Échoués: {failed}")
    print(f"⏭️  Ignorés: {skipped}")
    print(f"📊 Total: {len(results)}")

if __name__ == "__main__":
    main()

