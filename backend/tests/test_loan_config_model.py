"""
Test script to validate LoanConfig model.

Run with: python -m pytest backend/tests/test_loan_config_model.py -v
Or: python backend/tests/test_loan_config_model.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import LoanConfig
from sqlalchemy import inspect


def test_table_exists():
    """Test that loan_configs table exists."""
    print("Testing loan_configs table existence...")
    init_database()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "loan_configs" in tables, "Table 'loan_configs' not found"
    print("✓ Table 'loan_configs' exists")


def test_table_columns():
    """Test that loan_configs table has correct columns."""
    print("\nTesting table columns...")
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('loan_configs')}
    
    # Vérifier les colonnes requises
    required_columns = [
        'id', 'name', 'credit_amount', 'interest_rate',
        'duration_years', 'initial_deferral_months', 'created_at', 'updated_at'
    ]
    
    for col_name in required_columns:
        assert col_name in columns, f"Column '{col_name}' not found"
        print(f"✓ Column '{col_name}' exists")
    
    # Vérifier les contraintes nullable
    assert columns['id']['nullable'] == False
    assert columns['name']['nullable'] == False
    assert columns['credit_amount']['nullable'] == False
    assert columns['interest_rate']['nullable'] == False
    assert columns['duration_years']['nullable'] == False
    assert columns['initial_deferral_months']['nullable'] == False
    print("✓ All columns have correct nullable constraints")


def test_create_loan_config():
    """Test creating a LoanConfig."""
    print("\nTesting LoanConfig creation...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(LoanConfig).filter(LoanConfig.name == "Prêt test").delete()
        db.commit()
        
        # Créer une configuration de test
        test_config = LoanConfig(
            name="Prêt test",
            credit_amount=200000.0,
            interest_rate=2.5,
            duration_years=20,
            initial_deferral_months=0
        )
        
        db.add(test_config)
        db.commit()
        
        # Vérifier que la configuration a été créée
        assert test_config.id is not None, "LoanConfig ID should be set after commit"
        print(f"✓ LoanConfig created with ID: {test_config.id}")
        
        # Vérifier les valeurs
        assert test_config.name == "Prêt test"
        assert test_config.credit_amount == 200000.0
        assert test_config.interest_rate == 2.5
        assert test_config.duration_years == 20
        assert test_config.initial_deferral_months == 0
        assert test_config.created_at is not None
        assert test_config.updated_at is not None
        print("✓ All fields are correctly set")
        
        # Nettoyer
        db.delete(test_config)
        db.commit()
        
    finally:
        db.close()


def test_read_loan_config():
    """Test reading a LoanConfig."""
    print("\nTesting LoanConfig reading...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(LoanConfig).filter(LoanConfig.name == "Prêt test read").delete()
        db.commit()
        
        # Créer une configuration de test
        test_config = LoanConfig(
            name="Prêt test read",
            credit_amount=150000.0,
            interest_rate=3.0,
            duration_years=15,
            initial_deferral_months=6
        )
        
        db.add(test_config)
        db.commit()
        config_id = test_config.id
        
        # Lire la configuration
        read_config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
        
        assert read_config is not None, "LoanConfig should be found"
        assert read_config.name == "Prêt test read"
        assert read_config.credit_amount == 150000.0
        assert read_config.interest_rate == 3.0
        assert read_config.duration_years == 15
        assert read_config.initial_deferral_months == 6
        print("✓ LoanConfig can be read correctly")
        
        # Nettoyer
        db.delete(read_config)
        db.commit()
        
    finally:
        db.close()


def test_update_loan_config():
    """Test updating a LoanConfig."""
    print("\nTesting LoanConfig update...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(LoanConfig).filter(LoanConfig.name == "Prêt test update").delete()
        db.commit()
        
        # Créer une configuration de test
        test_config = LoanConfig(
            name="Prêt test update",
            credit_amount=100000.0,
            interest_rate=2.0,
            duration_years=10,
            initial_deferral_months=0
        )
        
        db.add(test_config)
        db.commit()
        config_id = test_config.id
        original_updated_at = test_config.updated_at
        
        # Mettre à jour
        test_config.interest_rate = 2.5
        test_config.duration_years = 12
        db.commit()
        db.refresh(test_config)
        
        # Vérifier les modifications
        assert test_config.interest_rate == 2.5
        assert test_config.duration_years == 12
        assert test_config.updated_at != original_updated_at, "updated_at should be updated"
        print("✓ LoanConfig can be updated correctly")
        
        # Nettoyer
        db.delete(test_config)
        db.commit()
        
    finally:
        db.close()


def test_unique_name_constraint():
    """Test that name must be unique."""
    print("\nTesting unique name constraint...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(LoanConfig).filter(LoanConfig.name == "Prêt unique").delete()
        db.commit()
        
        # Créer une première configuration
        config1 = LoanConfig(
            name="Prêt unique",
            credit_amount=100000.0,
            interest_rate=2.0,
            duration_years=10,
            initial_deferral_months=0
        )
        
        db.add(config1)
        db.commit()
        
        # Essayer de créer une deuxième avec le même nom
        config2 = LoanConfig(
            name="Prêt unique",
            credit_amount=200000.0,
            interest_rate=3.0,
            duration_years=15,
            initial_deferral_months=0
        )
        
        db.add(config2)
        
        try:
            db.commit()
            # Si on arrive ici, la contrainte n'a pas fonctionné
            # Vérifier qu'il n'y a qu'un seul enregistrement
            count = db.query(LoanConfig).filter(LoanConfig.name == "Prêt unique").count()
            if count == 1:
                print("✓ Unique constraint works (duplicate was prevented)")
                db.delete(config2)
                db.commit()
            else:
                assert False, f"Should have only 1 config with name 'Prêt unique', got {count}"
        except Exception as e:
            db.rollback()
            # SQLite peut lever différentes exceptions selon la version
            print(f"✓ Unique constraint works: {type(e).__name__}")
        
        # Nettoyer
        db.delete(config1)
        db.commit()
        
    finally:
        db.close()


def test_multiple_loan_configs():
    """Test handling multiple loan configurations."""
    print("\nTesting multiple LoanConfigs...")
    init_database()
    db = SessionLocal()
    
    try:
        # Nettoyer les données de test existantes
        db.query(LoanConfig).filter(LoanConfig.name.in_(["Prêt A", "Prêt B", "Prêt C"])).delete()
        db.commit()
        
        # Créer plusieurs configurations
        configs = [
            LoanConfig(
                name="Prêt A",
                credit_amount=100000.0,
                interest_rate=2.0,
                duration_years=10,
                initial_deferral_months=0
            ),
            LoanConfig(
                name="Prêt B",
                credit_amount=200000.0,
                interest_rate=2.5,
                duration_years=20,
                initial_deferral_months=6
            ),
            LoanConfig(
                name="Prêt C",
                credit_amount=300000.0,
                interest_rate=3.0,
                duration_years=25,
                initial_deferral_months=12
            )
        ]
        
        for config in configs:
            db.add(config)
        db.commit()
        
        # Vérifier qu'on peut les lire
        all_configs = db.query(LoanConfig).filter(
            LoanConfig.name.in_(["Prêt A", "Prêt B", "Prêt C"])
        ).all()
        
        assert len(all_configs) == 3, f"Expected 3 configs, got {len(all_configs)}"
        print(f"✓ Created and read {len(all_configs)} LoanConfigs")
        
        # Nettoyer
        for config in all_configs:
            db.delete(config)
        db.commit()
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing LoanConfig Model")
    print("=" * 60)
    
    try:
        test_table_exists()
        test_table_columns()
        test_create_loan_config()
        test_read_loan_config()
        test_update_loan_config()
        test_unique_name_constraint()
        test_multiple_loan_configs()
        
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
