"""
Test script for Pro Rata & Forecast - Step 11bis.1

Tests:
1. Migration - Tables created
2. ProRata Settings - CRUD operations
3. Forecast Configs - CRUD operations
4. Isolation by property_id
5. Bulk upsert

Usage:
    python backend/scripts/test_prorata_forecast_step_11bis_1.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"

# Test counters
tests_passed = 0
tests_failed = 0


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result."""
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"✅ {name}")
    else:
        tests_failed += 1
        print(f"❌ {name}")
    if details:
        print(f"   {details}")


def log_section(title: str):
    """Log section header."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")


def get_test_property_id():
    """Get a valid property ID from the database."""
    try:
        response = requests.get(f"{API_BASE_URL}/properties")
        response.raise_for_status()
        data = response.json()
        if data.get("items") and len(data["items"]) > 0:
            return data["items"][0]["id"]
        else:
            print("⚠️ No properties found in database. Creating a test property...")
            # Create a test property
            response = requests.post(
                f"{API_BASE_URL}/properties",
                json={"name": f"Test Property {datetime.now().timestamp()}", "address": "Test Address"}
            )
            response.raise_for_status()
            return response.json()["id"]
    except Exception as e:
        print(f"❌ Error getting property: {e}")
        return None


# ========================================
# Test 1: Migration - Tables exist
# ========================================
def test_migration():
    """Test that migration created the tables."""
    log_section("Test 1: Migration - Tables created")
    
    # Run migration first
    print("Running migration...")
    from backend.database.migrations.add_prorata_forecast_tables import run_migration
    success = run_migration()
    log_test("Migration executed", success)
    
    # Check tables exist via API (indirectly by testing endpoints)
    return success


# ========================================
# Test 2: ProRata Settings CRUD
# ========================================
def test_prorata_settings_crud(property_id: int):
    """Test ProRata Settings CRUD operations."""
    log_section("Test 2: ProRata Settings CRUD")
    
    # 2.1 GET settings (should create default)
    print("\n2.1 GET /prorata-settings (creates default if not exists)")
    try:
        response = requests.get(f"{API_BASE_URL}/prorata-settings", params={"property_id": property_id})
        data = response.json()
        log_test(
            "GET prorata-settings returns default settings",
            response.status_code == 200 and data.get("prorata_enabled") == False,
            f"Status: {response.status_code}, Data: {json.dumps(data, indent=2)[:200]}"
        )
    except Exception as e:
        log_test("GET prorata-settings", False, str(e))
    
    # 2.2 PUT settings (enable prorata)
    print("\n2.2 PUT /prorata-settings (enable prorata)")
    try:
        response = requests.put(
            f"{API_BASE_URL}/prorata-settings",
            params={"property_id": property_id},
            json={"prorata_enabled": True, "forecast_enabled": False, "forecast_years": 5}
        )
        data = response.json()
        log_test(
            "PUT prorata-settings enables prorata",
            response.status_code == 200 and data.get("prorata_enabled") == True,
            f"Status: {response.status_code}, prorata_enabled={data.get('prorata_enabled')}"
        )
    except Exception as e:
        log_test("PUT prorata-settings", False, str(e))
    
    # 2.3 GET settings again (verify persistence)
    print("\n2.3 GET /prorata-settings (verify persistence)")
    try:
        response = requests.get(f"{API_BASE_URL}/prorata-settings", params={"property_id": property_id})
        data = response.json()
        log_test(
            "GET prorata-settings shows updated values",
            response.status_code == 200 and data.get("prorata_enabled") == True and data.get("forecast_years") == 5,
            f"prorata_enabled={data.get('prorata_enabled')}, forecast_years={data.get('forecast_years')}"
        )
    except Exception as e:
        log_test("GET prorata-settings persistence", False, str(e))


# ========================================
# Test 3: Forecast Configs CRUD
# ========================================
def test_forecast_configs_crud(property_id: int):
    """Test Forecast Configs CRUD operations."""
    log_section("Test 3: Forecast Configs CRUD")
    
    test_year = 2026
    test_type = "compte_resultat"
    
    # 3.1 GET configs (should be empty initially)
    print("\n3.1 GET /forecast-configs (initial - should return list)")
    try:
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs",
            params={"property_id": property_id, "year": test_year, "target_type": test_type}
        )
        data = response.json()
        log_test(
            "GET forecast-configs returns list",
            response.status_code == 200 and isinstance(data, list),
            f"Status: {response.status_code}, Count: {len(data)}"
        )
    except Exception as e:
        log_test("GET forecast-configs", False, str(e))
    
    # 3.2 POST config (create single)
    print("\n3.2 POST /forecast-configs (create single config)")
    config_id = None
    try:
        response = requests.post(
            f"{API_BASE_URL}/forecast-configs",
            json={
                "property_id": property_id,
                "year": test_year,
                "level_1": "Loyers",
                "target_type": test_type,
                "base_annual_amount": 14400.0,
                "annual_growth_rate": 0.02
            }
        )
        data = response.json()
        config_id = data.get("id")
        log_test(
            "POST forecast-configs creates config",
            response.status_code == 201 and data.get("level_1") == "Loyers",
            f"Status: {response.status_code}, id={config_id}, level_1={data.get('level_1')}"
        )
    except Exception as e:
        log_test("POST forecast-configs", False, str(e))
    
    # 3.3 PUT config (update amount)
    print("\n3.3 PUT /forecast-configs/{id} (update amount)")
    if config_id:
        try:
            response = requests.put(
                f"{API_BASE_URL}/forecast-configs/{config_id}",
                params={"property_id": property_id},
                json={"base_annual_amount": 15000.0}
            )
            data = response.json()
            log_test(
                "PUT forecast-configs updates amount",
                response.status_code == 200 and data.get("base_annual_amount") == 15000.0,
                f"Status: {response.status_code}, amount={data.get('base_annual_amount')}"
            )
        except Exception as e:
            log_test("PUT forecast-configs", False, str(e))
    
    # 3.4 GET configs (verify creation)
    print("\n3.4 GET /forecast-configs (verify config exists)")
    try:
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs",
            params={"property_id": property_id, "year": test_year, "target_type": test_type}
        )
        data = response.json()
        has_loyers = any(c.get("level_1") == "Loyers" for c in data)
        log_test(
            "GET forecast-configs shows created config",
            response.status_code == 200 and has_loyers,
            f"Count: {len(data)}, has_loyers={has_loyers}"
        )
    except Exception as e:
        log_test("GET forecast-configs after create", False, str(e))
    
    # 3.5 DELETE config
    print("\n3.5 DELETE /forecast-configs/{id}")
    if config_id:
        try:
            response = requests.delete(
                f"{API_BASE_URL}/forecast-configs/{config_id}",
                params={"property_id": property_id}
            )
            log_test(
                "DELETE forecast-configs removes config",
                response.status_code == 204,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            log_test("DELETE forecast-configs", False, str(e))


# ========================================
# Test 4: Bulk Upsert
# ========================================
def test_bulk_upsert(property_id: int):
    """Test bulk upsert functionality."""
    log_section("Test 4: Bulk Upsert")
    
    test_year = 2026
    test_type = "compte_resultat"
    
    # 4.1 POST bulk (create multiple)
    print("\n4.1 POST /forecast-configs/bulk (create multiple configs)")
    try:
        configs = [
            {"property_id": property_id, "year": test_year, "level_1": "Loyers", "target_type": test_type, "base_annual_amount": 14400.0, "annual_growth_rate": 0.02},
            {"property_id": property_id, "year": test_year, "level_1": "Taxe foncière", "target_type": test_type, "base_annual_amount": 1800.0, "annual_growth_rate": 0.01},
            {"property_id": property_id, "year": test_year, "level_1": "Assurance PNO", "target_type": test_type, "base_annual_amount": 400.0, "annual_growth_rate": 0.015},
        ]
        response = requests.post(
            f"{API_BASE_URL}/forecast-configs/bulk",
            params={"property_id": property_id},
            json=configs
        )
        data = response.json()
        log_test(
            "POST bulk creates multiple configs",
            response.status_code == 200 and len(data) == 3,
            f"Status: {response.status_code}, Created: {len(data)} configs"
        )
    except Exception as e:
        log_test("POST bulk create", False, str(e))
    
    # 4.2 POST bulk again (upsert - update existing)
    print("\n4.2 POST /forecast-configs/bulk (upsert - update existing)")
    try:
        configs = [
            {"property_id": property_id, "year": test_year, "level_1": "Loyers", "target_type": test_type, "base_annual_amount": 15000.0, "annual_growth_rate": 0.03},
            {"property_id": property_id, "year": test_year, "level_1": "Charges copropriété", "target_type": test_type, "base_annual_amount": 2400.0, "annual_growth_rate": 0.02},
        ]
        response = requests.post(
            f"{API_BASE_URL}/forecast-configs/bulk",
            params={"property_id": property_id},
            json=configs
        )
        data = response.json()
        # Check that Loyers was updated
        loyers_config = next((c for c in data if c.get("level_1") == "Loyers"), None)
        updated = loyers_config and loyers_config.get("base_annual_amount") == 15000.0
        log_test(
            "POST bulk upsert updates existing configs",
            response.status_code == 200 and updated,
            f"Status: {response.status_code}, Loyers updated to 15000: {updated}"
        )
    except Exception as e:
        log_test("POST bulk upsert", False, str(e))
    
    # 4.3 GET all configs (should have 4 now)
    print("\n4.3 GET /forecast-configs (verify total count)")
    try:
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs",
            params={"property_id": property_id, "year": test_year, "target_type": test_type}
        )
        data = response.json()
        log_test(
            "GET forecast-configs shows all configs",
            response.status_code == 200 and len(data) == 4,
            f"Status: {response.status_code}, Count: {len(data)} (expected 4)"
        )
    except Exception as e:
        log_test("GET all configs", False, str(e))


# ========================================
# Test 5: Property Isolation
# ========================================
def test_property_isolation():
    """Test that configs are isolated by property_id."""
    log_section("Test 5: Property Isolation")
    
    # Get two different properties
    try:
        response = requests.get(f"{API_BASE_URL}/properties")
        properties = response.json().get("items", [])
        
        if len(properties) < 2:
            print("⚠️ Need at least 2 properties for isolation test. Creating another...")
            response = requests.post(
                f"{API_BASE_URL}/properties",
                json={"name": f"Isolation Test Property {datetime.now().timestamp()}", "address": "Test"}
            )
            properties.append(response.json())
        
        prop1_id = properties[0]["id"]
        prop2_id = properties[1]["id"]
        test_year = 2026
        
        # 5.1 Create config for property 1
        print(f"\n5.1 Create config for property {prop1_id}")
        response = requests.post(
            f"{API_BASE_URL}/forecast-configs/bulk",
            params={"property_id": prop1_id},
            json=[{
                "property_id": prop1_id,
                "year": test_year,
                "level_1": "ISOLATION_TEST",
                "target_type": "compte_resultat",
                "base_annual_amount": 9999.0,
                "annual_growth_rate": 0.0
            }]
        )
        log_test(
            f"Create config for property {prop1_id}",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 5.2 Check property 2 doesn't see it
        print(f"\n5.2 Check property {prop2_id} doesn't see ISOLATION_TEST config")
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs",
            params={"property_id": prop2_id, "year": test_year, "target_type": "compte_resultat"}
        )
        data = response.json()
        has_isolation_test = any(c.get("level_1") == "ISOLATION_TEST" for c in data)
        log_test(
            f"Property {prop2_id} doesn't see ISOLATION_TEST",
            response.status_code == 200 and not has_isolation_test,
            f"has_isolation_test={has_isolation_test}"
        )
        
        # 5.3 Check property 1 sees it
        print(f"\n5.3 Check property {prop1_id} sees ISOLATION_TEST config")
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs",
            params={"property_id": prop1_id, "year": test_year, "target_type": "compte_resultat"}
        )
        data = response.json()
        has_isolation_test = any(c.get("level_1") == "ISOLATION_TEST" for c in data)
        log_test(
            f"Property {prop1_id} sees ISOLATION_TEST",
            response.status_code == 200 and has_isolation_test,
            f"has_isolation_test={has_isolation_test}"
        )
        
    except Exception as e:
        log_test("Property isolation test", False, str(e))


# ========================================
# Test 6: Reference Data Endpoint
# ========================================
def test_reference_data(property_id: int):
    """Test reference data endpoint."""
    log_section("Test 6: Reference Data Endpoint")
    
    print("\n6.1 GET /forecast-configs/reference-data")
    try:
        response = requests.get(
            f"{API_BASE_URL}/forecast-configs/reference-data",
            params={"property_id": property_id, "year": 2026, "target_type": "compte_resultat"}
        )
        data = response.json()
        log_test(
            "GET reference-data returns valid structure",
            response.status_code == 200 and "categories" in data and "year" in data,
            f"Status: {response.status_code}, keys: {list(data.keys())}"
        )
    except Exception as e:
        log_test("GET reference-data", False, str(e))


# ========================================
# Main
# ========================================
def main():
    print("\n" + "="*60)
    print("🧪 TEST: Pro Rata & Forecast - Step 11bis.1")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Run migration first
    test_migration()
    
    # Get a test property
    property_id = get_test_property_id()
    if not property_id:
        print("\n❌ Cannot proceed without a valid property_id")
        return
    
    print(f"\n📌 Using property_id: {property_id}")
    
    # Run tests
    test_prorata_settings_crud(property_id)
    test_forecast_configs_crud(property_id)
    test_bulk_upsert(property_id)
    test_property_isolation()
    test_reference_data(property_id)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Tests passed: {tests_passed}")
    print(f"❌ Tests failed: {tests_failed}")
    total = tests_passed + tests_failed
    if total > 0:
        print(f"📈 Success rate: {(tests_passed/total)*100:.1f}%")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {tests_failed} tests failed")


if __name__ == "__main__":
    main()
