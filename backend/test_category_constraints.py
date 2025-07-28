#!/usr/bin/env python3
"""
Test the category constraints endpoint
"""

import requests

def test_category_constraints():
    """Test the category constraints endpoint"""
    try:
        # Test with login category
        response = requests.get('http://localhost:8000/api/templates/category-constraints/login')
        print(f"Status Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"Category: {data.get('category')}")
            print(f"Templates Count: {data.get('templates_count')}")
            print(f"Styles: {data.get('styles', [])}")
            print(f"Themes: {data.get('themes', [])}")
            print(f"Features: {data.get('features', [])}")
            print(f"Layouts: {data.get('layouts', [])}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_category_constraints() 