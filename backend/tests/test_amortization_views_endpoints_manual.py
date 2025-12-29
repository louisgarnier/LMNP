"""
Test manuel des endpoints API pour les vues d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Usage:
    python3 backend/tests/test_amortization_views_endpoints_manual.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import AmortizationView

def test_endpoints_manual():
    """Test manuel des endpoints - vérifie que la structure est correcte."""
    db = SessionLocal()
    try:
        print("🧪 Test manuel des endpoints API pour les vues d'amortissement\n")
        
        # Test 1: Vérifier que la table existe
        count = db.query(AmortizationView).count()
        print(f"✅ Test 1: Table 'amortization_views' accessible ({count} vue(s) existante(s))")
        
        # Test 2: Créer une vue de test
        test_view_data = {
            "level_2_value": "ammortissements",
            "amortization_types": [
                {
                    "name": "Part terrain",
                    "level_1_values": ["Caution entree"],
                    "start_date": "2024-01-01",
                    "duration": 30,
                    "annual_amount": 1000
                },
                {
                    "name": "Immobilisation mobilier",
                    "level_1_values": ["Mobilier"],
                    "start_date": None,
                    "duration": 10,
                    "annual_amount": None
                }
            ]
        }
        
        test_view = AmortizationView(
            name="Test View Manual",
            level_2_value="ammortissements",
            view_data=test_view_data
        )
        
        db.add(test_view)
        db.commit()
        db.refresh(test_view)
        
        print(f"✅ Test 2: Vue de test créée avec ID {test_view.id}")
        assert test_view.id is not None
        assert test_view.name == "Test View Manual"
        assert test_view.view_data == test_view_data
        
        # Test 3: Filtrer par level_2_value
        views_for_level2 = db.query(AmortizationView).filter(
            AmortizationView.level_2_value == "ammortissements"
        ).all()
        print(f"✅ Test 3: Filtrage par level_2_value fonctionne ({len(views_for_level2)} vue(s) trouvée(s))")
        
        # Test 4: Vérifier structure view_data
        assert "level_2_value" in test_view.view_data
        assert "amortization_types" in test_view.view_data
        assert isinstance(test_view.view_data["amortization_types"], list)
        assert len(test_view.view_data["amortization_types"]) == 2
        print("✅ Test 4: Structure view_data correcte")
        
        # Nettoyage
        db.delete(test_view)
        db.commit()
        print(f"✅ Test 5: Vue de test supprimée")
        
        print("\n✅ Tous les tests manuels passent !")
        print("\n📝 Prochaines étapes:")
        print("   1. Démarrer le serveur: python3 -m uvicorn backend.api.main:app --reload")
        print("   2. Tester les endpoints via Swagger UI: http://localhost:8000/docs")
        print("   3. Ou tester avec curl/Postman")
        
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
    success = test_endpoints_manual()
    sys.exit(0 if success else 1)

