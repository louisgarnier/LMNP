"""
Test script to validate database schema creation.

Run with: python -m pytest backend/tests/test_database_schema.py -v
Or: python backend/tests/test_database_schema.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, get_db, engine
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    Mapping,
    Parameter,
    Amortization,
    FinancialStatement,
    ConsolidatedFinancialStatement
)
from sqlalchemy import inspect
from datetime import date, datetime


def test_database_initialization():
    """Test that database can be initialized."""
    print("Testing database initialization...")
    init_database()
    print("✓ Database initialized successfully")


def test_tables_exist():
    """Test that all required tables exist."""
    print("\nTesting table existence...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        "transactions",
        "enriched_transactions",
        "mappings",
        "parameters",
        "amortizations",
        "financial_statements",
        "consolidated_financial_statements"
    ]
    
    for table in required_tables:
        assert table in tables, f"Table {table} not found"
        print(f"✓ Table '{table}' exists")
    
    print(f"\n✓ All {len(required_tables)} required tables exist")


def test_table_columns():
    """Test that tables have correct columns."""
    print("\nTesting table columns...")
    inspector = inspect(engine)
    
    # Test transactions table
    trans_columns = [col['name'] for col in inspector.get_columns('transactions')]
    assert 'id' in trans_columns
    assert 'date' in trans_columns
    assert 'quantite' in trans_columns
    assert 'nom' in trans_columns
    assert 'solde' in trans_columns
    print("✓ Transactions table has correct columns")
    
    # Test enriched_transactions table
    enriched_columns = [col['name'] for col in inspector.get_columns('enriched_transactions')]
    assert 'transaction_id' in enriched_columns
    assert 'mois' in enriched_columns
    assert 'annee' in enriched_columns
    assert 'level_1' in enriched_columns
    assert 'level_2' in enriched_columns
    assert 'level_3' in enriched_columns
    print("✓ Enriched transactions table has correct columns")
    
    # Test mappings table
    mapping_columns = [col['name'] for col in inspector.get_columns('mappings')]
    assert 'nom' in mapping_columns
    assert 'level_1' in mapping_columns
    assert 'level_2' in mapping_columns
    print("✓ Mappings table has correct columns")
    
    print("✓ All tables have correct column structure")


def test_insert_and_query():
    """Test inserting and querying data."""
    print("\nTesting data insertion and querying...")
    
    db = next(get_db())
    
    try:
        # Insert a test transaction
        test_transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=1000.0,
            nom="Test Transaction",
            solde=5000.0,
            source_file="test.csv"
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        
        assert test_transaction.id is not None
        print(f"✓ Inserted transaction with ID: {test_transaction.id}")
        
        # Query it back
        retrieved = db.query(Transaction).filter(Transaction.id == test_transaction.id).first()
        assert retrieved is not None
        assert retrieved.nom == "Test Transaction"
        assert retrieved.quantite == 1000.0
        print("✓ Successfully queried transaction")
        
        # Insert a test mapping
        test_mapping = Mapping(
            nom="Test Transaction",
            level_1="test_level_1",
            level_2="test_level_2",
            level_3="test_level_3"
        )
        db.add(test_mapping)
        db.commit()
        print("✓ Inserted test mapping")
        
        # Insert a test parameter
        test_param = Parameter(
            key="test_param",
            value="100",
            value_type="int",
            description="Test parameter"
        )
        db.add(test_param)
        db.commit()
        print("✓ Inserted test parameter")
        
        # Clean up
        db.delete(test_transaction)
        db.delete(test_mapping)
        db.delete(test_param)
        db.commit()
        print("✓ Cleaned up test data")
        
    finally:
        db.close()


def test_indexes():
    """Test that indexes exist."""
    print("\nTesting indexes...")
    inspector = inspect(engine)
    
    # Check transactions indexes
    trans_indexes = [idx['name'] for idx in inspector.get_indexes('transactions')]
    assert any('date' in idx for idx in trans_indexes if idx), "Date index not found"
    print("✓ Indexes exist on transactions table")
    
    print("✓ Indexes are properly configured")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Schema Validation Tests")
    print("=" * 60)
    
    try:
        test_database_initialization()
        test_tables_exist()
        test_table_columns()
        test_insert_and_query()
        test_indexes()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

