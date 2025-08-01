#!/usr/bin/env python3
"""
Simple Database Tag Extractor
Extracts all tags from the database collection for manual analysis.
"""

import sys
import os
import json
from collections import Counter

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing required packages. Please install: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

def extract_tags():
    """Extract all tags from the database"""
    
    # Connect to database
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DB_NAME', 'ui_templates')
    
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        print(f"✅ Connected to database: {db_name}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    # Get all templates
    try:
        templates = list(db.templates.find({}))
        print(f"📊 Found {len(templates)} templates in database")
    except Exception as e:
        print(f"❌ Error fetching templates: {e}")
        return
    
    # Extract all tags
    all_tags = []
    template_info = []
    
    for template in templates:
        template_id = template.get('_id', 'unknown')
        template_name = template.get('name', 'Unknown')
        template_category = template.get('category', 'unknown')
        tags = template.get('tags', [])
        
        # Handle different tag formats
        if isinstance(tags, list):
            template_tags = tags
        elif isinstance(tags, str):
            template_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        else:
            template_tags = []
        
        all_tags.extend(template_tags)
        
        template_info.append({
            "id": str(template_id),
            "name": template_name,
            "category": template_category,
            "tags": template_tags
        })
    
    # Count tag frequency
    tag_counter = Counter(all_tags)
    
    # Create simple report
    report = {
        "summary": {
            "total_templates": len(templates),
            "total_unique_tags": len(tag_counter),
            "total_tag_occurrences": len(all_tags)
        },
        "all_tags": list(tag_counter.keys()),
        "tag_frequency": dict(tag_counter.most_common()),
        "most_common_tags": tag_counter.most_common(20),
        "templates": template_info
    }
    
    # Save detailed report
    with open("database_tags_detailed.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Save simple tag list
    with open("database_tags_simple.txt", 'w', encoding='utf-8') as f:
        f.write("All unique tags from database:\n")
        f.write("=" * 40 + "\n\n")
        for tag in sorted(tag_counter.keys()):
            f.write(f"{tag}: {tag_counter[tag]} occurrences\n")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 TAG EXTRACTION SUMMARY")
    print("="*50)
    print(f"📁 Total Templates: {len(templates)}")
    print(f"🏷️  Total Unique Tags: {len(tag_counter)}")
    print(f"📈 Total Tag Occurrences: {len(all_tags)}")
    
    print(f"\n🏆 Top 10 Most Common Tags:")
    for tag, count in tag_counter.most_common(10):
        print(f"   • {tag}: {count} occurrences")
    
    print(f"\n📂 All Unique Tags ({len(tag_counter)} total):")
    for tag in sorted(tag_counter.keys()):
        print(f"   • {tag}")
    
    print("\n✅ Files saved:")
    print("   • database_tags_detailed.json - Complete analysis")
    print("   • database_tags_simple.txt - Simple tag list")
    print("="*50)

if __name__ == "__main__":
    extract_tags() 