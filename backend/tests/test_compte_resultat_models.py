"""
Test script to validate CompteResultatMapping and CompteResultatData models.

Run with: python -m pytest backend/tests/test_compte_resultat_models.py -v
Or: python backend/tests/test_compte_resultat_models.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import CompteResultatMapping, CompteResultatData
from sqlalchemy import inspect


def test_tables_exist():
    """Test that compte_resultat_mappings and compte_resultat_data tables exist."""
    print("Testing tables existence...")
    init_database()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "compte_resultat_mappings" in tables, "Table 'compte_resultat_mappings' not found"
    print("✓ Table 'compte_resultat_mappings' exists")
    
    assert "compte_resultat_data" in tables, "Table 'compte_resultat_data' not found"
    print("✓ Table 'compte_resultat_data' exists")


def test_mapping_table_columns():
    """Test that compte_resultat_mappings table has correct columns."""
    print("\nTesting compte_resultat_mappings table columns...")
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('compte_resultat_mappings')}
    
    # Vérifier les colonnes requises
    required_columns = [
        'id', 'category_name', 'level_1_values', 'created_at', 'updated_at'
    ]
    
    for col_name in required_columns:
        assert col_name in columns, f"Column '{col_name}' not found"
        print(f"✓ Column '{col_name}' exists")
    
    # Vérifier les contraintes nullable
    # Note: En SQLite, PRIMARY KEY AUTOINCREMENT peut être marquée nullable=True par SQLAlchemy
    # mais ne peut pas être NULL en pratique
    assert columns['category_name']['nullable'] == False, f"Column 'category_name' should be NOT NULL, got nullable={columns['category_name']['nullable']}"
    assert columns['level_1_values']['nullable'] == True, f"Column 'level_1_values' should be NULL, got nullable={columns['level_1_values']['nullable']}"  # Optionnel
    # Note: created_at et updated_at peuvent être nullable en SQLite même avec default
    print("✓ All columns have correct nullable constraints")


def test_data_table_columns():
    """Test that compte_resultat_data table has correct columns."""
    print("\nTesting compte_resultat_data table columns...")
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('compte_resultat_data')}
    
    # Vérifier les colonnes requises
    required_columns = [
        'id', 'annee', 'category_name', 'amount', 'created_at', 'updated_at'
    ]
    
    for col_name in required_columns:
        assert col_name in columns, f"Column '{col_name}' not found"
        print(f"✓ Column '{col_name}' exists")
    
    # Vérifier les contraintes nullable
    # Note: En SQLite, PRIMARY KEY AUTOINCREMENT peut être marquée nullable=True par SQLAlchemy
    # mais ne peut pas être NULL en pratique
    assert columns['annee']['nullable'] == False, f"Column 'annee' should be NOT NULL, got nullable={columns['annee']['nullable']}"
    assert columns['category_name']['nullable'] == False, f"Column 'category_name' should be NOT NULL, got nullable={columns['category_name']['nullable']}"
    assert columns['amount']['nullable'] == False, f"Column 'amount' should be NOT NULL, got nullable={columns['amount']['nullable']}"
    # Note: created_at et updated_at peuvent être nullable en SQLite même avec default
    print("✓ All columns have correct nullable constraints")


def test_create_mapping():
    """Test creating a CompteResultatMapping."""
    print("\nTesting CompteResultatMapping creation...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Loyers hors charge encaissés"
        ).delete()
        db.commit()
        
        # Créer un mapping de test
        level_1_values = json.dumps(["LOYERS", "REVENUS"])
        test_mapping = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values=level_1_values
        )
        
        db.add(test_mapping)
        db.commit()
        
        # Vérifier que le mapping a été créé
        assert test_mapping.id is not None, "CompteResultatMapping ID should be set after commit"
        print(f"✓ CompteResultatMapping created with ID: {test_mapping.id}")
        
        # Vérifier les valeurs
        assert test_mapping.category_name == "Loyers hors charge encaissés"
        assert test_mapping.level_1_values == level_1_values
        assert test_mapping.created_at is not None
        assert test_mapping.updated_at is not None
        print("✓ All fields are correctly set")
        
        # Nettoyer
        db.delete(test_mapping)
        db.commit()
        
    finally:
        db.close()


def test_create_mapping_without_level1():
    """Test creating a CompteResultatMapping without level_1_values."""
    print("\nTesting CompteResultatMapping creation without level_1_values...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Charges d'amortissements"
        ).delete()
        db.commit()
        
        # Créer un mapping sans level_1_values (catégorie spéciale)
        test_mapping = CompteResultatMapping(
            category_name="Charges d'amortissements",
            level_1_values=None
        )
        
        db.add(test_mapping)
        db.commit()
        
        # Vérifier que le mapping a été créé
        assert test_mapping.id is not None
        assert test_mapping.level_1_values is None
        print("✓ CompteResultatMapping created without level_1_values")
        
        # Nettoyer
        db.delete(test_mapping)
        db.commit()
        
    finally:
        db.close()


def test_read_mapping():
    """Test reading a CompteResultatMapping."""
    print("\nTesting CompteResultatMapping reading...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Charges de copropriété"
        ).delete()
        db.commit()
        
        # Créer un mapping de test
        level_1_values = json.dumps(["CHARGES", "COPROPRIETE"])
        test_mapping = CompteResultatMapping(
            category_name="Charges de copropriété",
            level_1_values=level_1_values
        )
        
        db.add(test_mapping)
        db.commit()
        mapping_id = test_mapping.id
        
        # Lire le mapping
        read_mapping = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.id == mapping_id
        ).first()
        
        assert read_mapping is not None, "CompteResultatMapping should be found"
        assert read_mapping.category_name == "Charges de copropriété"
        assert read_mapping.level_1_values == level_1_values
        print("✓ CompteResultatMapping can be read correctly")
        
        # Nettoyer
        db.delete(read_mapping)
        db.commit()
        
    finally:
        db.close()


def test_update_mapping():
    """Test updating a CompteResultatMapping."""
    print("\nTesting CompteResultatMapping update...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Assurances"
        ).delete()
        db.commit()
        
        # Créer un mapping de test
        test_mapping = CompteResultatMapping(
            category_name="Assurances",
            level_1_values=json.dumps(["ASSURANCE"])
        )
        
        db.add(test_mapping)
        db.commit()
        mapping_id = test_mapping.id
        original_updated_at = test_mapping.updated_at
        
        # Mettre à jour
        test_mapping.level_1_values = json.dumps(["ASSURANCE", "PROTECTION"])
        db.commit()
        db.refresh(test_mapping)
        
        # Vérifier les modifications
        assert test_mapping.level_1_values == json.dumps(["ASSURANCE", "PROTECTION"])
        assert test_mapping.updated_at != original_updated_at, "updated_at should be updated"
        print("✓ CompteResultatMapping can be updated correctly")
        
        # Nettoyer
        db.delete(test_mapping)
        db.commit()
        
    finally:
        db.close()


def test_create_data():
    """Test creating a CompteResultatData."""
    print("\nTesting CompteResultatData creation...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatData).filter(
            CompteResultatData.category_name == "Loyers hors charge encaissés",
            CompteResultatData.annee == 2024
        ).delete()
        db.commit()
        
        # Créer une donnée de test
        test_data = CompteResultatData(
            annee=2024,
            category_name="Loyers hors charge encaissés",
            amount=50000.0
        )
        
        db.add(test_data)
        db.commit()
        
        # Vérifier que la donnée a été créée
        assert test_data.id is not None, "CompteResultatData ID should be set after commit"
        print(f"✓ CompteResultatData created with ID: {test_data.id}")
        
        # Vérifier les valeurs
        assert test_data.annee == 2024
        assert test_data.category_name == "Loyers hors charge encaissés"
        assert test_data.amount == 50000.0
        assert test_data.created_at is not None
        assert test_data.updated_at is not None
        print("✓ All fields are correctly set")
        
        # Nettoyer
        db.delete(test_data)
        db.commit()
        
    finally:
        db.close()


def test_read_data():
    """Test reading CompteResultatData."""
    print("\nTesting CompteResultatData reading...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatData).filter(
            CompteResultatData.category_name == "Charges de copropriété",
            CompteResultatData.annee == 2023
        ).delete()
        db.commit()
        
        # Créer une donnée de test
        test_data = CompteResultatData(
            annee=2023,
            category_name="Charges de copropriété",
            amount=12000.0
        )
        
        db.add(test_data)
        db.commit()
        data_id = test_data.id
        
        # Lire la donnée
        read_data = db.query(CompteResultatData).filter(
            CompteResultatData.id == data_id
        ).first()
        
        assert read_data is not None, "CompteResultatData should be found"
        assert read_data.annee == 2023
        assert read_data.category_name == "Charges de copropriété"
        assert read_data.amount == 12000.0
        print("✓ CompteResultatData can be read correctly")
        
        # Nettoyer
        db.delete(read_data)
        db.commit()
        
    finally:
        db.close()


def test_multiple_data_same_category():
    """Test handling multiple CompteResultatData for same category across years."""
    print("\nTesting multiple CompteResultatData for same category...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(CompteResultatData).filter(
            CompteResultatData.category_name == "Loyers hors charge encaissés",
            CompteResultatData.annee.in_([2022, 2023, 2024])
        ).delete()
        db.commit()
        
        # Créer plusieurs données pour la même catégorie sur différentes années
        data_list = [
            CompteResultatData(
                annee=2022,
                category_name="Loyers hors charge encaissés",
                amount=45000.0
            ),
            CompteResultatData(
                annee=2023,
                category_name="Loyers hors charge encaissés",
                amount=48000.0
            ),
            CompteResultatData(
                annee=2024,
                category_name="Loyers hors charge encaissés",
                amount=50000.0
            )
        ]
        
        for data in data_list:
            db.add(data)
        db.commit()
        
        # Vérifier qu'on peut les lire
        all_data = db.query(CompteResultatData).filter(
            CompteResultatData.category_name == "Loyers hors charge encaissés",
            CompteResultatData.annee.in_([2022, 2023, 2024])
        ).all()
        
        assert len(all_data) == 3, f"Expected 3 data entries, got {len(all_data)}"
        print(f"✓ Created and read {len(all_data)} CompteResultatData entries")
        
        # Nettoyer
        for data in all_data:
            db.delete(data)
        db.commit()
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing CompteResultatMapping and CompteResultatData Models")
    print("=" * 60)
    
    try:
        test_tables_exist()
        test_mapping_table_columns()
        test_data_table_columns()
        test_create_mapping()
        test_create_mapping_without_level1()
        test_read_mapping()
        test_update_mapping()
        test_create_data()
        test_read_data()
        test_multiple_data_same_category()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
