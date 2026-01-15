"""
Test script for compte_resultat_override API routes.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md

This script tests the API routes for overrides.
Make sure the backend server is running before executing this script.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_get_all_overrides():
    """Test GET /api/compte-resultat/override"""
    print("Test 1: GET /api/compte-resultat/override")
    response = requests.get(f"{BASE_URL}/compte-resultat/override")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Overrides retrieved: {len(data)} override(s)")
        for o in data:
            print(f"   - Year {o['year']}: {o['override_value']} €")
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_get_override_by_year(year: int):
    """Test GET /api/compte-resultat/override/{year}"""
    print(f"Test 2: GET /api/compte-resultat/override/{year}")
    response = requests.get(f"{BASE_URL}/compte-resultat/override/{year}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Override found: Year {data['year']}, Value {data['override_value']} €")
    elif response.status_code == 404:
        print(f"ℹ️  No override found for year {year} (expected if not created yet)")
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_create_override(year: int, value: float):
    """Test POST /api/compte-resultat/override"""
    print(f"Test 3: POST /api/compte-resultat/override (year={year}, value={value})")
    payload = {
        "year": year,
        "override_value": value
    }
    response = requests.post(
        f"{BASE_URL}/compte-resultat/override",
        json=payload
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Override created: ID={data['id']}, Year={data['year']}, Value={data['override_value']} €")
        return data
    else:
        print(f"❌ Error: {response.text}")
    print()
    return None


def test_update_override(year: int, new_value: float):
    """Test POST /api/compte-resultat/override (update existing)"""
    print(f"Test 4: POST /api/compte-resultat/override (update year={year}, new_value={new_value})")
    payload = {
        "year": year,
        "override_value": new_value
    }
    response = requests.post(
        f"{BASE_URL}/compte-resultat/override",
        json=payload
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Override updated: Year={data['year']}, Value={data['override_value']} €")
        return data
    else:
        print(f"❌ Error: {response.text}")
    print()
    return None


def test_delete_override(year: int):
    """Test DELETE /api/compte-resultat/override/{year}"""
    print(f"Test 5: DELETE /api/compte-resultat/override/{year}")
    response = requests.delete(f"{BASE_URL}/compte-resultat/override/{year}")
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✅ Override deleted for year {year}")
    elif response.status_code == 404:
        print(f"ℹ️  No override found for year {year} (already deleted or never existed)")
    else:
        print(f"❌ Error: {response.text}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Compte Resultat Override API Routes")
    print("=" * 60)
    print()
    
    # Test 1: Get all overrides (should be empty initially)
    test_get_all_overrides()
    
    # Test 2: Get override for non-existent year (should return 404)
    test_get_override_by_year(2023)
    
    # Test 3: Create an override
    override = test_create_override(2023, 5000.50)
    
    # Test 2 again: Get override for existing year (should return 200)
    test_get_override_by_year(2023)
    
    # Test 1 again: Get all overrides (should have one)
    test_get_all_overrides()
    
    # Test 4: Update the override
    test_update_override(2023, 7500.75)
    
    # Verify update
    test_get_override_by_year(2023)
    
    # Test 5: Delete the override
    test_delete_override(2023)
    
    # Verify deletion
    test_get_override_by_year(2023)
    test_get_all_overrides()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the backend server.")
        print("   Make sure the backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
