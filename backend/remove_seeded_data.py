#!/usr/bin/env python3
"""
Remove the seeded data from the database
"""

from db import get_db

def remove_seeded_data():
    db = get_db()
    
    # Names of the seeded templates
    seeded_names = [
        "Modern SaaS Landing",
        "Creative Portfolio", 
        "Corporate Business",
        "E-commerce Store"
    ]
    
    print("Removing seeded templates:")
    for name in seeded_names:
        result = db.templates.delete_one({"name": name})
        if result.deleted_count > 0:
            print(f"✅ Removed: {name}")
        else:
            print(f"❌ Not found: {name}")
    
    # Check remaining templates
    remaining = db.templates.count_documents({})
    print(f"\nRemaining templates: {remaining}")
    
    # Show remaining categories
    direct_categories = db.templates.distinct('category')
    metadata_categories = db.templates.distinct('metadata.category')
    all_categories = list(set(direct_categories + metadata_categories))
    all_categories = [cat for cat in all_categories if cat]
    
    print(f"Remaining categories: {all_categories}")

if __name__ == "__main__":
    remove_seeded_data() 