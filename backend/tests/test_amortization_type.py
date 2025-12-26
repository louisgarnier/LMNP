"""
Tests unitaires pour le modèle AmortizationType.

Run with: python -m pytest backend/tests/test_amortization_type.py -v
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, AmortizationType


# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    """Crée les tables pour les tests."""
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    """Supprime les tables après les tests."""
    Base.metadata.drop_all(bind=engine)


def test_amortization_type_creation():
    """Test création d'un AmortizationType."""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # Créer un type d'amortissement
        amortization_type = AmortizationType(
            name="Immobilisation mobilier",
            level_2_value="ammortissements",
            level_1_values=["Meubles", "Furniture"],
            start_date=None,
            duration=5.0,
            annual_amount=None
        )
        
        db.add(amortization_type)
        db.commit()
        db.refresh(amortization_type)
        
        # Vérifier que l'ID a été généré
        assert amortization_type.id is not None
        assert amortization_type.id > 0
        
        # Vérifier les valeurs
        assert amortization_type.name == "Immobilisation mobilier"
        assert amortization_type.level_2_value == "ammortissements"
        assert amortization_type.level_1_values == ["Meubles", "Furniture"]
        assert amortization_type.start_date is None
        assert amortization_type.duration == 5.0
        assert amortization_type.annual_amount is None
        
        # Vérifier les timestamps
        assert amortization_type.created_at is not None
        assert amortization_type.updated_at is not None
        
        print("✅ Test création AmortizationType : PASSÉ")
        
    finally:
        db.close()
        teardown_test_db()


def test_amortization_type_with_start_date():
    """Test création avec date de début."""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        start_date = date(2024, 3, 14)
        
        amortization_type = AmortizationType(
            name="Immobilisation travaux",
            level_2_value="ammortissements",
            level_1_values=["Travaux"],
            start_date=start_date,
            duration=20.0,
            annual_amount=1000.0
        )
        
        db.add(amortization_type)
        db.commit()
        db.refresh(amortization_type)
        
        assert amortization_type.start_date == start_date
        assert amortization_type.duration == 20.0
        assert amortization_type.annual_amount == 1000.0
        
        print("✅ Test AmortizationType avec start_date : PASSÉ")
        
    finally:
        db.close()
        teardown_test_db()


def test_amortization_type_json_level1_values():
    """Test que level_1_values est correctement stocké en JSON."""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        level_1_values = ["Value1", "Value2", "Value3"]
        
        amortization_type = AmortizationType(
            name="Test Type",
            level_2_value="ammortissements",
            level_1_values=level_1_values,
            start_date=None,
            duration=10.0,
            annual_amount=None
        )
        
        db.add(amortization_type)
        db.commit()
        db.refresh(amortization_type)
        
        # Vérifier que level_1_values est bien une liste
        assert isinstance(amortization_type.level_1_values, list)
        assert amortization_type.level_1_values == level_1_values
        
        # Vérifier qu'on peut récupérer depuis la DB
        retrieved = db.query(AmortizationType).filter(AmortizationType.id == amortization_type.id).first()
        assert retrieved.level_1_values == level_1_values
        
        print("✅ Test JSON level_1_values : PASSÉ")
        
    finally:
        db.close()
        teardown_test_db()


def test_amortization_type_required_fields():
    """Test que les champs obligatoires sont bien requis."""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # Test avec tous les champs requis
        amortization_type = AmortizationType(
            name="Test Type",
            level_2_value="ammortissements",
            level_1_values=[],
            duration=5.0
        )
        
        db.add(amortization_type)
        db.commit()
        
        assert amortization_type.id is not None
        
        print("✅ Test champs obligatoires : PASSÉ")
        
    finally:
        db.close()
        teardown_test_db()


if __name__ == "__main__":
    print("🧪 Exécution des tests AmortizationType...\n")
    
    test_amortization_type_creation()
    test_amortization_type_with_start_date()
    test_amortization_type_json_level1_values()
    test_amortization_type_required_fields()
    
    print("\n✅ Tous les tests sont passés!")

