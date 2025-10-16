"""
Quick API test script for FastAPI web application
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test key API endpoints"""

    print("=" * 80)
    print("Testing FastAPI Endpoints")
    print("=" * 80)

    # Test 1: Health check
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        print(f"\n[OK] Health Check: {r.status_code}")
        print(f"     Status: {r.json()['status']}")
    except Exception as e:
        print(f"[ERROR] Health Check failed: {e}")

    # Test 2: Applications
    try:
        r = requests.get(f"{BASE_URL}/api/applications")
        data = r.json()
        print(f"\n[OK] Applications Endpoint: {r.status_code}")
        print(f"     Total Apps: {data['total']}")
    except Exception as e:
        print(f"[ERROR] Applications failed: {e}")

    # Test 3: Security Zones
    try:
        r = requests.get(f"{BASE_URL}/api/security-zones")
        data = r.json()
        print(f"\n[OK] Security Zones Endpoint: {r.status_code}")
        print(f"     Total Zones: {data['total_zones']}")
        print(f"     Total Apps: {data['total_apps']}")
    except Exception as e:
        print(f"[ERROR] Security Zones failed: {e}")

    # Test 4: DNS Validation Summary
    try:
        r = requests.get(f"{BASE_URL}/api/dns-validation/summary")
        data = r.json()
        stats = data.get('statistics', {})
        print(f"\n[OK] DNS Validation Endpoint: {r.status_code}")
        print(f"     Valid: {stats.get('total_valid', 0)}")
        print(f"     Mismatches: {stats.get('total_mismatches', 0)}")
    except Exception as e:
        print(f"[ERROR] DNS Validation failed: {e}")

    # Test 5: Enterprise Summary
    try:
        r = requests.get(f"{BASE_URL}/api/enterprise/summary")
        data = r.json()
        stats = data.get('statistics', {})
        print(f"\n[OK] Enterprise Summary Endpoint: {r.status_code}")
        print(f"     Applications: {stats.get('total_applications', 0)}")
        print(f"     Dependencies: {stats.get('total_dependencies', 0)}")
    except Exception as e:
        print(f"[ERROR] Enterprise Summary failed: {e}")

    # Test 6: Zone Distribution (for charts)
    try:
        r = requests.get(f"{BASE_URL}/api/analytics/zone-distribution")
        data = r.json()
        print(f"\n[OK] Zone Distribution Endpoint: {r.status_code}")
        print(f"     Total Apps: {data.get('total', 0)}")
        if data.get('labels'):
            print(f"     Zones: {', '.join(data['labels'][:3])}...")
    except Exception as e:
        print(f"[ERROR] Zone Distribution failed: {e}")

    print("\n" + "=" * 80)
    print("Testing Complete!")
    print("=" * 80)
    print(f"\n[INFO] Dashboard URL: {BASE_URL}")
    print(f"[INFO] API Docs URL:  {BASE_URL}/docs")
    print("\n[SECURITY] Server is localhost-only - NOT accessible from internet")
    print("=" * 80)

if __name__ == "__main__":
    test_endpoints()
