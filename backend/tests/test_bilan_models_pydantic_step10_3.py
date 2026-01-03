"""
Test des modèles Pydantic pour le Bilan (Step 10.3).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/tests/test_bilan_models_pydantic_step10_3.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.api.models import (
    BilanMappingBase, BilanMappingCreate, BilanMappingUpdate, BilanMappingResponse,
    BilanMappingListResponse, BilanDataBase, BilanDataResponse, BilanDataListResponse,
    BilanResponse, BilanTypeItem, BilanSubCategoryItem, BilanCategoryItem,
    BilanMappingViewCreate, BilanMappingViewUpdate, BilanMappingViewResponse,
    BilanMappingViewListResponse, BilanGenerateRequest
)


def test_bilan_mapping_models():
    """Test des modèles BilanMapping."""
    print("🧪 Test BilanMapping models...")
    
    # Test BilanMappingBase
    base = BilanMappingBase(
        category_name="Immobilisations",
        level_1_values=["Achat immobilier"],
        type="ACTIF",
        sub_category="Actif immobilisé",
        is_special=False,
        special_source=None,
        amortization_view_id=None
    )
    assert base.category_name == "Immobilisations"
    assert base.type == "ACTIF"
    print("  ✅ BilanMappingBase fonctionne")
    
    # Test BilanMappingCreate
    create = BilanMappingCreate(
        category_name="Immobilisations",
        level_1_values=["Achat immobilier"],
        type="ACTIF",
        sub_category="Actif immobilisé",
        is_special=False
    )
    assert create.category_name == "Immobilisations"
    print("  ✅ BilanMappingCreate fonctionne")
    
    # Test BilanMappingUpdate (tous les champs optionnels)
    update = BilanMappingUpdate(category_name="Nouveau nom")
    assert update.category_name == "Nouveau nom"
    assert update.type is None
    print("  ✅ BilanMappingUpdate fonctionne")
    
    # Test BilanMappingResponse (avec id et dates)
    response = BilanMappingResponse(
        id=1,
        category_name="Immobilisations",
        level_1_values=["Achat immobilier"],
        type="ACTIF",
        sub_category="Actif immobilisé",
        is_special=False,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    assert response.id == 1
    print("  ✅ BilanMappingResponse fonctionne")
    
    # Test BilanMappingListResponse
    list_response = BilanMappingListResponse(
        mappings=[response],
        total=1
    )
    assert len(list_response.mappings) == 1
    assert list_response.total == 1
    print("  ✅ BilanMappingListResponse fonctionne")


def test_bilan_data_models():
    """Test des modèles BilanData."""
    print("🧪 Test BilanData models...")
    
    # Test BilanDataBase
    base = BilanDataBase(
        annee=2024,
        category_name="Immobilisations",
        amount=150000.50
    )
    assert base.annee == 2024
    assert base.amount == 150000.50
    print("  ✅ BilanDataBase fonctionne")
    
    # Test BilanDataResponse
    response = BilanDataResponse(
        id=1,
        annee=2024,
        category_name="Immobilisations",
        amount=150000.50,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    assert response.id == 1
    print("  ✅ BilanDataResponse fonctionne")
    
    # Test BilanDataListResponse
    list_response = BilanDataListResponse(
        data=[response],
        total=1
    )
    assert len(list_response.data) == 1
    assert list_response.total == 1
    print("  ✅ BilanDataListResponse fonctionne")


def test_bilan_hierarchical_models():
    """Test des modèles hiérarchiques BilanResponse."""
    print("🧪 Test BilanResponse hierarchical models...")
    
    # Test BilanCategoryItem
    category = BilanCategoryItem(
        category_name="Immobilisations",
        amount=150000.50
    )
    assert category.category_name == "Immobilisations"
    assert category.amount == 150000.50
    print("  ✅ BilanCategoryItem fonctionne")
    
    # Test BilanSubCategoryItem
    sub_category = BilanSubCategoryItem(
        sub_category="Actif immobilisé",
        total=150000.50,
        categories=[category]
    )
    assert sub_category.sub_category == "Actif immobilisé"
    assert sub_category.total == 150000.50
    assert len(sub_category.categories) == 1
    print("  ✅ BilanSubCategoryItem fonctionne")
    
    # Test BilanTypeItem
    type_item = BilanTypeItem(
        type="ACTIF",
        total=150000.50,
        sub_categories=[sub_category]
    )
    assert type_item.type == "ACTIF"
    assert type_item.total == 150000.50
    assert len(type_item.sub_categories) == 1
    print("  ✅ BilanTypeItem fonctionne")
    
    # Test BilanResponse
    bilan_response = BilanResponse(
        year=2024,
        types=[type_item],
        equilibre={
            "actif": 150000.50,
            "passif": 150000.50,
            "difference": 0.0,
            "percentage": 0.0
        }
    )
    assert bilan_response.year == 2024
    assert len(bilan_response.types) == 1
    assert bilan_response.equilibre["actif"] == 150000.50
    print("  ✅ BilanResponse fonctionne")


def test_bilan_mapping_view_models():
    """Test des modèles BilanMappingView."""
    print("🧪 Test BilanMappingView models...")
    
    # Test BilanMappingViewCreate
    create = BilanMappingViewCreate(
        name="Test View",
        view_data={
            "mappings": [{"id": 1, "category_name": "Immobilisations"}],
            "selected_level_3_values": ["Immobilisations"]
        }
    )
    assert create.name == "Test View"
    assert "mappings" in create.view_data
    print("  ✅ BilanMappingViewCreate fonctionne")
    
    # Test BilanMappingViewUpdate
    update = BilanMappingViewUpdate(name="Nouveau nom")
    assert update.name == "Nouveau nom"
    assert update.view_data is None
    print("  ✅ BilanMappingViewUpdate fonctionne")
    
    # Test BilanMappingViewResponse
    response = BilanMappingViewResponse(
        id=1,
        name="Test View",
        view_data={"mappings": []},
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    assert response.id == 1
    print("  ✅ BilanMappingViewResponse fonctionne")
    
    # Test BilanMappingViewListResponse
    list_response = BilanMappingViewListResponse(
        views=[response],
        total=1
    )
    assert len(list_response.views) == 1
    assert list_response.total == 1
    print("  ✅ BilanMappingViewListResponse fonctionne")


def test_bilan_generate_request():
    """Test du modèle BilanGenerateRequest."""
    print("🧪 Test BilanGenerateRequest...")
    
    # Test avec selected_level_3_values
    request = BilanGenerateRequest(
        year=2024,
        selected_level_3_values=["Immobilisations", "Capitaux propres"]
    )
    assert request.year == 2024
    assert len(request.selected_level_3_values) == 2
    print("  ✅ BilanGenerateRequest avec level_3 fonctionne")
    
    # Test sans selected_level_3_values
    request2 = BilanGenerateRequest(year=2024)
    assert request2.year == 2024
    assert request2.selected_level_3_values is None
    print("  ✅ BilanGenerateRequest sans level_3 fonctionne")


def test_special_categories():
    """Test des modèles avec catégories spéciales."""
    print("🧪 Test catégories spéciales...")
    
    # Test avec catégorie spéciale
    special_mapping = BilanMappingBase(
        category_name="Amortissements cumulés",
        level_1_values=None,
        type="ACTIF",
        sub_category="Actif immobilisé",
        is_special=True,
        special_source="amortizations",
        amortization_view_id=1
    )
    assert special_mapping.is_special == True
    assert special_mapping.special_source == "amortizations"
    assert special_mapping.amortization_view_id == 1
    print("  ✅ Catégorie spéciale fonctionne")


if __name__ == "__main__":
    print("=" * 60)
    print("Test des modèles Pydantic pour le Bilan (Step 10.3)")
    print("=" * 60)
    print()
    
    try:
        test_bilan_mapping_models()
        print()
        test_bilan_data_models()
        print()
        test_bilan_hierarchical_models()
        print()
        test_bilan_mapping_view_models()
        print()
        test_bilan_generate_request()
        print()
        test_special_categories()
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

