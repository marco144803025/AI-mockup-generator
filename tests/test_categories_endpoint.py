#!/usr/bin/env python3
"""
Test the categories endpoint
"""

import requests
import json

def test_categories_endpoint():
    """Test if the categories endpoint returns available categories"""
    try:
        response = requests.get("http://localhost:8000/api/templates/categories")
        if response.status_code == 200:
            data = response.json()
            print(f" Categories endpoint working!")
            print(f" Found {data.get('count', 0)} categories:")
            for category in data.get('categories', []):
                print(f"   - {category}")
            return True
        else:
            print(f" Categories endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f" Error testing categories endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Categories Endpoint...")
    success = test_categories_endpoint()
    print(f"\n{'✅ Test passed' if success else '❌ Test failed'}") 