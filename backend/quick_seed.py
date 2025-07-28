#!/usr/bin/env python3
"""
Quick script to seed database with sample templates
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from db import get_db

load_dotenv()

def quick_seed():
    """Quick seed with a few templates"""
    
    db = get_db()
    
    # Sample templates
    templates = [
        {
            "name": "Modern SaaS Landing",
            "category": "landing",
            "tags": ["modern", "saas", "clean"],
            "description": "Modern SaaS landing page",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Creative Portfolio",
            "category": "portfolio", 
            "tags": ["creative", "portfolio", "artistic"],
            "description": "Creative portfolio template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Corporate Business",
            "category": "corporate",
            "tags": ["corporate", "business", "professional"],
            "description": "Corporate business website",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "E-commerce Store",
            "category": "ecommerce",
            "tags": ["ecommerce", "shopping", "store"],
            "description": "E-commerce website template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    try:
        # Insert templates
        result = db.templates.insert_many(templates)
        print(f"✅ Added {len(result.inserted_ids)} templates")
        
        # Verify
        count = db.templates.count_documents({})
        categories = db.templates.distinct("category")
        print(f"📊 Total templates: {count}")
        print(f"📂 Categories: {categories}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🌱 Quick seeding...")
    success = quick_seed()
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed!") 