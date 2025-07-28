#!/usr/bin/env python3
"""
Check what's in the MongoDB database
"""

from db import get_db

def check_database():
    db = get_db()
    
    # Get all templates
    templates = list(db.templates.find())
    print(f"Total templates: {len(templates)}")
    
    print("\nAll templates:")
    for i, template in enumerate(templates, 1):
        name = template.get('name', 'No name')
        category = template.get('category', 'No category')
        metadata = template.get('metadata', {})
        metadata_category = metadata.get('category', 'No metadata category')
        
        print(f"{i}. {name}")
        print(f"   Direct category: {category}")
        print(f"   Metadata category: {metadata_category}")
        print()

if __name__ == "__main__":
    check_database() 