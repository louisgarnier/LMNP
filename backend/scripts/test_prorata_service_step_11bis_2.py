"""
Test script for Step 11bis.2: Pro Rata Service Logic

Tests:
- prorata_service.py functions (apply_prorata, calculate_forecast_amount, etc.)
- get_reference_data endpoint with real data
- Logic: MAX(réel, prévu) pour catégories configurables
- Logic: valeurs réelles pour catégories calculées

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.api.utils.logger_config import get_logger

logger = get_logger("test_prorata_service")

# API configuration
API_URL = "http://localhost:8000/api"
CURRENT_YEAR = datetime.now().year

# Test counters
tests_passed = 0
tests_failed = 0


def test_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_pass(message: str, details: str = None):
    """Log test success"""
    global tests_passed
    tests_passed += 1
    print(f"✅ {message}")
    if details:
        print(f"   {details}")
    logger.info(f"TEST PASS: {message}")


def test_fail(message: str, details: str = None):
    """Log test failure"""
    global tests_failed
    tests_failed += 1
    print(f"❌ {message}")
    if details:
        print(f"   {details}")
    logger.error(f"TEST FAIL: {message} - {details}")


def get_first_property_id() -> int:
    """Get the first available property ID"""
    response = requests.get(f"{API_URL}/properties")
    if response.status_code == 200:
        data = response.json()
        # Handle different response formats
        if isinstance(data, list) and len(data) > 0:
            return data[0]["id"]
        elif isinstance(data, dict):
            # Paginated response with "items" key
            prop_list = data.get("items", data.get("properties", []))
            if prop_list and len(prop_list) > 0:
                return prop_list[0]["id"]
    raise Exception(f"No properties found in database. Response: {response.text[:200]}")


def run_tests():
    """Run all Step 11bis.2 tests"""
    global tests_passed, tests_failed
    
    print("\n" + "="*70)
    print("  STEP 11BIS.2 - PRO RATA SERVICE TESTS")
    print("="*70)
    
    # Get a property ID for testing
    property_id = get_first_property_id()
    print(f"\n📍 Using property_id={property_id} for tests\n")
    
    # ==================================================
    # Section 1: Test prorata_service functions directly
    # ==================================================
    test_section("1. PRORATA SERVICE DIRECT TESTS")
    
    # Import the service functions
    from backend.api.services.prorata_service import (
        is_calculated_category,
        get_calculated_categories,
        calculate_forecast_amount,
        apply_prorata,
        get_prorata_settings,
        get_forecast_configs,
    )
    from backend.database.connection import SessionLocal
    
    # Test 1.1: is_calculated_category
    print("1.1 Testing is_calculated_category()")
    
    # Compte de résultat - calculated
    assert is_calculated_category("Dotations aux amortissements", "compte_resultat") == True
    assert is_calculated_category("Charges financières", "compte_resultat") == True
    test_pass("Dotations aux amortissements is calculated for compte_resultat")
    
    # Compte de résultat - NOT calculated
    assert is_calculated_category("Loyers", "compte_resultat") == False
    assert is_calculated_category("Taxe foncière", "compte_resultat") == False
    test_pass("Loyers is NOT calculated for compte_resultat")
    
    # Bilan actif - calculated
    assert is_calculated_category("Amortissements cumulés", "bilan_actif") == True
    assert is_calculated_category("Compte bancaire", "bilan_actif") == True
    test_pass("Amortissements cumulés is calculated for bilan_actif")
    
    # Bilan passif - calculated
    assert is_calculated_category("Résultat de l'exercice", "bilan_passif") == True
    assert is_calculated_category("Report à nouveau", "bilan_passif") == True
    test_pass("Résultat de l'exercice is calculated for bilan_passif")
    
    # Bilan passif - NOT calculated
    assert is_calculated_category("Capital", "bilan_passif") == False
    test_pass("Capital is NOT calculated for bilan_passif")
    
    # Test 1.2: calculate_forecast_amount
    print("\n1.2 Testing calculate_forecast_amount()")
    
    # Base case: 0 years ahead
    result = calculate_forecast_amount(1000.0, 0.02, 0)
    assert result == 1000.0, f"Expected 1000.0, got {result}"
    test_pass("0 years ahead returns base amount", f"1000.0 × (1 + 0.02)^0 = {result}")
    
    # 1 year ahead with 2% growth
    result = calculate_forecast_amount(1000.0, 0.02, 1)
    expected = 1000.0 * 1.02
    assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    test_pass("1 year ahead with 2% growth", f"1000.0 × (1 + 0.02)^1 = {result}")
    
    # 3 years ahead with 5% growth
    result = calculate_forecast_amount(1000.0, 0.05, 3)
    expected = 1000.0 * (1.05 ** 3)
    assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    test_pass("3 years ahead with 5% growth", f"1000.0 × (1 + 0.05)^3 = {result:.2f}")
    
    # Negative growth rate (depreciation)
    result = calculate_forecast_amount(1000.0, -0.10, 2)
    expected = 1000.0 * (0.90 ** 2)
    assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    test_pass("Negative growth rate (depreciation)", f"1000.0 × (1 - 0.10)^2 = {result:.2f}")
    
    # Test 1.3: apply_prorata with disabled settings
    print("\n1.3 Testing apply_prorata() with DISABLED settings")
    
    db = SessionLocal()
    try:
        # Make sure prorata is disabled
        response = requests.put(
            f"{API_URL}/prorata-settings?property_id={property_id}",
            json={"prorata_enabled": False, "forecast_enabled": False}
        )
        assert response.status_code == 200
        
        real_amounts = {
            "Loyers": 5000.0,
            "Taxe foncière": -1500.0,
            "Dotations aux amortissements": -3000.0,  # Calculated category
        }
        
        result = apply_prorata(db, property_id, CURRENT_YEAR, "compte_resultat", real_amounts)
        
        # All should return real values when disabled
        assert result["Loyers"]["amount"] == 5000.0, f"Expected 5000.0, got {result['Loyers']['amount']}"
        assert result["Loyers"]["source"] == "real"
        test_pass("Disabled: Loyers returns real value", f"amount={result['Loyers']['amount']}, source={result['Loyers']['source']}")
        
        assert result["Dotations aux amortissements"]["amount"] == -3000.0
        assert result["Dotations aux amortissements"]["is_calculated"] == True
        test_pass("Disabled: Calculated category still marked as calculated")
        
    finally:
        db.close()
    
    # Test 1.4: apply_prorata with ENABLED settings and forecast configs
    print("\n1.4 Testing apply_prorata() with ENABLED settings")
    
    # Enable prorata and create forecast configs
    response = requests.put(
        f"{API_URL}/prorata-settings?property_id={property_id}",
        json={"prorata_enabled": True, "forecast_enabled": False}
    )
    assert response.status_code == 200
    
    # Create forecast configs for testing MAX logic
    configs_to_create = [
        {
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "level_1": "TEST_LOYERS",
            "target_type": "compte_resultat",
            "base_annual_amount": 12000.0,  # Prévu > Réel
            "annual_growth_rate": 0.02
        },
        {
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "level_1": "TEST_CHARGES",
            "target_type": "compte_resultat",
            "base_annual_amount": -2000.0,  # Prévu < Réel (in absolute value)
            "annual_growth_rate": 0.01
        }
    ]
    
    response = requests.post(
        f"{API_URL}/forecast-configs/bulk?property_id={property_id}",
        json=configs_to_create
    )
    assert response.status_code == 200
    
    db = SessionLocal()
    try:
        # Test case: Réel < Prévu → use Prévu
        real_amounts = {
            "TEST_LOYERS": 5000.0,  # Real is 5000, Prévu is 12000
        }
        
        result = apply_prorata(db, property_id, CURRENT_YEAR, "compte_resultat", real_amounts)
        
        assert result["TEST_LOYERS"]["amount"] == 12000.0, f"Expected 12000.0 (prévu), got {result['TEST_LOYERS']['amount']}"
        assert result["TEST_LOYERS"]["source"] == "planned"
        test_pass("MAX: Réel (5000) < Prévu (12000) → returns Prévu", 
                  f"amount={result['TEST_LOYERS']['amount']}, source={result['TEST_LOYERS']['source']}")
        
        # Test case: Réel > Prévu → use Réel
        real_amounts = {
            "TEST_CHARGES": -5000.0,  # Real is -5000, Prévu is -2000 (abs: 5000 > 2000)
        }
        
        result = apply_prorata(db, property_id, CURRENT_YEAR, "compte_resultat", real_amounts)
        
        assert result["TEST_CHARGES"]["amount"] == -5000.0, f"Expected -5000.0 (réel), got {result['TEST_CHARGES']['amount']}"
        assert result["TEST_CHARGES"]["source"] == "real"
        test_pass("MAX: |Réel| (5000) > |Prévu| (2000) → returns Réel", 
                  f"amount={result['TEST_CHARGES']['amount']}, source={result['TEST_CHARGES']['source']}")
        
        # Test case: Réel = 0 → use Prévu
        real_amounts = {
            "TEST_LOYERS": 0.0,  # Real is 0, Prévu is 12000
        }
        
        result = apply_prorata(db, property_id, CURRENT_YEAR, "compte_resultat", real_amounts)
        
        assert result["TEST_LOYERS"]["amount"] == 12000.0, f"Expected 12000.0 (prévu), got {result['TEST_LOYERS']['amount']}"
        assert result["TEST_LOYERS"]["source"] == "planned"
        test_pass("MAX: Réel = 0, Prévu = 12000 → returns Prévu", 
                  f"amount={result['TEST_LOYERS']['amount']}, source={result['TEST_LOYERS']['source']}")
        
        # Test case: Catégorie calculée → toujours réel
        real_amounts = {
            "Dotations aux amortissements": -3000.0,
        }
        
        result = apply_prorata(db, property_id, CURRENT_YEAR, "compte_resultat", real_amounts)
        
        assert result["Dotations aux amortissements"]["amount"] == -3000.0
        assert result["Dotations aux amortissements"]["is_calculated"] == True
        assert result["Dotations aux amortissements"]["source"] == "calculated"
        test_pass("Calculated category always returns real value", 
                  f"is_calculated=True, source=calculated")
        
    finally:
        db.close()
    
    # ==================================================
    # Section 2: Test get_reference_data endpoint
    # ==================================================
    test_section("2. GET REFERENCE DATA ENDPOINT")
    
    # Test 2.1: Get reference data for compte_resultat
    print("2.1 Testing GET /forecast-configs/reference-data for compte_resultat")
    
    response = requests.get(
        f"{API_URL}/forecast-configs/reference-data",
        params={
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "target_type": "compte_resultat"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        test_pass("GET reference-data returns 200", f"Got {len(data.get('categories', []))} categories")
        
        # Check response structure
        assert "categories" in data
        assert "year" in data
        assert "target_type" in data
        assert data["year"] == CURRENT_YEAR
        assert data["target_type"] == "compte_resultat"
        test_pass("Response structure is correct")
        
        # Check if categories have correct fields
        if data["categories"]:
            cat = data["categories"][0]
            assert "level_1" in cat
            assert "real_current_year" in cat
            assert "real_previous_year" in cat
            assert "is_calculated" in cat
            test_pass("Category structure is correct", f"First category: {cat['level_1']}")
        else:
            print("   ⚠️ No categories returned (property may have no transactions)")
    else:
        test_fail(f"GET reference-data failed", f"Status: {response.status_code}, Response: {response.text}")
    
    # Test 2.2: Get reference data for bilan_actif
    print("\n2.2 Testing GET /forecast-configs/reference-data for bilan_actif")
    
    response = requests.get(
        f"{API_URL}/forecast-configs/reference-data",
        params={
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "target_type": "bilan_actif"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        test_pass("GET bilan_actif returns 200", f"Got {len(data.get('categories', []))} categories")
        
        # Check for calculated categories
        calculated_found = False
        for cat in data.get("categories", []):
            if cat.get("is_calculated"):
                calculated_found = True
                print(f"   📊 Calculated: {cat['level_1']}")
        
        if calculated_found:
            test_pass("Found calculated categories in bilan_actif")
    else:
        test_fail(f"GET bilan_actif failed", f"Status: {response.status_code}")
    
    # Test 2.3: Get reference data for bilan_passif
    print("\n2.3 Testing GET /forecast-configs/reference-data for bilan_passif")
    
    response = requests.get(
        f"{API_URL}/forecast-configs/reference-data",
        params={
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "target_type": "bilan_passif"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        test_pass("GET bilan_passif returns 200", f"Got {len(data.get('categories', []))} categories")
    else:
        test_fail(f"GET bilan_passif failed", f"Status: {response.status_code}")
    
    # Test 2.4: Test with invalid target_type
    print("\n2.4 Testing GET /forecast-configs/reference-data with invalid target_type")
    
    response = requests.get(
        f"{API_URL}/forecast-configs/reference-data",
        params={
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "target_type": "invalid_type"
        }
    )
    
    if response.status_code == 400:
        test_pass("Invalid target_type returns 400")
    else:
        # May return empty list instead of error
        data = response.json()
        if len(data.get("categories", [])) == 0:
            test_pass("Invalid target_type returns empty categories (acceptable)")
        else:
            test_fail(f"Expected 400 or empty list", f"Got status {response.status_code}")
    
    # ==================================================
    # Section 3: Cleanup test data
    # ==================================================
    test_section("3. CLEANUP")
    
    # Reset prorata settings
    response = requests.put(
        f"{API_URL}/prorata-settings?property_id={property_id}",
        json={"prorata_enabled": False, "forecast_enabled": False}
    )
    test_pass("Reset prorata settings to disabled")
    
    # Delete test forecast configs (those starting with TEST_)
    response = requests.get(
        f"{API_URL}/forecast-configs",
        params={"property_id": property_id, "year": CURRENT_YEAR, "target_type": "compte_resultat"}
    )
    if response.status_code == 200:
        configs = response.json()
        deleted_count = 0
        for config in configs:
            if config["level_1"].startswith("TEST_"):
                del_response = requests.delete(
                    f"{API_URL}/forecast-configs/{config['id']}?property_id={property_id}"
                )
                if del_response.status_code == 204:
                    deleted_count += 1
        test_pass(f"Deleted {deleted_count} test forecast configs")
    
    # ==================================================
    # SUMMARY
    # ==================================================
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"\n  ✅ Tests passed: {tests_passed}")
    print(f"  ❌ Tests failed: {tests_failed}")
    print(f"  📊 Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n  🎉 ALL TESTS PASSED! Step 11bis.2 is complete.")
    else:
        print(f"\n  ⚠️ {tests_failed} test(s) failed. Please check the logs.")
    
    print("="*70 + "\n")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
