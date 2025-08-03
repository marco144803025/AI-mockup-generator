#!/usr/bin/env python3
"""
Simple script to seed database with sample templates
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Set environment variables directly
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGO_DB_NAME'] = 'ui_templates'

from pymongo import MongoClient

def simple_seed():
    """Simple seed with categories"""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['ui_templates']
    
    # Sample templates with categories
    templates = [
        {
            "name": "Modern Landing Page",
            "category": "landing",
            "tags": ["modern", "clean", "hero section", "call-to-action"],
            "description": "Modern landing page template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Login Form",
            "category": "login",
            "tags": ["login", "form", "authentication", "user-friendly"],
            "description": "Clean login form template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Sign Up Form",
            "category": "signup",
            "tags": ["signup", "registration", "form", "social authentication"],
            "description": "User registration form template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "User Profile",
            "category": "profile",
            "tags": ["profile", "user", "dashboard", "personal"],
            "description": "User profile page template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "About Me Page",
            "category": "about",
            "tags": ["about", "personal", "bio", "information"],
            "description": "About me page template",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

    ]
    
    try:
        # Clear existing templates
        db.templates.delete_many({})
        
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
    print("🌱 Simple seeding...")
    success = simple_seed()
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed!") 