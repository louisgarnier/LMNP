"""
Test unitaire pour le modèle AmortizationView.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import AmortizationView
from datetime import datetime

def test_amortization_view_model():
    """Test que le modèle AmortizationView peut être créé et récupéré."""
    db = SessionLocal()
    try:
        # Test 1: Créer une vue
        test_view_data = {
            "level_2_value": "ammortissements",
            "amortization_types": [
                {
                    "name": "Part terrain",
                    "level_1_values": ["Caution entree"],
                    "start_date": "2024-01-01",
                    "duration": 30,
                    "annual_amount": 1000
                }
            ]
        }
        
        view = AmortizationView(
            name="Test View",
            level_2_value="ammortissements",
            view_data=test_view_data
        )
        
        db.add(view)
        db.commit()
        db.refresh(view)
        
        print(f"✅ Test 1: Vue créée avec ID {view.id}")
        assert view.id is not None
        assert view.name == "Test View"
        assert view.level_2_value == "ammortissements"
        assert view.view_data == test_view_data
        
        # Test 2: Récupérer la vue
        retrieved_view = db.query(AmortizationView).filter(AmortizationView.id == view.id).first()
        assert retrieved_view is not None
        assert retrieved_view.name == "Test View"
        print(f"✅ Test 2: Vue récupérée avec succès")
        
        # Test 3: Filtrer par level_2_value
        views_for_level2 = db.query(AmortizationView).filter(
            AmortizationView.level_2_value == "ammortissements"
        ).all()
        assert len(views_for_level2) >= 1
        print(f"✅ Test 3: Filtrage par level_2_value fonctionne ({len(views_for_level2)} vue(s) trouvée(s))")
        
        # Nettoyage
        db.delete(view)
        db.commit()
        print(f"✅ Test 4: Vue supprimée avec succès")
        
        print("\n✅ Tous les tests passent !")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_amortization_view_model()
    sys.exit(0 if success else 1)
