"""
Test script for Property model - Phase 11 Step 0.1

This script tests:
- Creation of Property model
- CRUD operations (Create, Read, Update, Delete)
- Unique constraint on name
- Timestamps (created_at, updated_at)

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.connection import SessionLocal
from database.models import Property
from datetime import datetime
import time


def test_create_property():
    """Test creating a property."""
    print("\n=== Test 1: Create Property ===")
    db = SessionLocal()
    try:
        # Use timestamp to ensure unique name
        import time
        timestamp = int(time.time() * 1000)
        property_name = f"Appartement Test 1 {timestamp}"
        
        property = Property(
            name=property_name,
            address="123 Rue de Test, 75001 Paris"
        )
        db.add(property)
        db.commit()
        db.refresh(property)
        
        print(f"✅ Property created: ID={property.id}, Name='{property.name}'")
        assert property.id is not None, "Property ID should not be None"
        assert property.name == property_name, "Property name should match"
        assert property.address == "123 Rue de Test, 75001 Paris", "Property address should match"
        assert property.created_at is not None, "created_at should be set"
        assert property.updated_at is not None, "updated_at should be set"
        
        return property.id
    finally:
        db.close()


def test_read_property(property_id: int):
    """Test reading a property."""
    print("\n=== Test 2: Read Property ===")
    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        
        assert property is not None, "Property should exist"
        print(f"✅ Property read: ID={property.id}, Name='{property.name}', Address='{property.address}'")
        
        return property
    finally:
        db.close()


def test_update_property(property_id: int):
    """Test updating a property."""
    print("\n=== Test 3: Update Property ===")
    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        old_updated_at = property.updated_at
        
        # Wait a bit to ensure updated_at changes
        time.sleep(1)
        
        # Use timestamp to ensure unique name
        timestamp = int(time.time() * 1000)
        new_name = f"Appartement Test 1 Modifié {timestamp}"
        
        property.name = new_name
        property.address = "456 Nouvelle Adresse, 75002 Paris"
        db.commit()
        db.refresh(property)
        
        print(f"✅ Property updated: Name='{property.name}', Address='{property.address}'")
        assert property.name == new_name, "Property name should be updated"
        assert property.address == "456 Nouvelle Adresse, 75002 Paris", "Property address should be updated"
        assert property.updated_at > old_updated_at, "updated_at should be updated"
        
    finally:
        db.close()


def test_unique_constraint():
    """Test unique constraint on name."""
    print("\n=== Test 4: Unique Constraint on Name ===")
    db = SessionLocal()
    try:
        # Use a unique name with timestamp to avoid conflicts
        import time
        timestamp = int(time.time() * 1000)
        unique_name = f"Appartement Unique {timestamp}"
        
        # Try to create a property with the same name
        property1 = Property(
            name=unique_name,
            address="Adresse 1"
        )
        db.add(property1)
        db.commit()
        
        # Try to create another property with the same name (should fail)
        property2 = Property(
            name=unique_name,
            address="Adresse 2"
        )
        db.add(property2)
        
        try:
            db.commit()
            print("❌ Unique constraint failed - should have raised an error")
            assert False, "Should have raised IntegrityError"
        except Exception as e:
            db.rollback()
            print(f"✅ Unique constraint works: {type(e).__name__}")
            
            # Clean up
            db.delete(property1)
            db.commit()
    finally:
        db.close()


def test_delete_property(property_id: int):
    """Test deleting a property."""
    print("\n=== Test 5: Delete Property ===")
    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        assert property is not None, "Property should exist before deletion"
        
        db.delete(property)
        db.commit()
        
        # Verify deletion
        deleted_property = db.query(Property).filter(Property.id == property_id).first()
        assert deleted_property is None, "Property should be deleted"
        
        print(f"✅ Property deleted: ID={property_id}")
    finally:
        db.close()


def test_list_properties():
    """Test listing all properties."""
    print("\n=== Test 6: List All Properties ===")
    db = SessionLocal()
    try:
        # Get count before
        count_before = db.query(Property).count()
        
        # Create a few test properties with unique names (using timestamp)
        import time
        timestamp = int(time.time() * 1000)  # milliseconds
        properties = [
            Property(name=f"Test Property {timestamp} {i}", address=f"Address {i}")
            for i in range(1, 4)
        ]
        for prop in properties:
            db.add(prop)
        db.commit()
        
        # List all properties
        all_properties = db.query(Property).all()
        count_after = len(all_properties)
        print(f"✅ Found {count_after} properties (was {count_before}, added {count_after - count_before})")
        
        # Clean up
        for prop in properties:
            db.delete(prop)
        db.commit()
        
        return count_after
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("TEST SCRIPT: Property Model - Phase 11 Step 0.1")
    print("=" * 60)
    
    try:
        # Run migration first
        print("\n📦 Running migration...")
        from database.migrations.add_properties_table import migrate
        migrate()
        
        # Run tests
        property_id = test_create_property()
        test_read_property(property_id)
        test_update_property(property_id)
        test_unique_constraint()
        test_list_properties()
        test_delete_property(property_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
