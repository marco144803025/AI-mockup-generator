#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from db import get_db

def check_templates():
    try:
        db = get_db()
        
        print("=== DATABASE TEMPLATE CHECK ===")
        
        # Get all categories
        categories = db.templates.distinct('category')
        print(f"Available categories: {categories}")
        
        # Check for login templates specifically
        login_templates = list(db.templates.find({'category': 'login'}, {'name': 1, 'category': 1, '_id': 0}))
        print(f"Login templates (category='login'): {len(login_templates)}")
        for template in login_templates:
            print(f"  - {template['name']} ({template['category']})")
        
        # Check all templates and their categories
        all_templates = list(db.templates.find({}, {'name': 1, 'category': 1, 'metadata': 1, '_id': 0}))
        print(f"\nAll templates ({len(all_templates)} total):")
        for template in all_templates:
            name = template.get('name', 'Unknown')
            category = template.get('category', 'No category')
            metadata_category = template.get('metadata', {}).get('category', 'No metadata category')
            print(f"  - {name}: category='{category}', metadata.category='{metadata_category}'")
        
        # Check for any templates that might be login-related
        login_related = list(db.templates.find({
            '$or': [
                {'category': 'login'},
                {'name': {'$regex': 'login', '$options': 'i'}},
                {'metadata.category': 'login'},
                {'description': {'$regex': 'login', '$options': 'i'}}
            ]
        }, {'name': 1, 'category': 1, 'metadata': 1, '_id': 0}))
        
        print(f"\nLogin-related templates (any field): {len(login_related)}")
        for template in login_related:
            print(f"  - {template['name']} ({template.get('category', 'No category')})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_templates() 