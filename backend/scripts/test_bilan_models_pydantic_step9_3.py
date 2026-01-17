"""
Test script for Step 9.3: Bilan Pydantic models.

This script tests:
1. That all Pydantic models are importable
2. That models can be instantiated with valid data
3. That validation works correctly
4. That the hierarchical structure (BilanResponse) works

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.models import (
    BilanMappingBase, BilanMappingCreate, BilanMappingUpdate, BilanMappingResponse,
    BilanMappingListResponse,
    BilanDataBase, BilanDataCreate, BilanDataUpdate, BilanDataResponse,
    BilanDataListResponse,
    BilanConfigBase, BilanConfigCreate, BilanConfigUpdate, BilanConfigResponse,
    BilanCalculateRequest,
    BilanCategoryItem, BilanSubCategoryItem, BilanTypeItem, BilanResponse
)


def test_bilan_mapping_models():
    """Test BilanMapping models."""
    print("📋 Testing BilanMapping models...")
    
    try:
        # Test Base
        base = BilanMappingBase(
            category_name="Immobilisations",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=json.dumps(["IMMOBILISATIONS"]),
            is_special=False
        )
        print("   ✅ BilanMappingBase created")
        
        # Test Create
        create = BilanMappingCreate(
            category_name="Immobilisations",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=json.dumps(["IMMOBILISATIONS"]),
            is_special=False
        )
        print("   ✅ BilanMappingCreate created")
        
        # Test Update
        update = BilanMappingUpdate(category_name="Immobilisations modifiées")
        print("   ✅ BilanMappingUpdate created")
        
        # Test Response
        response = BilanMappingResponse(
            id=1,
            category_name="Immobilisations",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=json.dumps(["IMMOBILISATIONS"]),
            is_special=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("   ✅ BilanMappingResponse created")
        
        # Test ListResponse
        list_response = BilanMappingListResponse(
            items=[response],
            total=1
        )
        print("   ✅ BilanMappingListResponse created")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bilan_data_models():
    """Test BilanData models."""
    print("\n📋 Testing BilanData models...")
    
    try:
        # Test Base
        base = BilanDataBase(
            annee=2024,
            category_name="Immobilisations",
            amount=100000.50
        )
        print("   ✅ BilanDataBase created")
        
        # Test Create
        create = BilanDataCreate(
            annee=2024,
            category_name="Immobilisations",
            amount=100000.50
        )
        print("   ✅ BilanDataCreate created")
        
        # Test Update
        update = BilanDataUpdate(amount=150000.75)
        print("   ✅ BilanDataUpdate created")
        
        # Test Response
        response = BilanDataResponse(
            id=1,
            annee=2024,
            category_name="Immobilisations",
            amount=100000.50,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("   ✅ BilanDataResponse created")
        
        # Test ListResponse
        list_response = BilanDataListResponse(
            items=[response],
            total=1
        )
        print("   ✅ BilanDataListResponse created")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bilan_config_models():
    """Test BilanConfig models."""
    print("\n📋 Testing BilanConfig models...")
    
    try:
        # Test Base
        base = BilanConfigBase(
            level_3_values=json.dumps(["VALEUR1", "VALEUR2"])
        )
        print("   ✅ BilanConfigBase created")
        
        # Test Create
        create = BilanConfigCreate(
            level_3_values=json.dumps(["VALEUR1", "VALEUR2"])
        )
        print("   ✅ BilanConfigCreate created")
        
        # Test Update
        update = BilanConfigUpdate(level_3_values=json.dumps(["VALEUR3", "VALEUR4"]))
        print("   ✅ BilanConfigUpdate created")
        
        # Test Response
        response = BilanConfigResponse(
            id=1,
            level_3_values=json.dumps(["VALEUR1", "VALEUR2"]),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("   ✅ BilanConfigResponse created")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bilan_calculate_request():
    """Test BilanCalculateRequest."""
    print("\n📋 Testing BilanCalculateRequest...")
    
    try:
        # Test with year only
        request1 = BilanCalculateRequest(year=2024)
        print("   ✅ BilanCalculateRequest (year only) created")
        
        # Test with year and level_3_values
        request2 = BilanCalculateRequest(
            year=2024,
            selected_level_3_values=["VALEUR1", "VALEUR2"]
        )
        print("   ✅ BilanCalculateRequest (with level_3_values) created")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bilan_hierarchical_structure():
    """Test BilanResponse hierarchical structure."""
    print("\n📋 Testing BilanResponse hierarchical structure...")
    
    try:
        # Create category items
        category1 = BilanCategoryItem(
            category_name="Immobilisations",
            amount=100000.0,
            is_special=False
        )
        category2 = BilanCategoryItem(
            category_name="Amortissements cumulés",
            amount=-33221.73,
            is_special=True
        )
        
        # Create sub-category items
        sub_category1 = BilanSubCategoryItem(
            sub_category="Actif immobilisé",
            total=66778.27,  # 100000 - 33221.73
            categories=[category1, category2]
        )
        
        # Create type items
        type1 = BilanTypeItem(
            type="ACTIF",
            total=66778.27,
            sub_categories=[sub_category1]
        )
        
        type2 = BilanTypeItem(
            type="PASSIF",
            total=66778.27,
            sub_categories=[]
        )
        
        # Create bilan response
        bilan_response = BilanResponse(
            year=2024,
            types=[type1, type2],
            actif_total=66778.27,
            passif_total=66778.27,
            difference=0.0,
            difference_percent=0.0
        )
        
        print("   ✅ BilanResponse hierarchical structure created")
        print(f"      - Year: {bilan_response.year}")
        print(f"      - Types: {len(bilan_response.types)}")
        print(f"      - ACTIF total: {bilan_response.actif_total:.2f} €")
        print(f"      - PASSIF total: {bilan_response.passif_total:.2f} €")
        print(f"      - Difference: {bilan_response.difference:.2f} €")
        print(f"      - Difference %: {bilan_response.difference_percent:.2f}%")
        
        # Test serialization
        json_data = bilan_response.model_dump()
        print("   ✅ BilanResponse can be serialized to dict")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_special_category_mapping():
    """Test mapping with special category."""
    print("\n📋 Testing special category mapping...")
    
    try:
        # Test mapping with special category (amortissements)
        mapping = BilanMappingResponse(
            id=1,
            category_name="Amortissements cumulés",
            type="ACTIF",
            sub_category="Actif immobilisé",
            level_1_values=None,
            is_special=True,
            special_source="amortization_result",
            compte_resultat_view_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("   ✅ Special category mapping created")
        print(f"      - is_special: {mapping.is_special}")
        print(f"      - special_source: {mapping.special_source}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Bilan Pydantic Models (Step 9.3)")
    print("=" * 60)
    
    results = []
    
    results.append(("BilanMapping models", test_bilan_mapping_models()))
    results.append(("BilanData models", test_bilan_data_models()))
    results.append(("BilanConfig models", test_bilan_config_models()))
    results.append(("BilanCalculateRequest", test_bilan_calculate_request()))
    results.append(("Bilan hierarchical structure", test_bilan_hierarchical_structure()))
    results.append(("Special category mapping", test_special_category_mapping()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
