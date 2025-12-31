"""
Test unitaire pour les modèles CompteResultatMapping et CompteResultatData.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python -m pytest backend/tests/test_compte_resultat_models.py -v
Or: python backend/tests/test_compte_resultat_models.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import CompteResultatMapping, CompteResultatData
from datetime import datetime


def cleanup_db():
    """Nettoie la base de données avant les tests."""
    db = SessionLocal()
    try:
        db.query(CompteResultatData).delete()
        db.query(CompteResultatMapping).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    finally:
        db.close()


def test_compte_resultat_mapping_model():
    """Test que le modèle CompteResultatMapping peut être créé et récupéré."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Test 1: Créer un mapping avec level_1 et level_2
        mapping = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values=["PRODUITS"],
            level_2_values=["LOYERS", "LOYERS_CHARGES"]
        )
        
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        print(f"✅ Test 1: Mapping créé avec ID {mapping.id}")
        assert mapping.id is not None
        assert mapping.category_name == "Loyers hors charge encaissés"
        assert mapping.level_1_values == ["PRODUITS"]
        assert mapping.level_2_values == ["LOYERS", "LOYERS_CHARGES"]
        assert mapping.level_3_values is None
        
        # Test 2: Récupérer le mapping
        retrieved_mapping = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.id == mapping.id
        ).first()
        assert retrieved_mapping is not None
        assert retrieved_mapping.category_name == "Loyers hors charge encaissés"
        assert retrieved_mapping.level_2_values == ["LOYERS", "LOYERS_CHARGES"]
        print(f"✅ Test 2: Mapping récupéré avec succès")
        
        # Test 3: Créer un mapping sans level_1 (NULL)
        mapping2 = CompteResultatMapping(
            category_name="Charges de copropriété hors fonds travaux",
            level_1_values=None,
            level_2_values=["CHARGES_COPROPRIETE"]
        )
        
        db.add(mapping2)
        db.commit()
        db.refresh(mapping2)
        
        assert mapping2.level_1_values is None
        assert mapping2.level_2_values == ["CHARGES_COPROPRIETE"]
        print(f"✅ Test 3: Mapping sans level_1 créé avec succès")
        
        # Test 4: Filtrer par category_name
        mappings_by_category = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == "Loyers hors charge encaissés"
        ).all()
        assert len(mappings_by_category) >= 1
        print(f"✅ Test 4: Filtrage par category_name fonctionne ({len(mappings_by_category)} mapping(s) trouvé(s))")
        
        # Test 5: Mettre à jour un mapping
        mapping.level_2_values = ["LOYERS", "LOYERS_CHARGES", "LOYERS_AUTRES"]
        db.commit()
        db.refresh(mapping)
        assert len(mapping.level_2_values) == 3
        assert "LOYERS_AUTRES" in mapping.level_2_values
        print(f"✅ Test 5: Mise à jour du mapping fonctionne")
        
        # Test 6: Supprimer un mapping
        mapping_id = mapping.id
        db.delete(mapping)
        db.commit()
        deleted_mapping = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.id == mapping_id
        ).first()
        assert deleted_mapping is None
        print(f"✅ Test 6: Suppression du mapping fonctionne")
        
        # Nettoyage
        db.delete(mapping2)
        db.commit()
        
        print("\n✅ Tous les tests du modèle CompteResultatMapping sont passés !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors des tests: {e}")
        raise
    finally:
        db.close()


def test_compte_resultat_data_model():
    """Test que le modèle CompteResultatData peut être créé et récupéré."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Test 1: Créer une donnée de compte de résultat
        data = CompteResultatData(
            annee=2024,
            category_name="Loyers hors charge encaissés",
            amount=50000.0,
            amortization_view_id=None
        )
        
        db.add(data)
        db.commit()
        db.refresh(data)
        
        print(f"✅ Test 1: Donnée créée avec ID {data.id}")
        assert data.id is not None
        assert data.annee == 2024
        assert data.category_name == "Loyers hors charge encaissés"
        assert data.amount == 50000.0
        assert data.amortization_view_id is None
        
        # Test 2: Récupérer la donnée
        retrieved_data = db.query(CompteResultatData).filter(
            CompteResultatData.id == data.id
        ).first()
        assert retrieved_data is not None
        assert retrieved_data.annee == 2024
        assert retrieved_data.amount == 50000.0
        print(f"✅ Test 2: Donnée récupérée avec succès")
        
        # Test 3: Créer une donnée avec amortization_view_id
        data2 = CompteResultatData(
            annee=2024,
            category_name="Charges d'amortissements",
            amount=10000.0,
            amortization_view_id=1
        )
        
        db.add(data2)
        db.commit()
        db.refresh(data2)
        
        assert data2.amortization_view_id == 1
        print(f"✅ Test 3: Donnée avec amortization_view_id créée avec succès")
        
        # Test 4: Filtrer par année
        data_by_year = db.query(CompteResultatData).filter(
            CompteResultatData.annee == 2024
        ).all()
        assert len(data_by_year) >= 2
        print(f"✅ Test 4: Filtrage par année fonctionne ({len(data_by_year)} donnée(s) trouvée(s))")
        
        # Test 5: Filtrer par catégorie et année
        data_by_category_year = db.query(CompteResultatData).filter(
            CompteResultatData.annee == 2024,
            CompteResultatData.category_name == "Loyers hors charge encaissés"
        ).all()
        assert len(data_by_category_year) >= 1
        print(f"✅ Test 5: Filtrage par catégorie et année fonctionne")
        
        # Test 6: Mettre à jour une donnée
        data.amount = 55000.0
        db.commit()
        db.refresh(data)
        assert data.amount == 55000.0
        print(f"✅ Test 6: Mise à jour de la donnée fonctionne")
        
        # Test 7: Supprimer une donnée
        data_id = data.id
        db.delete(data)
        db.commit()
        deleted_data = db.query(CompteResultatData).filter(
            CompteResultatData.id == data_id
        ).first()
        assert deleted_data is None
        print(f"✅ Test 7: Suppression de la donnée fonctionne")
        
        # Nettoyage
        db.delete(data2)
        db.commit()
        
        print("\n✅ Tous les tests du modèle CompteResultatData sont passés !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors des tests: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Tests des modèles CompteResultatMapping et CompteResultatData")
    print("=" * 60)
    print()
    
    test_compte_resultat_mapping_model()
    print()
    test_compte_resultat_data_model()
    print()
    print("=" * 60)
    print("✅ Tous les tests sont passés !")
    print("=" * 60)

