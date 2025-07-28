#!/usr/bin/env python3
"""
Test script to verify categories endpoint
"""

import requests
import json

def test_categories_endpoint():
    """Test the categories endpoint"""
    
    try:
        print("Testing categories endpoint...")
        response = requests.get("http://localhost:8000/api/templates/categories")
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.ok:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if 'categories' in data:
                print(f"✅ Categories found: {data['categories']}")
                print(f"✅ Count: {data['count']}")
                return True
            else:
                print("❌ No 'categories' field in response")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_categories_endpoint()
    if success:
        print("\n🎉 Categories endpoint is working!")
    else:
        print("\n❌ Categories endpoint failed!") 