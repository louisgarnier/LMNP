"""
Test script for Step 9.1: Bilan models and tables.

This script tests:
1. That the BilanMapping, BilanData, and BilanConfig models are correctly defined
2. That the migration script creates the tables correctly
3. That basic CRUD operations work on the models

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import BilanMapping, BilanData, BilanConfig
from sqlalchemy import inspect
import json


def test_models_exist():
    """Test that the models are importable."""
    print("📋 Testing model imports...")
    
    try:
        assert BilanMapping is not None
        assert BilanData is not None
        assert BilanConfig is not None
        print("✅ All models are importable")
        return True
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False


def test_tables_exist():
    """Test that the tables exist in the database."""
    print("\n📋 Testing table existence...")
    
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        required_tables = ['bilan_mappings', 'bilan_data', 'bilan_config']
        
        for table in required_tables:
            if table in tables:
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Table {table} does not exist")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False
    finally:
        db.close()


def test_bilan_mapping_crud():
    """Test CRUD operations on BilanMapping."""
    print("\n📋 Testing BilanMapping CRUD...")
    
    db = SessionLocal()
    try:
        # Create
        mapping = BilanMapping(
            category_name="Immobilisations",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=json.dumps(["IMMOBILISATIONS"]),
            is_special=False,
            special_source=None,
            compte_resultat_view_id=None
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        mapping_id = mapping.id
        print(f"✅ Created BilanMapping with id={mapping_id}")
        
        # Read
        retrieved = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
        assert retrieved is not None
        assert retrieved.category_name == "Immobilisations"
        assert retrieved.type == "ACTIF"
        assert retrieved.sub_category == "Actif immobilisé"
        assert retrieved.is_special == False
        print("✅ Read BilanMapping successful")
        
        # Update
        retrieved.category_name = "Immobilisations (modifié)"
        db.commit()
        db.refresh(retrieved)
        assert retrieved.category_name == "Immobilisations (modifié)"
        print("✅ Update BilanMapping successful")
        
        # Delete
        db.delete(retrieved)
        db.commit()
        
        deleted = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
        assert deleted is None
        print("✅ Delete BilanMapping successful")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error in BilanMapping CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_bilan_data_crud():
    """Test CRUD operations on BilanData."""
    print("\n📋 Testing BilanData CRUD...")
    
    db = SessionLocal()
    try:
        # Create
        data = BilanData(
            annee=2024,
            category_name="Immobilisations",
            amount=100000.50
        )
        db.add(data)
        db.commit()
        db.refresh(data)
        
        data_id = data.id
        print(f"✅ Created BilanData with id={data_id}")
        
        # Read
        retrieved = db.query(BilanData).filter(BilanData.id == data_id).first()
        assert retrieved is not None
        assert retrieved.annee == 2024
        assert retrieved.category_name == "Immobilisations"
        assert retrieved.amount == 100000.50
        print("✅ Read BilanData successful")
        
        # Update
        retrieved.amount = 150000.75
        db.commit()
        db.refresh(retrieved)
        assert retrieved.amount == 150000.75
        print("✅ Update BilanData successful")
        
        # Delete
        db.delete(retrieved)
        db.commit()
        
        deleted = db.query(BilanData).filter(BilanData.id == data_id).first()
        assert deleted is None
        print("✅ Delete BilanData successful")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error in BilanData CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_bilan_config_crud():
    """Test CRUD operations on BilanConfig."""
    print("\n📋 Testing BilanConfig CRUD...")
    
    db = SessionLocal()
    try:
        # Check if config already exists
        existing = db.query(BilanConfig).first()
        if existing:
            config = existing
            print(f"ℹ️  Using existing BilanConfig with id={config.id}")
        else:
            # Create
            config = BilanConfig(
                level_3_values=json.dumps(["VALEUR1", "VALEUR2"])
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            print(f"✅ Created BilanConfig with id={config.id}")
        
        config_id = config.id
        
        # Read
        retrieved = db.query(BilanConfig).filter(BilanConfig.id == config_id).first()
        assert retrieved is not None
        assert retrieved.level_3_values is not None
        values = json.loads(retrieved.level_3_values)
        print(f"✅ Read BilanConfig successful (level_3_values: {values})")
        
        # Update
        retrieved.level_3_values = json.dumps(["VALEUR3", "VALEUR4"])
        db.commit()
        db.refresh(retrieved)
        updated_values = json.loads(retrieved.level_3_values)
        assert "VALEUR3" in updated_values
        print("✅ Update BilanConfig successful")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error in BilanConfig CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_special_category_mapping():
    """Test creating a special category mapping."""
    print("\n📋 Testing special category mapping...")
    
    db = SessionLocal()
    try:
        # Create special category (Amortissements cumulés)
        mapping = BilanMapping(
            category_name="Amortissements cumulés",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=None,  # Special category doesn't need level_1_values
            is_special=True,
            special_source="amortization_result",
            compte_resultat_view_id=None
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        mapping_id = mapping.id
        print(f"✅ Created special category mapping with id={mapping_id}")
        
        # Verify
        retrieved = db.query(BilanMapping).filter(BilanMapping.id == mapping_id).first()
        assert retrieved.is_special == True
        assert retrieved.special_source == "amortization_result"
        assert retrieved.level_1_values is None
        print("✅ Special category mapping verified")
        
        # Cleanup
        db.delete(retrieved)
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error in special category mapping: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Bilan Models (Step 9.1)")
    print("=" * 60)
    
    results = []
    
    results.append(("Model imports", test_models_exist()))
    results.append(("Table existence", test_tables_exist()))
    results.append(("BilanMapping CRUD", test_bilan_mapping_crud()))
    results.append(("BilanData CRUD", test_bilan_data_crud()))
    results.append(("BilanConfig CRUD", test_bilan_config_crud()))
    results.append(("Special category mapping", test_special_category_mapping()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
