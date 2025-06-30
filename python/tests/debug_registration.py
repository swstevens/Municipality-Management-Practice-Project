#!/usr/bin/env python3
"""
Debug script to test registration endpoint
Run this to see the exact validation error
"""

import requests
import json
import sys

def test_registration():
    """Test registration with different payloads to identify the issue"""
    
    API_BASE = "http://localhost:8000"
    
    # Test data variations
    test_cases = [
        {
            "name": "Valid data",
            "data": {
                "username": "testuser123",
                "email": "testuser123@waterutil.test",
                "password": "securepass123",
                "role": "operator"
            }
        },
        {
            "name": "Short password",
            "data": {
                "username": "testuser456",
                "email": "testuser456@waterutil.test", 
                "password": "short",
                "role": "operator"
            }
        },
        {
            "name": "Invalid email",
            "data": {
                "username": "testuser789",
                "email": "invalid-email",
                "password": "securepass123",
                "role": "operator"
            }
        },
        {
            "name": "Missing role",
            "data": {
                "username": "testuser000",
                "email": "testuser000@waterutil.test",
                "password": "securepass123"
                # role missing - should default to 'customer'
            }
        }
    ]
    
    print("🧪 Testing registration endpoint...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Data: {json.dumps(test_case['data'], indent=6)}")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/register",
                json=test_case['data'],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: User {result.get('username')} created with ID {result.get('id')}")
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Error: {json.dumps(error_data, indent=6)}")
                    
                    # Show detailed validation errors
                    if response.status_code == 422 and 'detail' in error_data:
                        print("   📋 Validation errors:")
                        if isinstance(error_data['detail'], list):
                            for error in error_data['detail']:
                                field = '.'.join(error.get('loc', ['unknown']))
                                message = error.get('msg', 'Unknown error')
                                print(f"      - {field}: {message}")
                        else:
                            print(f"      - {error_data['detail']}")
                            
                except json.JSONDecodeError:
                    print(f"   ❌ Error: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
            print("   Make sure FastAPI server is running: uvicorn main:app --reload")
            return False
    
    return True

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running")
        print("Start with: uvicorn main:app --reload")
        return False

def main():
    print("🌊 Water Utility Registration Debug Tool")
    print("=" * 50)
    
    if not test_server_health():
        sys.exit(1)
    
    print()
    if test_registration():
        print("\n🎉 Debug complete! Check the output above for any validation errors.")
    else:
        print("\n❌ Debug failed - check server connection.")

if __name__ == "__main__":
    main()