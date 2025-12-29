"""
Test unitaire pour le modèle LoanConfig.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python -m pytest backend/tests/test_loan_config_model.py -v
Or: python backend/tests/test_loan_config_model.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import LoanConfig
from datetime import datetime

def test_loan_config_model():
    """Test que le modèle LoanConfig peut être créé et récupéré."""
    db = SessionLocal()
    try:
        # Test 1: Créer une configuration de crédit
        config = LoanConfig(
            name="Prêt principal",
            credit_amount=200000.0,
            interest_rate=3.2,
            duration_years=20,
            initial_deferral_months=12
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        print(f"✅ Test 1: Configuration créée avec ID {config.id}")
        assert config.id is not None
        assert config.name == "Prêt principal"
        assert config.credit_amount == 200000.0
        assert config.interest_rate == 3.2
        assert config.duration_years == 20
        assert config.initial_deferral_months == 12
        
        # Test 2: Récupérer la configuration
        retrieved_config = db.query(LoanConfig).filter(LoanConfig.id == config.id).first()
        assert retrieved_config is not None
        assert retrieved_config.name == "Prêt principal"
        assert retrieved_config.credit_amount == 200000.0
        print(f"✅ Test 2: Configuration récupérée avec succès")
        
        # Test 3: Filtrer par name
        configs_by_name = db.query(LoanConfig).filter(
            LoanConfig.name == "Prêt principal"
        ).all()
        assert len(configs_by_name) >= 1
        print(f"✅ Test 3: Filtrage par name fonctionne ({len(configs_by_name)} configuration(s) trouvée(s))")
        
        # Test 4: Mettre à jour une configuration
        config.credit_amount = 250000.0
        config.interest_rate = 3.5
        db.commit()
        db.refresh(config)
        assert config.credit_amount == 250000.0
        assert config.interest_rate == 3.5
        print(f"✅ Test 4: Mise à jour de la configuration fonctionne")
        
        # Test 5: Supprimer une configuration
        config_id = config.id
        db.delete(config)
        db.commit()
        deleted_config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
        assert deleted_config is None
        print(f"✅ Test 5: Suppression de la configuration fonctionne")
        
        print("\n✅ Tous les tests du modèle LoanConfig sont passés !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors des tests: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_loan_config_model()

