#!/usr/bin/env python3
"""
Check database constraints for prompt engineering
"""

from db import get_db

def analyze_database_constraints():
    db = get_db()
    
    # Get all templates
    templates = list(db.templates.find())
    
    print(f"Total templates: {len(templates)}")
    
    # Analyze categories
    categories = db.templates.distinct('category')
    metadata_categories = db.templates.distinct('metadata.category')
    all_categories = list(set(categories + metadata_categories))
    all_categories = [cat for cat in all_categories if cat]
    
    print(f"\nAvailable categories: {all_categories}")
    
    # Analyze tags
    all_tags = []
    for template in templates:
        tags = template.get('tags', [])
        if tags:
            all_tags.extend(tags)
    
    unique_tags = list(set(all_tags))
    print(f"\nAvailable tags ({len(unique_tags)}): {unique_tags}")
    
    # Analyze by category
    print("\nTemplates by category:")
    for category in all_categories:
        # Check direct category field
        direct_count = db.templates.count_documents({'category': category})
        # Check metadata.category field
        metadata_count = db.templates.count_documents({'metadata.category': category})
        total = direct_count + metadata_count
        
        if total > 0:
            print(f"  {category}: {total} templates")
            
            # Get tags for this category
            category_tags = []
            for template in templates:
                template_category = template.get('category') or template.get('metadata', {}).get('category')
                if template_category == category:
                    tags = template.get('tags', [])
                    category_tags.extend(tags)
            
            unique_category_tags = list(set(category_tags))
            print(f"    Tags: {unique_category_tags[:10]}...")  # Show first 10 tags
    
    # Create constraint summary for prompt engineering
    print("\n" + "="*50)
    print("DATABASE CONSTRAINTS FOR PROMPT ENGINEERING")
    print("="*50)
    print(f"Available Categories: {', '.join(all_categories)}")
    print(f"Available Tags: {', '.join(unique_tags)}")
    
    return {
        'categories': all_categories,
        'tags': unique_tags,
        'templates': templates
    }

if __name__ == "__main__":
    analyze_database_constraints() 