#!/usr/bin/env python3
"""
Debug script to test categories endpoint
"""

import requests
import json

def test_categories():
    """Test the categories endpoint"""
    try:
        print("Testing categories endpoint...")
        response = requests.get("http://localhost:8000/api/templates/categories", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Success!")
            print(f"Categories: {data.get('categories', [])}")
            print(f"Count: {data.get('count', 0)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Error text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout error - server not responding")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_health():
    """Test the health endpoint"""
    try:
        print("\nTesting health endpoint...")
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        
        print(f"Health Status Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check exception: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Categories Endpoint...")
    
    health_ok = test_health()
    if health_ok:
        test_categories()
    else:
        print("❌ Server health check failed - check if backend is running") 