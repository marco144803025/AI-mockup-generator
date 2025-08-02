#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from tools.mongodb_tools import MongoDBTools

def test_login_search():
    try:
        mongodb_tools = MongoDBTools()
        
        print("=== TESTING LOGIN TEMPLATE SEARCH ===")
        
        # Test 1: Search for 'login' category
        print("\n1. Searching for 'login' category:")
        result = mongodb_tools.get_templates_by_category("login", limit=10)
        print(f"Result: {result}")
        
        # Test 2: Search for 'Login' category (capitalized)
        print("\n2. Searching for 'Login' category:")
        result2 = mongodb_tools.get_templates_by_category("Login", limit=10)
        print(f"Result: {result2}")
        
        # Test 3: Check what categories are available
        print("\n3. Available categories:")
        categories_result = mongodb_tools.get_available_categories()
        print(f"Categories result: {categories_result}")
        
        # Test 4: Direct database query
        print("\n4. Direct database query for login templates:")
        from db import get_db
        db = get_db()
        
        # Query for login templates in metadata.category
        login_templates = list(db.templates.find({
            "metadata.category": "login"
        }, {'name': 1, 'metadata.category': 1, '_id': 0}))
        print(f"Login templates in metadata.category: {len(login_templates)}")
        for template in login_templates:
            print(f"  - {template['name']} ({template['metadata']['category']})")
        
        # Query for login templates in direct category field
        login_templates_direct = list(db.templates.find({
            "category": "login"
        }, {'name': 1, 'category': 1, '_id': 0}))
        print(f"Login templates in direct category: {len(login_templates_direct)}")
        for template in login_templates_direct:
            print(f"  - {template['name']} ({template['category']})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_search() 