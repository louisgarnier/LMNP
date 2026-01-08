"""
Test script to validate AmortizationType model.

Run with: python -m pytest backend/tests/test_amortization_type.py -v
Or: python backend/tests/test_amortization_type.py
"""

import sys
import json
from pathlib import Path
from datetime import date, datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import AmortizationType
from sqlalchemy import inspect


def test_table_exists():
    """Test that amortization_types table exists."""
    print("Testing amortization_types table existence...")
    init_database()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "amortization_types" in tables, "Table 'amortization_types' not found"
    print("✓ Table 'amortization_types' exists")


def test_table_columns():
    """Test that amortization_types table has correct columns."""
    print("\nTesting table columns...")
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('amortization_types')}
    
    # Vérifier les colonnes requises
    required_columns = [
        'id', 'name', 'level_2_value', 'level_1_values',
        'start_date', 'duration', 'annual_amount',
        'created_at', 'updated_at'
    ]
    
    for col_name in required_columns:
        assert col_name in columns, f"Column '{col_name}' not found"
        print(f"✓ Column '{col_name}' exists")
    
    # Vérifier les types (SQLite peut avoir des types différents, on vérifie juste que les colonnes existent)
    assert columns['id']['nullable'] == False
    assert columns['name']['nullable'] == False
    assert columns['level_2_value']['nullable'] == False
    assert columns['level_1_values']['nullable'] == False  # Text/JSON
    assert columns['duration']['nullable'] == False
    assert columns['start_date']['nullable'] == True  # Nullable
    assert columns['annual_amount']['nullable'] == True  # Nullable
    print("✓ All columns have correct nullable constraints")


def test_create_amortization_type():
    """Test creating an AmortizationType."""
    print("\nTesting AmortizationType creation...")
    init_database()
    db = SessionLocal()
    
    try:
        # Créer un type de test
        test_type = AmortizationType(
            name="Test Immobilisation",
            level_2_value="ammortissements",
            level_1_values=json.dumps(["Test Level 1"]),
            start_date=date(2024, 1, 1),
            duration=10.0,
            annual_amount=1000.0
        )
        
        db.add(test_type)
        db.commit()
        
        # Vérifier que le type a été créé
        retrieved = db.query(AmortizationType).filter(
            AmortizationType.name == "Test Immobilisation"
        ).first()
        
        assert retrieved is not None, "AmortizationType not created"
        assert retrieved.name == "Test Immobilisation"
        assert retrieved.level_2_value == "ammortissements"
        assert json.loads(retrieved.level_1_values) == ["Test Level 1"]
        assert retrieved.start_date == date(2024, 1, 1)
        assert retrieved.duration == 10.0
        assert retrieved.annual_amount == 1000.0
        
        print("✓ AmortizationType created successfully")
        
        # Nettoyer
        db.delete(retrieved)
        db.commit()
        
    finally:
        db.close()


def test_json_level_1_values():
    """Test that level_1_values can store and retrieve JSON."""
    print("\nTesting JSON level_1_values...")
    init_database()
    db = SessionLocal()
    
    try:
        # Créer un type avec plusieurs level_1_values
        test_values = ["Valeur 1", "Valeur 2", "Valeur 3"]
        test_type = AmortizationType(
            name="Test JSON",
            level_2_value="test",
            level_1_values=json.dumps(test_values),
            duration=5.0
        )
        
        db.add(test_type)
        db.commit()
        
        # Récupérer et vérifier
        retrieved = db.query(AmortizationType).filter(
            AmortizationType.name == "Test JSON"
        ).first()
        
        assert retrieved is not None
        parsed_values = json.loads(retrieved.level_1_values)
        assert parsed_values == test_values
        assert len(parsed_values) == 3
        
        print("✓ JSON level_1_values stored and retrieved correctly")
        
        # Nettoyer
        db.delete(retrieved)
        db.commit()
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing AmortizationType Model")
    print("=" * 60)
    
    try:
        test_table_exists()
        test_table_columns()
        test_create_amortization_type()
        test_json_level_1_values()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

