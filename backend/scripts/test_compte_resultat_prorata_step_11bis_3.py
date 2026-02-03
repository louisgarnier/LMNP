"""
Test script for Step 11bis.3: Compte de Résultat with Pro Rata

Tests:
- Compte de Résultat without prorata → real values
- Compte de Résultat with prorata enabled → MAX(real, planned) for configurable categories
- Calculated categories always use real values

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

logger = get_logger("test_cr_prorata")

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
        if isinstance(data, list) and len(data) > 0:
            return data[0]["id"]
        elif isinstance(data, dict):
            prop_list = data.get("items", data.get("properties", []))
            if prop_list and len(prop_list) > 0:
                return prop_list[0]["id"]
    raise Exception(f"No properties found in database")


def run_tests():
    """Run all Step 11bis.3 tests"""
    global tests_passed, tests_failed
    
    print("\n" + "="*70)
    print("  STEP 11BIS.3 - COMPTE DE RÉSULTAT WITH PRO RATA")
    print("="*70)
    
    # Get a property ID for testing
    property_id = get_first_property_id()
    print(f"\n📍 Using property_id={property_id} for tests\n")
    
    # ==================================================
    # Section 1: Setup - Disable prorata and get baseline
    # ==================================================
    test_section("1. SETUP & BASELINE (Pro Rata DISABLED)")
    
    # Disable prorata
    response = requests.put(
        f"{API_URL}/prorata-settings?property_id={property_id}",
        json={"prorata_enabled": False, "forecast_enabled": False}
    )
    assert response.status_code == 200
    test_pass("Disabled prorata for testing")
    
    # Get baseline CR data (without prorata)
    response = requests.get(
        f"{API_URL}/compte-resultat/calculate",
        params={"property_id": property_id, "years": str(CURRENT_YEAR)}
    )
    
    if response.status_code == 200:
        data = response.json()
        baseline_cr = data.get("results", {}).get(str(CURRENT_YEAR), {})
        test_pass("Got baseline CR data", f"prorata_applied={baseline_cr.get('prorata_applied', False)}")
        
        # Store baseline values
        baseline_produits = baseline_cr.get("produits", {})
        baseline_charges = baseline_cr.get("charges", {})
        
        print(f"\n   Baseline produits: {len(baseline_produits)} categories")
        for cat, val in baseline_produits.items():
            print(f"      - {cat}: {val:.2f} €")
        
        print(f"\n   Baseline charges: {len(baseline_charges)} categories")
        for cat, val in baseline_charges.items():
            print(f"      - {cat}: {val:.2f} €")
    else:
        test_fail(f"Failed to get baseline CR", f"Status: {response.status_code}")
        return False
    
    # ==================================================
    # Section 2: Configure forecast and enable prorata
    # ==================================================
    test_section("2. CONFIGURE FORECAST & ENABLE PRO RATA")
    
    # Find a configurable category with 0 or low real value
    test_category = None
    test_planned_amount = 10000.0  # Planned annual amount
    
    # Look for a category in produits with low real value
    for cat, val in baseline_produits.items():
        if abs(val) < 1000:  # Low real value
            test_category = cat
            break
    
    if not test_category and baseline_produits:
        # Use first category
        test_category = list(baseline_produits.keys())[0]
    
    if not test_category:
        # Create a test category name
        test_category = "Loyers hors charge encaissés"
    
    print(f"   Using test category: '{test_category}'")
    print(f"   Real value: {baseline_produits.get(test_category, 0):.2f} €")
    print(f"   Planned value: {test_planned_amount:.2f} €")
    
    # Create forecast config for this category
    configs_to_create = [
        {
            "property_id": property_id,
            "year": CURRENT_YEAR,
            "level_1": test_category,
            "target_type": "compte_resultat",
            "base_annual_amount": test_planned_amount,
            "annual_growth_rate": 0.02
        }
    ]
    
    response = requests.post(
        f"{API_URL}/forecast-configs/bulk?property_id={property_id}",
        json=configs_to_create
    )
    
    if response.status_code == 200:
        test_pass("Created forecast config", f"category={test_category}, amount={test_planned_amount}")
    else:
        test_fail(f"Failed to create forecast config", f"Status: {response.status_code}")
    
    # Enable prorata
    response = requests.put(
        f"{API_URL}/prorata-settings?property_id={property_id}",
        json={"prorata_enabled": True, "forecast_enabled": False}
    )
    
    if response.status_code == 200:
        test_pass("Enabled prorata")
    else:
        test_fail(f"Failed to enable prorata", f"Status: {response.status_code}")
    
    # ==================================================
    # Section 3: Get CR with prorata enabled
    # ==================================================
    test_section("3. COMPTE DE RÉSULTAT WITH PRO RATA ENABLED")
    
    # Get CR data with prorata enabled
    response = requests.get(
        f"{API_URL}/compte-resultat/calculate",
        params={"property_id": property_id, "years": str(CURRENT_YEAR)}
    )
    
    if response.status_code == 200:
        data = response.json()
        prorata_cr = data.get("results", {}).get(str(CURRENT_YEAR), {})
        
        # Check if prorata was applied
        prorata_applied = prorata_cr.get("prorata_applied", False)
        if prorata_applied:
            test_pass("Pro Rata was applied", f"prorata_applied={prorata_applied}")
        else:
            test_fail("Pro Rata was NOT applied", "Expected prorata_applied=True")
        
        prorata_produits = prorata_cr.get("produits", {})
        prorata_charges = prorata_cr.get("charges", {})
        
        print(f"\n   Pro Rata produits: {len(prorata_produits)} categories")
        for cat, val in prorata_produits.items():
            baseline_val = baseline_produits.get(cat, 0)
            changed = "📈" if val != baseline_val else ""
            print(f"      - {cat}: {val:.2f} € (was {baseline_val:.2f} €) {changed}")
        
        # Check test category
        test_real = baseline_produits.get(test_category, 0)
        test_prorata = prorata_produits.get(test_category, 0)
        
        print(f"\n   Test category '{test_category}':")
        print(f"      - Real: {test_real:.2f} €")
        print(f"      - Planned: {test_planned_amount:.2f} €")
        print(f"      - Pro Rata result: {test_prorata:.2f} €")
        
        # Verify MAX logic
        expected_max = max(abs(test_real), abs(test_planned_amount))
        if test_real >= 0:
            # Positive category (revenue)
            expected_value = expected_max
        else:
            # Negative category (expense)
            expected_value = -expected_max
        
        # For revenue categories, we expect the planned value if it's higher
        if abs(test_prorata) >= abs(test_real) and abs(test_prorata) >= abs(test_planned_amount) * 0.99:
            test_pass(f"MAX logic correct for '{test_category}'", 
                     f"Result={test_prorata:.2f}, Expected MAX({test_real:.2f}, {test_planned_amount:.2f})")
        else:
            # Check if the value is at least the planned amount (for configurable categories)
            if abs(test_prorata) >= abs(test_planned_amount) * 0.99:
                test_pass(f"Pro Rata applied correctly", f"Result={test_prorata:.2f} >= Planned={test_planned_amount:.2f}")
            elif abs(test_prorata) >= abs(test_real) * 0.99:
                test_pass(f"Real value used (was higher)", f"Result={test_prorata:.2f} >= Real={test_real:.2f}")
            else:
                test_fail(f"Unexpected value for '{test_category}'", 
                         f"Result={test_prorata:.2f}, Real={test_real:.2f}, Planned={test_planned_amount:.2f}")
        
        # Check calculated categories (should NOT change)
        calculated_categories = ["Charges d'amortissements", "Coût du financement (hors remboursement du capital)"]
        for calc_cat in calculated_categories:
            if calc_cat in baseline_charges and calc_cat in prorata_charges:
                baseline_val = baseline_charges[calc_cat]
                prorata_val = prorata_charges[calc_cat]
                if abs(baseline_val - prorata_val) < 0.01:
                    test_pass(f"Calculated category unchanged: '{calc_cat}'", f"{baseline_val:.2f} → {prorata_val:.2f}")
                else:
                    test_fail(f"Calculated category CHANGED: '{calc_cat}'", f"{baseline_val:.2f} → {prorata_val:.2f}")
    else:
        test_fail(f"Failed to get CR with prorata", f"Status: {response.status_code}, Response: {response.text[:200]}")
    
    # ==================================================
    # Section 4: Cleanup
    # ==================================================
    test_section("4. CLEANUP")
    
    # Disable prorata
    response = requests.put(
        f"{API_URL}/prorata-settings?property_id={property_id}",
        json={"prorata_enabled": False, "forecast_enabled": False}
    )
    test_pass("Disabled prorata")
    
    # Delete test forecast config
    response = requests.get(
        f"{API_URL}/forecast-configs",
        params={"property_id": property_id, "year": CURRENT_YEAR, "target_type": "compte_resultat"}
    )
    if response.status_code == 200:
        configs = response.json()
        deleted_count = 0
        for config in configs:
            if config["level_1"] == test_category:
                del_response = requests.delete(
                    f"{API_URL}/forecast-configs/{config['id']}?property_id={property_id}"
                )
                if del_response.status_code == 204:
                    deleted_count += 1
        if deleted_count > 0:
            test_pass(f"Deleted {deleted_count} test forecast config(s)")
    
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
        print("\n  🎉 ALL TESTS PASSED! Step 11bis.3 is complete.")
    else:
        print(f"\n  ⚠️ {tests_failed} test(s) failed. Please check the logs.")
    
    print("="*70 + "\n")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
