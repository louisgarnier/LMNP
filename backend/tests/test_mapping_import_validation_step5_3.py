"""
Test pour Step 5.3 : Validation des mappings importés contre allowed_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import pandas as pd
import io

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Mapping, AllowedMapping
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel,
    validate_mapping,
    validate_level3_value
)


def create_test_excel_file(valid_rows, invalid_rows):
    """Crée un fichier Excel de test avec des lignes valides et invalides."""
    data = []
    
    # Ajouter les lignes valides
    for row in valid_rows:
        data.append({
            'nom': row.get('nom', ''),
            'level_1': row.get('level_1', ''),
            'level_2': row.get('level_2', ''),
            'level_3': row.get('level_3', '')
        })
    
    # Ajouter les lignes invalides
    for row in invalid_rows:
        data.append({
            'nom': row.get('nom', ''),
            'level_1': row.get('level_1', ''),
            'level_2': row.get('level_2', ''),
            'level_3': row.get('level_3', '')
        })
    
    df = pd.DataFrame(data)
    return df


def test_validation_functions():
    """Test 1 : Vérifier que les fonctions de validation fonctionnent."""
    print("\n" + "=" * 60)
    print("Test 1 : Fonctions de validation")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # S'assurer que des données existent dans allowed_mappings
        count = db.query(AllowedMapping).count()
        if count == 0:
            print("  Chargement des combinaisons depuis Excel...")
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
                print("  ✓ Combinaisons chargées")
            else:
                print("  ⚠ Fichier Excel non trouvé")
                return
        
        # Récupérer une combinaison valide
        valid_mapping = db.query(AllowedMapping).first()
        if valid_mapping:
            # Test validation d'une combinaison valide
            is_valid = validate_mapping(
                db,
                valid_mapping.level_1,
                valid_mapping.level_2,
                valid_mapping.level_3
            )
            assert is_valid, "La combinaison valide devrait être valide"
            print(f"  ✓ Combinaison valide validée: ({valid_mapping.level_1}, {valid_mapping.level_2}, {valid_mapping.level_3})")
            
            # Test validation d'une combinaison invalide
            is_valid = validate_mapping(db, "INVALIDE", "INVALIDE", "INVALIDE")
            assert not is_valid, "La combinaison invalide ne devrait pas être valide"
            print("  ✓ Combinaison invalide correctement rejetée")
        
        # Test validation level_3
        assert validate_level3_value("Passif"), "'Passif' devrait être valide"
        assert validate_level3_value("Produits"), "'Produits' devrait être valide"
        assert not validate_level3_value("INVALIDE"), "'INVALIDE' ne devrait pas être valide"
        print("  ✓ Validation level_3 fonctionne")
        
    finally:
        db.close()
    
    print("✓ Test 1 réussi\n")


def test_import_with_mixed_data():
    """Test 2 : Tester l'import avec un fichier mixte (valides + invalides)."""
    print("=" * 60)
    print("Test 2 : Import avec fichier mixte (valides + invalides)")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # S'assurer que des données existent dans allowed_mappings
        count = db.query(AllowedMapping).count()
        if count == 0:
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            if excel_path.exists():
                load_allowed_mappings_from_excel(db, excel_path)
        
        # Récupérer une combinaison valide pour le test
        valid_mapping = db.query(AllowedMapping).first()
        if not valid_mapping:
            print("  ⚠ Aucune combinaison valide disponible")
            return
        
        # Nettoyer les mappings de test
        db.query(Mapping).filter(Mapping.nom.like("TEST_%")).delete()
        db.commit()
        
        # Créer un fichier Excel de test avec des lignes valides et invalides
        valid_rows = [
            {
                'nom': 'TEST_VALID_1',
                'level_1': valid_mapping.level_1,
                'level_2': valid_mapping.level_2,
                'level_3': valid_mapping.level_3
            },
            {
                'nom': 'TEST_VALID_2',
                'level_1': valid_mapping.level_1,
                'level_2': valid_mapping.level_2,
                'level_3': valid_mapping.level_3
            }
        ]
        
        invalid_rows = [
            {
                'nom': 'TEST_INVALID_1',
                'level_1': 'INVALIDE',
                'level_2': 'INVALIDE',
                'level_3': 'INVALIDE'
            },
            {
                'nom': 'TEST_INVALID_2',
                'level_1': valid_mapping.level_1,
                'level_2': valid_mapping.level_2,
                'level_3': 'INVALIDE_LEVEL3'  # level_3 invalide
            }
        ]
        
        df = create_test_excel_file(valid_rows, invalid_rows)
        
        # Simuler la validation comme dans l'endpoint
        imported_count = 0
        errors_count = 0
        errors_messages = []
        
        for idx, row in df.iterrows():
            nom_value = str(row['nom']).strip()
            level_1_value = str(row['level_1']).strip()
            level_2_value = str(row['level_2']).strip()
            level_3_value = str(row['level_3']).strip() if pd.notna(row['level_3']) else None
            
            # Validation level_3
            if level_3_value and not validate_level3_value(level_3_value):
                errors_count += 1
                errors_messages.append(f"Ligne {idx + 2}: erreur - mapping inconnu (level_3 invalide)")
                continue
            
            # Validation combinaison
            if not validate_mapping(db, level_1_value, level_2_value, level_3_value):
                errors_count += 1
                errors_messages.append(f"Ligne {idx + 2}: erreur - mapping inconnu (combinaison non autorisée)")
                continue
            
            # Si valide, créer le mapping
            existing = db.query(Mapping).filter(Mapping.nom == nom_value).first()
            if not existing:
                mapping = Mapping(
                    nom=nom_value,
                    level_1=level_1_value,
                    level_2=level_2_value,
                    level_3=level_3_value,
                    is_prefix_match=True,
                    priority=0
                )
                db.add(mapping)
                imported_count += 1
        
        db.commit()
        
        print(f"  Lignes valides: {len(valid_rows)}")
        print(f"  Lignes invalides: {len(invalid_rows)}")
        print(f"  ✓ {imported_count} mapping(s) importé(s)")
        print(f"  ✓ {errors_count} erreur(s) détectée(s)")
        
        assert imported_count == len(valid_rows), f"Toutes les lignes valides devraient être importées ({imported_count} != {len(valid_rows)})"
        assert errors_count == len(invalid_rows), f"Toutes les lignes invalides devraient être rejetées ({errors_count} != {len(invalid_rows)})"
        
        # Vérifier que les mappings valides ont été créés
        for row in valid_rows:
            mapping = db.query(Mapping).filter(Mapping.nom == row['nom']).first()
            assert mapping is not None, f"Le mapping '{row['nom']}' devrait être créé"
        
        # Vérifier que les mappings invalides n'ont pas été créés
        for row in invalid_rows:
            mapping = db.query(Mapping).filter(Mapping.nom == row['nom']).first()
            assert mapping is None, f"Le mapping '{row['nom']}' ne devrait pas être créé"
        
        print("  ✓ Mappings valides créés, mappings invalides rejetés")
        
        # Nettoyer
        db.query(Mapping).filter(Mapping.nom.like("TEST_%")).delete()
        db.commit()
        
    finally:
        db.close()
    
    print("✓ Test 2 réussi\n")


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("TESTS - Step 5.3 : Validation des mappings importés")
    print("=" * 60)
    
    try:
        # Initialiser la base de données
        init_database()
        
        test_validation_functions()
        test_import_with_mixed_data()
        
        print("=" * 60)
        print("✓ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
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

