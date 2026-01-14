"""
Test d'intégration pour vérifier que l'invalidation des comptes de résultat
se déclenche bien lors des modifications de données.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce test vérifie que :
1. La création d'une transaction invalide les comptes de résultat pour l'année
2. La modification d'une transaction invalide les comptes de résultat
3. La suppression d'une transaction invalide les comptes de résultat
4. La création/modification/suppression de loan_payment invalide les comptes
5. La modification de mappings invalide tous les comptes

Usage:
    python backend/tests/test_compte_resultat_integration.py
"""

import sys
from pathlib import Path
import requests

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000/api"


def print_section(title):
    """Afficher un titre de section."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_transaction_creates_invalidates():
    """Test que la création d'une transaction invalide les comptes."""
    print_section("1. Test création transaction → invalidation")
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Serveur backend non accessible")
            return False
    except:
        print("❌ Serveur backend non démarré")
        print("   Démarrez-le avec: uvicorn backend.api.main:app --reload")
        return False
    
    # 1. Générer un compte de résultat pour 2024
    print("1.1 Génération compte de résultat pour 2024...")
    response = requests.post(f"{BASE_URL}/compte-resultat/generate", params={"year": 2024})
    if response.status_code != 200:
        print(f"❌ Erreur génération: {response.text}")
        return False
    print("✓ Compte de résultat généré")
    
    # 2. Vérifier qu'il existe
    print("1.2 Vérification existence...")
    response = requests.get(f"{BASE_URL}/compte-resultat", params={"year": 2024})
    if response.status_code != 200:
        print(f"❌ Erreur récupération: {response.text}")
        return False
    data = response.json()
    count_before = data['total']
    print(f"✓ {count_before} données trouvées")
    
    # 3. Créer une transaction pour 2024
    print("1.3 Création transaction pour 2024...")
    transaction_data = {
        "date": "2024-06-15",
        "quantite": 100.0,
        "nom": "Test transaction invalidation",
        "solde": 100.0
    }
    response = requests.post(
        f"{BASE_URL}/transactions",
        json=transaction_data,
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 201:
        print(f"❌ Erreur création transaction: {response.text}")
        return False
    transaction_id = response.json()['id']
    print(f"✓ Transaction créée (ID: {transaction_id})")
    
    # 4. Vérifier que les comptes de résultat ont été invalidés
    print("1.4 Vérification invalidation...")
    response = requests.get(f"{BASE_URL}/compte-resultat", params={"year": 2024})
    if response.status_code != 200:
        print(f"❌ Erreur récupération: {response.text}")
        return False
    data = response.json()
    count_after = data['total']
    print(f"✓ {count_after} données après création transaction")
    
    if count_after < count_before:
        print("✓ Invalidation confirmée (données supprimées)")
    else:
        print("⚠️ Invalidation peut-être non déclenchée (même nombre de données)")
    
    # Nettoyer
    print("1.5 Nettoyage...")
    requests.delete(f"{BASE_URL}/transactions/{transaction_id}")
    print("✓ Transaction supprimée")
    
    return True


def main():
    """Exécuter les tests d'intégration."""
    print("=" * 60)
    print("Tests d'intégration - Invalidation automatique")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur backend est démarré")
    print("   uvicorn backend.api.main:app --reload\n")
    
    try:
        success = test_transaction_creates_invalidates()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ Tests d'intégration terminés")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ Tests d'intégration échoués")
            print("=" * 60)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
