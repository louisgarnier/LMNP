"""
Tests unitaires pour csv_utils.py

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.utils.csv_utils import (
    read_csv_safely,
    detect_column_mapping,
    validate_transactions,
    preview_transactions
)


def test_read_csv_safely_utf8_semicolon():
    """Test lecture CSV UTF-8 avec séparateur ;"""
    print("\n📋 Test 1: Lecture CSV UTF-8 avec séparateur ;")
    
    csv_content = "Date;amount;name;Solde\n17/08/2021;-15;SOUSCRIPTION PART SOCIALE A;-15\n02/09/2021;1000;VIR INST LOUIS GARNIER;985"
    csv_bytes = csv_content.encode('utf-8')
    
    df, encoding, separator = read_csv_safely(csv_bytes, "test.csv")
    
    assert encoding == 'utf-8', f"❌ Encodage attendu: utf-8, obtenu: {encoding}"
    assert separator == ';', f"❌ Séparateur attendu: ;, obtenu: {separator}"
    assert len(df.columns) == 4, f"❌ Nombre de colonnes attendu: 4, obtenu: {len(df.columns)}"
    assert len(df) == 2, f"❌ Nombre de lignes attendu: 2, obtenu: {len(df)}"
    print("✅ Test réussi")


def test_read_csv_safely_latin1_comma():
    """Test lecture CSV Latin-1 avec séparateur ,"""
    print("\n📋 Test 2: Lecture CSV Latin-1 avec séparateur ,")
    
    csv_content = "Date,amount,name,Solde\n17/08/2021,-15,SOUSCRIPTION PART SOCIALE A,-15"
    csv_bytes = csv_content.encode('latin-1')
    
    df, encoding, separator = read_csv_safely(csv_bytes, "test.csv")
    
    assert encoding in ['latin-1', 'utf-8'], f"❌ Encodage attendu: latin-1 ou utf-8, obtenu: {encoding}"
    assert separator == ',', f"❌ Séparateur attendu: ,, obtenu: {separator}"
    assert len(df.columns) == 4, f"❌ Nombre de colonnes attendu: 4, obtenu: {len(df.columns)}"
    print("✅ Test réussi")


def test_detect_column_mapping():
    """Test détection mapping colonnes"""
    print("\n📋 Test 3: Détection mapping colonnes")
    
    df = pd.DataFrame({
        'Date': ['17/08/2021', '02/09/2021'],
        'amount': [-15, 1000],
        'name': ['SOUSCRIPTION', 'VIR INST'],
        'Solde': [-15, 985]
    })
    
    mapping = detect_column_mapping(df)

    assert 'date' in mapping.values(), "❌ Mapping date manquant"
    assert 'quantite' in mapping.values(), "❌ Mapping quantite manquant"
    assert 'nom' in mapping.values(), "❌ Mapping nom manquant"
    # Le solde n'est plus mappé depuis les fichiers CSV, il est calculé
    # automatiquement (voir docstring de detect_column_mapping) — assertion
    # 'solde' retirée car ce comportement est un changement de produit
    # antérieur à ce test, pas une régression (Bloc A Task 8).
    assert 'solde' not in mapping.values(), "❌ 'solde' ne devrait plus être mappé depuis le CSV"

    # Vérifier les mappings spécifiques
    date_col = [k for k, v in mapping.items() if v == 'date'][0]
    assert date_col == 'Date', f"❌ Colonne date attendue: Date, obtenue: {date_col}"
    
    print(f"✅ Mapping détecté: {mapping}")
    print("✅ Test réussi")


def test_detect_column_mapping_variants():
    """Test détection mapping avec variantes de noms"""
    print("\n📋 Test 4: Détection mapping avec variantes")
    
    # Test avec Montant au lieu de amount
    df1 = pd.DataFrame({
        'Date': ['17/08/2021'],
        'Montant': [-15],
        'Libellé': ['SOUSCRIPTION'],
        'Solde': [-15]
    })
    
    mapping1 = detect_column_mapping(df1)
    assert 'quantite' in mapping1.values(), "❌ Mapping quantite manquant avec 'Montant'"
    assert 'nom' in mapping1.values(), "❌ Mapping nom manquant avec 'Libellé'"
    print("✅ Test variantes réussi")


def test_validate_transactions():
    """Test validation transactions"""
    print("\n📋 Test 5: Validation transactions")
    
    df = pd.DataFrame({
        'Date': ['17/08/2021', '02/09/2021', 'invalid_date'],
        'amount': [-15, 1000, 'invalid'],
        'name': ['SOUSCRIPTION', 'VIR INST', ''],
        'Solde': [-15, 985, 100]
    })
    
    column_mapping = {
        'Date': 'date',
        'amount': 'quantite',
        'name': 'nom',
        'Solde': 'solde'
    }
    
    df_clean, errors = validate_transactions(df, column_mapping)
    
    # Vérifier que les lignes invalides ont été supprimées
    assert len(df_clean) <= len(df), "❌ Les lignes invalides n'ont pas été supprimées"
    
    # Vérifier que les dates valides sont parsées
    date_col = 'Date'
    if date_col in df_clean.columns:
        assert pd.api.types.is_datetime64_any_dtype(df_clean[date_col]), "❌ Les dates ne sont pas au format datetime"
    
    print(f"✅ Validation réussie. Erreurs: {errors}")
    print(f"✅ Lignes après validation: {len(df_clean)} (sur {len(df)} initiales)")
    print("✅ Test réussi")


def test_validate_transactions_dates_dd_mm_yyyy():
    """Test validation dates au format DD/MM/YYYY"""
    print("\n📋 Test 6: Validation dates DD/MM/YYYY")
    
    df = pd.DataFrame({
        'Date': ['17/08/2021', '02/09/2021', '31/12/2020'],
        'amount': [-15, 1000, 500],
        'name': ['TEST1', 'TEST2', 'TEST3'],
        'Solde': [-15, 985, 1485]
    })
    
    column_mapping = {
        'Date': 'date',
        'amount': 'quantite',
        'name': 'nom',
        'Solde': 'solde'
    }
    
    df_clean, errors = validate_transactions(df, column_mapping)
    
    # Vérifier que toutes les dates valides sont parsées
    assert len(df_clean) == 3, f"❌ Toutes les dates devraient être valides, {len(df_clean)} lignes restantes"
    assert pd.api.types.is_datetime64_any_dtype(df_clean['Date']), "❌ Les dates ne sont pas au format datetime"
    
    print("✅ Test validation dates réussi")


def test_validate_transactions_montants_virgule():
    """Test validation montants avec virgule"""
    print("\n📋 Test 7: Validation montants avec virgule")
    
    df = pd.DataFrame({
        'Date': ['17/08/2021', '02/09/2021'],
        'amount': ['-15,50', '1000,25'],
        'name': ['TEST1', 'TEST2'],
        'Solde': ['-15,50', '1000,25']
    })
    
    column_mapping = {
        'Date': 'date',
        'amount': 'quantite',
        'name': 'nom',
        'Solde': 'solde'
    }
    
    df_clean, errors = validate_transactions(df, column_mapping)
    
    # Vérifier que les montants avec virgule sont convertis
    assert pd.api.types.is_numeric_dtype(df_clean['amount']), "❌ Les montants ne sont pas numériques"
    
    print("✅ Test validation montants avec virgule réussi")


def test_preview_transactions():
    """Test preview transactions"""
    print("\n📋 Test 8: Preview transactions")
    
    df = pd.DataFrame({
        'Date': ['17/08/2021', '02/09/2021', '05/10/2021'],
        'amount': [-15, 1000, -100],
        'name': ['SOUSCRIPTION', 'VIR INST', 'VIR SEPA'],
        'Solde': [-15, 985, 885]
    })
    
    # Convertir les dates
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    column_mapping = {
        'Date': 'date',
        'amount': 'quantite',
        'name': 'nom',
        'Solde': 'solde'
    }
    
    preview = preview_transactions(df, column_mapping, num_rows=2)
    
    assert len(preview) == 2, f"❌ Preview devrait contenir 2 lignes, obtenu: {len(preview)}"
    assert 'date' in preview[0], "❌ Colonne date manquante dans preview"
    assert 'quantite' in preview[0], "❌ Colonne quantite manquante dans preview"
    assert 'nom' in preview[0], "❌ Colonne nom manquante dans preview"
    assert 'solde' in preview[0], "❌ Colonne solde manquante dans preview"
    
    # Vérifier format date
    assert preview[0]['date'] == '17/08/2021', f"❌ Date formatée incorrectement: {preview[0]['date']}"
    
    print(f"✅ Preview: {preview}")
    print("✅ Test preview réussi")


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 60)
    print("🧪 Tests: CSV Utils")
    print("=" * 60)
    
    try:
        test_read_csv_safely_utf8_semicolon()
        test_read_csv_safely_latin1_comma()
        test_detect_column_mapping()
        test_detect_column_mapping_variants()
        test_validate_transactions()
        test_validate_transactions_dates_dd_mm_yyyy()
        test_validate_transactions_montants_virgule()
        test_preview_transactions()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés avec succès!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()

