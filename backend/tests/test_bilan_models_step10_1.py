"""
Test des modèles de données du Bilan (Step 10.1).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_models_step10_1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.database.models import BilanMapping, BilanData, BilanMappingView, AmortizationView
from datetime import datetime


def test_bilan_mapping():
    """Test création et lecture d'un BilanMapping."""
    print("🧪 Test BilanMapping...")
    db = SessionLocal()
    try:
        # Créer un mapping de test
        mapping = BilanMapping(
            category_name="Immobilisations",
            level_1_values=["Achat immobilier", "Travaux"],
            type="ACTIF",
            sub_category="Actif immobilisé",
            is_special=False,
            special_source=None,
            amortization_view_id=None
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        # Vérifier que l'ID a été généré
        assert mapping.id is not None, "L'ID devrait être généré automatiquement"
        print(f"  ✅ Mapping créé avec ID: {mapping.id}")
        
        # Vérifier les champs
        assert mapping.category_name == "Immobilisations"
        assert mapping.level_1_values == ["Achat immobilier", "Travaux"]
        assert mapping.type == "ACTIF"
        assert mapping.sub_category == "Actif immobilisé"
        assert mapping.is_special == False
        print("  ✅ Tous les champs sont corrects")
        
        # Test avec catégorie spéciale
        special_mapping = BilanMapping(
            category_name="Amortissements cumulés",
            level_1_values=None,
            type="ACTIF",
            sub_category="Actif immobilisé",
            is_special=True,
            special_source="amortizations",
            amortization_view_id=None
        )
        db.add(special_mapping)
        db.commit()
        db.refresh(special_mapping)
        
        assert special_mapping.is_special == True
        assert special_mapping.special_source == "amortizations"
        print("  ✅ Catégorie spéciale créée correctement")
        
        # Nettoyer
        db.delete(mapping)
        db.delete(special_mapping)
        db.commit()
        print("  ✅ Mapping supprimé")
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_bilan_data():
    """Test création et lecture d'un BilanData."""
    print("🧪 Test BilanData...")
    db = SessionLocal()
    try:
        # Créer une donnée de test
        data = BilanData(
            annee=2024,
            category_name="Immobilisations",
            amount=150000.50
        )
        db.add(data)
        db.commit()
        db.refresh(data)
        
        # Vérifier que l'ID a été généré
        assert data.id is not None, "L'ID devrait être généré automatiquement"
        print(f"  ✅ Donnée créée avec ID: {data.id}")
        
        # Vérifier les champs
        assert data.annee == 2024
        assert data.category_name == "Immobilisations"
        assert data.amount == 150000.50
        print("  ✅ Tous les champs sont corrects")
        
        # Test recherche par année
        results = db.query(BilanData).filter(BilanData.annee == 2024).all()
        assert len(results) >= 1
        print("  ✅ Recherche par année fonctionne")
        
        # Nettoyer
        db.delete(data)
        db.commit()
        print("  ✅ Donnée supprimée")
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_bilan_mapping_view():
    """Test création et lecture d'un BilanMappingView."""
    print("🧪 Test BilanMappingView...")
    db = SessionLocal()
    try:
        # Créer une vue de test
        view_data = {
            "mappings": [
                {
                    "id": 1,
                    "category_name": "Immobilisations",
                    "level_1_values": ["Achat immobilier"]
                }
            ],
            "selected_level_3_values": ["Immobilisations", "Capitaux propres"]
        }
        
        view = BilanMappingView(
            name="Test View",
            view_data=view_data
        )
        db.add(view)
        db.commit()
        db.refresh(view)
        
        # Vérifier que l'ID a été généré
        assert view.id is not None, "L'ID devrait être généré automatiquement"
        print(f"  ✅ Vue créée avec ID: {view.id}")
        
        # Vérifier les champs
        assert view.name == "Test View"
        assert view.view_data == view_data
        assert "mappings" in view.view_data
        assert "selected_level_3_values" in view.view_data
        print("  ✅ Tous les champs sont corrects")
        
        # Test unicité du nom
        try:
            duplicate_view = BilanMappingView(
                name="Test View",  # Même nom
                view_data={}
            )
            db.add(duplicate_view)
            db.commit()
            print("  ❌ L'unicité du nom n'est pas respectée")
            db.delete(duplicate_view)
            db.commit()
        except Exception:
            db.rollback()
            print("  ✅ L'unicité du nom est respectée")
        
        # Nettoyer
        db.delete(view)
        db.commit()
        print("  ✅ Vue supprimée")
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_foreign_key_relation():
    """Test de la relation ForeignKey vers amortization_views."""
    print("🧪 Test relation ForeignKey...")
    db = SessionLocal()
    try:
        # Vérifier qu'une vue d'amortissement existe (ou en créer une de test)
        amortization_view = db.query(AmortizationView).first()
        
        if amortization_view:
            # Créer un mapping avec relation
            mapping = BilanMapping(
                category_name="Amortissements cumulés",
                level_1_values=None,
                type="ACTIF",
                sub_category="Actif immobilisé",
                is_special=True,
                special_source="amortizations",
                amortization_view_id=amortization_view.id
            )
            db.add(mapping)
            db.commit()
            db.refresh(mapping)
            
            assert mapping.amortization_view_id == amortization_view.id
            print(f"  ✅ Relation ForeignKey fonctionne (amortization_view_id: {mapping.amortization_view_id})")
            
            # Nettoyer
            db.delete(mapping)
            db.commit()
        else:
            print("  ⚠️ Aucune vue d'amortissement trouvée, test de relation ignoré")
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Test des modèles de données du Bilan (Step 10.1)")
    print("=" * 60)
    print()
    
    try:
        test_bilan_mapping()
        print()
        test_bilan_data()
        print()
        test_bilan_mapping_view()
        print()
        test_foreign_key_relation()
        print()
        
        print("=" * 60)
        print("✅ Tous les tests sont passés !")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test échoué: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Erreur inattendue: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

