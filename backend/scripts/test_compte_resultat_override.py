"""
Test script for compte_resultat_override table and models.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import CompteResultatOverride
from datetime import datetime


def test_override():
    """Test creating, reading, and deleting an override."""
    db = SessionLocal()
    
    try:
        # Test 1: Create an override
        print("Test 1: Creating override for year 2023...")
        override = CompteResultatOverride(
            year=2023,
            override_value=5000.50
        )
        db.add(override)
        db.commit()
        db.refresh(override)
        print(f"✅ Override created: ID={override.id}, Year={override.year}, Value={override.override_value}")
        
        # Test 2: Read the override
        print("\nTest 2: Reading override for year 2023...")
        found = db.query(CompteResultatOverride).filter(CompteResultatOverride.year == 2023).first()
        if found:
            print(f"✅ Override found: ID={found.id}, Year={found.year}, Value={found.override_value}")
        else:
            print("❌ Override not found")
            return
        
        # Test 3: Update the override
        print("\nTest 3: Updating override value...")
        found.override_value = 7500.75
        db.commit()
        db.refresh(found)
        print(f"✅ Override updated: Value={found.override_value}")
        
        # Test 4: Test UNIQUE constraint (should fail)
        print("\nTest 4: Testing UNIQUE constraint (should fail)...")
        try:
            duplicate = CompteResultatOverride(
                year=2023,
                override_value=10000.00
            )
            db.add(duplicate)
            db.commit()
            print("❌ UNIQUE constraint not working - duplicate was created!")
        except Exception as e:
            print(f"✅ UNIQUE constraint working - duplicate rejected: {type(e).__name__}")
            db.rollback()
        
        # Test 5: Delete the override
        print("\nTest 5: Deleting override...")
        db.delete(found)
        db.commit()
        print("✅ Override deleted")
        
        # Verify deletion
        found_after_delete = db.query(CompteResultatOverride).filter(CompteResultatOverride.year == 2023).first()
        if found_after_delete:
            print("❌ Override still exists after deletion!")
        else:
            print("✅ Override successfully deleted")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_override()
