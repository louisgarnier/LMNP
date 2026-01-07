"""
Test pour Step 5.1 : Création de la table allowed_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect
from backend.database.connection import SessionLocal, init_database, engine
from backend.database.models import AllowedMapping, Base
from backend.api.services.mapping_obligatoire_service import (
    load_allowed_mappings_from_excel,
    get_allowed_level1_values,
    get_allowed_level2_values,
    get_allowed_level3_values,
    validate_mapping,
    validate_level3_value,
    reset_to_hardcoded_values,
    ALLOWED_LEVEL_3_VALUES
)


def test_table_creation():
    """Test 1 : Vérifier que la table allowed_mappings est créée."""
    print("\n" + "=" * 60)
    print("Test 1 : Création de la table allowed_mappings")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Vérifier que la table existe
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert 'allowed_mappings' in tables, "La table 'allowed_mappings' n'existe pas"
    print("✓ Table 'allowed_mappings' créée")
    
    # Vérifier les colonnes
    columns = [col['name'] for col in inspector.get_columns('allowed_mappings')]
    expected_columns = ['id', 'level_1', 'level_2', 'level_3', 'is_hardcoded', 'created_at', 'updated_at']
    
    for col in expected_columns:
        assert col in columns, f"Colonne '{col}' manquante"
    
    print(f"✓ Colonnes vérifiées : {', '.join(expected_columns)}")
    
    # Vérifier l'index unique
    indexes = inspector.get_indexes('allowed_mappings')
    unique_indexes = [idx for idx in indexes if idx['unique']]
    
    assert len(unique_indexes) > 0, "Index unique manquant"
    print("✓ Index unique vérifié")
    
    print("✓ Test 1 réussi\n")


def test_load_from_excel():
    """Test 2 : Charger les combinaisons depuis le fichier Excel."""
    print("=" * 60)
    print("Test 2 : Chargement depuis le fichier Excel")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Nettoyer la table avant le test
        db.query(AllowedMapping).delete()
        db.commit()
        print("  Table nettoyée avant le test")
        
        # Charger depuis Excel
        excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
        
        if not excel_path.exists():
            print(f"⚠ ATTENTION : Le fichier Excel n'existe pas : {excel_path}")
            print("   Ce test sera ignoré. Exécutez le script load_hardcoded_mappings.py d'abord.")
            return
        
        loaded_count = load_allowed_mappings_from_excel(db, excel_path)
        
        assert loaded_count > 0, "Aucune combinaison chargée"
        print(f"✓ {loaded_count} combinaisons chargées")
        
        # Vérifier que toutes sont marquées comme hard codées
        hardcoded_count = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        
        assert hardcoded_count == loaded_count, f"Toutes les combinaisons doivent être hard codées ({hardcoded_count} != {loaded_count})"
        print(f"✓ Toutes les combinaisons sont marquées is_hardcoded = True")
        
        # Vérifier qu'on a bien environ 50 combinaisons (peut être 49 ou 50 selon les lignes valides)
        total_count = db.query(AllowedMapping).count()
        print(f"✓ Total de combinaisons dans la table : {total_count}")
        
        assert total_count >= 49, f"On devrait avoir au moins 49 combinaisons ({total_count} < 49)"
        
    finally:
        db.close()
    
    print("✓ Test 2 réussi\n")


def test_get_values():
    """Test 3 : Récupérer les valeurs level_1, level_2, level_3."""
    print("=" * 60)
    print("Test 3 : Récupération des valeurs autorisées")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Récupérer toutes les valeurs level_1
        level1_values = get_allowed_level1_values(db)
        assert len(level1_values) > 0, "Aucune valeur level_1 trouvée"
        print(f"✓ {len(level1_values)} valeurs level_1 uniques trouvées")
        print(f"   Exemples : {level1_values[:3]}")
        
        # Récupérer les level_2 pour un level_1
        if level1_values:
            level2_values = get_allowed_level2_values(db, level1_values[0])
            print(f"✓ {len(level2_values)} valeurs level_2 trouvées pour '{level1_values[0]}'")
            if level2_values:
                print(f"   Exemples : {level2_values[:3]}")
                
                # Récupérer les level_3 pour un couple (level_1, level_2)
                level3_values = get_allowed_level3_values(db, level1_values[0], level2_values[0])
                print(f"✓ {len(level3_values)} valeurs level_3 trouvées pour ('{level1_values[0]}', '{level2_values[0]}')")
                if level3_values:
                    print(f"   Exemples : {level3_values}")
        
    finally:
        db.close()
    
    print("✓ Test 3 réussi\n")


def test_validate_mapping():
    """Test 4 : Valider une combinaison."""
    print("=" * 60)
    print("Test 4 : Validation de combinaisons")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Récupérer une combinaison existante
        existing = db.query(AllowedMapping).first()
        
        if existing:
            # Valider une combinaison existante
            is_valid = validate_mapping(db, existing.level_1, existing.level_2, existing.level_3)
            assert is_valid, "La combinaison existante devrait être valide"
            print(f"✓ Combinaison existante validée : ({existing.level_1}, {existing.level_2}, {existing.level_3})")
            
            # Valider une combinaison inexistante
            is_valid = validate_mapping(db, "INEXISTANT", "INEXISTANT", "INEXISTANT")
            assert not is_valid, "La combinaison inexistante ne devrait pas être valide"
            print("✓ Combinaison inexistante correctement rejetée")
        
    finally:
        db.close()
    
    print("✓ Test 4 réussi\n")


def test_validate_level3():
    """Test 5 : Valider les valeurs level_3."""
    print("=" * 60)
    print("Test 5 : Validation des valeurs level_3")
    print("=" * 60)
    
    # Tester les valeurs autorisées
    for value in ALLOWED_LEVEL_3_VALUES:
        assert validate_level3_value(value), f"'{value}' devrait être valide"
        print(f"✓ '{value}' est valide")
    
    # Tester une valeur non autorisée
    assert not validate_level3_value("INVALIDE"), "'INVALIDE' ne devrait pas être valide"
    print("✓ Valeur invalide correctement rejetée")
    
    # Tester None (level_3 est nullable)
    assert validate_level3_value(None), "None devrait être valide (level_3 est nullable)"
    print("✓ None est valide (level_3 est nullable)")
    
    print("✓ Test 5 réussi\n")


def test_reset():
    """Test 6 : Reset (supprimer les combinaisons non hard codées)."""
    print("=" * 60)
    print("Test 6 : Reset des combinaisons non hard codées")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Compter les combinaisons hard codées
        hardcoded_before = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        
        # Ajouter une combinaison non hard codée (pour test)
        test_mapping = AllowedMapping(
            level_1="TEST",
            level_2="TEST",
            level_3="Charges Déductibles",
            is_hardcoded=False
        )
        db.add(test_mapping)
        db.commit()
        
        total_before = db.query(AllowedMapping).count()
        print(f"  Avant reset : {total_before} combinaisons ({hardcoded_before} hard codées)")
        
        # Reset
        deleted_count = reset_to_hardcoded_values(db)
        
        total_after = db.query(AllowedMapping).count()
        hardcoded_after = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        
        print(f"  Après reset : {total_after} combinaisons ({hardcoded_after} hard codées)")
        print(f"  {deleted_count} combinaison(s) supprimée(s)")
        
        assert hardcoded_before == hardcoded_after, "Les combinaisons hard codées ne doivent pas être supprimées"
        assert total_after == hardcoded_after, "Seules les combinaisons hard codées doivent rester"
        
        print("✓ Reset fonctionne correctement")
        
    finally:
        db.close()
    
    print("✓ Test 6 réussi\n")


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("TESTS - Step 5.1 : Création de la table allowed_mappings")
    print("=" * 60)
    
    try:
        test_table_creation()
        test_load_from_excel()
        test_get_values()
        test_validate_mapping()
        test_validate_level3()
        test_reset()
        
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

