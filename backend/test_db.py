#!/usr/bin/env python3
"""
Test MongoDB connection and categories
"""

from db import get_db

def test_database():
    try:
        db = get_db()
        print("MongoDB connection test:")
        print(f"Database: {db.name}")
        
        # Check templates count
        templates_count = db.templates.count_documents({})
        print(f"Templates count: {templates_count}")
        
        # Check categories
        categories = list(db.templates.distinct("category"))
        print(f"Categories: {categories}")
        
        # Check metadata categories
        metadata_categories = list(db.templates.distinct("metadata.category"))
        print(f"Metadata categories: {metadata_categories}")
        
        # Show all templates
        templates = list(db.templates.find())
        print(f"\nAll templates:")
        for i, template in enumerate(templates, 1):
            name = template.get('name', 'No name')
            category = template.get('category', 'No category')
            metadata = template.get('metadata', {})
            metadata_category = metadata.get('category', 'No metadata category')
            print(f"{i}. {name}")
            print(f"   Direct category: {category}")
            print(f"   Metadata category: {metadata_category}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_database() 