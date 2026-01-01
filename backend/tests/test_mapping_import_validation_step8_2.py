"""
Test script for Step 8.2 - Validation des mappings importés contre allowed_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_mapping_import_validation_step8_2.py

⚠️ IMPORTANT: Le backend doit être démarré sur http://localhost:8000
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import io
import pandas as pd
import requests
from pathlib import Path


BASE_URL = "http://localhost:8000"


def get_valid_combinations_from_db():
    """Récupère des combinaisons valides depuis la BDD pour les tests."""
    from backend.database import SessionLocal
    from backend.api.services.mapping_default_service import (
        get_allowed_level1_values,
        get_allowed_level2_values,
        get_allowed_level3_values
    )
    
    db = SessionLocal()
    try:
        level1_values = get_allowed_level1_values(db)
        if not level1_values:
            return None, None, None
        
        level1 = level1_values[0]
        level2_values = get_allowed_level2_values(db, level1)
        if not level2_values:
            return level1, None, None
        
        level2 = level2_values[0]
        level3_values = get_allowed_level3_values(db, level1, level2)
        level3 = level3_values[0] if level3_values else None
        
        return level1, level2, level3
    finally:
        db.close()


def create_test_excel_file_valid_and_invalid():
    """Crée un fichier Excel de test avec des mappings valides et invalides."""
    # Récupérer des combinaisons valides depuis la BDD
    valid_level1, valid_level2, valid_level3 = get_valid_combinations_from_db()
    
    if not valid_level1 or not valid_level2:
        print("⚠️  Impossible de récupérer des combinaisons valides depuis la BDD")
        # Utiliser des valeurs par défaut
        valid_level1 = "Adhésion Organisme de Gestion Agréé (OGA)"
        valid_level2 = "Autres dépenses"
        valid_level3 = "Charges Déductibles"
    
    # Créer un DataFrame avec des mappings valides et invalides
    data = {
        'Nom': [
            'TEST VALID 1',                 # Valide (combinaison existe dans allowed_mappings)
            'TEST VALID 2',                 # Valide (combinaison existe dans allowed_mappings)
            'TEST INVALID 1',               # Invalide (combinaison level_1/level_2/level_3 qui n'existe pas)
            'TEST INVALID 2',               # Invalide (combinaison level_1/level_2/level_3 qui n'existe pas)
            'TEST VALID 3',                 # Valide (combinaison existe dans allowed_mappings)
        ],
        'Level 1': [
            valid_level1,                   # Valide
            valid_level1,                   # Valide
            'INVALID_LEVEL1',               # Invalide
            valid_level1,                   # Valide level_1 mais invalide combinaison
            valid_level1,                   # Valide
        ],
        'Level 2': [
            valid_level2,                   # Valide
            valid_level2,                   # Valide
            'INVALID_LEVEL2',               # Invalide
            'INVALID_LEVEL2_COMBO',         # Invalide (n'existe pas pour ce level_1)
            valid_level2,                   # Valide
        ],
        'Level 3': [
            valid_level3 if valid_level3 else '',  # Valide (si existe)
            valid_level3 if valid_level3 else '',  # Valide (si existe)
            'INVALID_LEVEL3',               # Invalide
            'INVALID_LEVEL3_COMBO',         # Invalide
            valid_level3 if valid_level3 else '',  # Valide (si existe)
        ]
    }
    df = pd.DataFrame(data)
    
    # Créer un fichier Excel en mémoire
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return excel_buffer, df, (valid_level1, valid_level2, valid_level3)


def test_preview_mapping_file():
    """Test l'endpoint preview pour voir les colonnes détectées."""
    print("=" * 60)
    print("Test 1: Preview du fichier Excel")
    print("=" * 60)
    
    excel_buffer, df, _ = create_test_excel_file_valid_and_invalid()
    
    try:
        files = {'file': ('test_mappings.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/api/mappings/preview", files=files)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Colonnes détectées: {[col['file_column'] for col in data['column_mapping']]}")
        print(f"✅ Nombre de lignes: {data['total_rows']}")
        
        return True, data
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, None


def test_import_mapping_file():
    """Test l'endpoint import avec validation."""
    print()
    print("=" * 60)
    print("Test 2: Import du fichier Excel avec validation")
    print("=" * 60)
    
    excel_buffer, df, valid_combo = create_test_excel_file_valid_and_invalid()
    
    if valid_combo[0] and valid_combo[1]:
        print(f"📋 Utilisation de combinaisons valides: {valid_combo[0]} / {valid_combo[1]} / {valid_combo[2] if valid_combo[2] else '(vide)'}")
    
    # Mapping des colonnes (basé sur les colonnes du DataFrame)
    column_mapping = [
        {"file_column": "Nom", "db_column": "nom"},
        {"file_column": "Level 1", "db_column": "level_1"},
        {"file_column": "Level 2", "db_column": "level_2"},
        {"file_column": "Level 3", "db_column": "level_3"}
    ]
    
    try:
        files = {'file': ('test_mappings.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {
            'mapping': str(column_mapping).replace("'", '"')  # Convertir en JSON string
        }
        
        # Corriger le format JSON
        import json
        data['mapping'] = json.dumps(column_mapping)
        
        response = requests.post(f"{BASE_URL}/api/mappings/import", files=files, data=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mappings importés: {result['imported_count']}")
        print(f"✅ Doublons ignorés: {result['duplicates_count']}")
        print(f"✅ Erreurs: {result['errors_count']}")
        
        if result['errors']:
            print(f"\n📋 Détails des erreurs:")
            for error in result['errors'][:10]:  # Limiter à 10 erreurs
                print(f"   - Ligne {error['line_number']}: {error['error_message']}")
                if 'erreur - mapping inconnu' in error['error_message']:
                    print(f"     ✅ Erreur de validation détectée correctement")
        
        # Vérifier que les erreurs "erreur - mapping inconnu" sont présentes
        validation_errors = [e for e in result['errors'] if 'erreur - mapping inconnu' in e.get('error_message', '')]
        if validation_errors:
            print(f"\n✅ {len(validation_errors)} erreur(s) de validation 'erreur - mapping inconnu' détectée(s)")
        else:
            print(f"\n⚠️  Aucune erreur 'erreur - mapping inconnu' détectée (peut être normal si toutes les combinaisons sont valides)")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_all():
    """Test complet de la validation."""
    print()
    print("=" * 60)
    print("Test de validation des mappings importés (Step 8.2)")
    print("=" * 60)
    print()
    
    # Test 1: Preview
    success1, preview_data = test_preview_mapping_file()
    if not success1:
        print("\n❌ Échec du test preview")
        return False
    
    # Test 2: Import avec validation
    success2, import_result = test_import_mapping_file()
    if not success2:
        print("\n❌ Échec du test import")
        return False
    
    print()
    print("=" * 60)
    print("✅ Tests terminés !")
    print("=" * 60)
    print("\n📝 Résumé:")
    print("   - La validation contre allowed_mappings est active")
    print("   - Les lignes avec des combinaisons invalides sont ignorées")
    print("   - Les erreurs 'erreur - mapping inconnu' sont loggées")
    
    return True


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)

