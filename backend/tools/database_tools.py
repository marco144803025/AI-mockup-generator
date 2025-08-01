"""
Database Tools - Functions for LLM to interact with MongoDB
"""

import logging
from typing import Dict, List, Any, Optional
from db import get_db

class DatabaseTools:
    """Tools for database operations that can be called by LLM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = get_db()
    
    def get_templates_by_category(self, category: str, limit: int = 10) -> Dict[str, Any]:
        """Get templates for a specific category"""
        try:
            # Normalize category name
            category_mapping = {
                'About': 'about',
                'sign-up': 'signup',
                'Sign-up': 'signup',
                'Signup': 'signup',
                'Login': 'login',
                'Profile': 'profile',
                'Landing': 'landing'
            }
            
            normalized_category = category_mapping.get(category, category.lower())
            
            # Find templates in this category
            possible_categories = [normalized_category]
            for original, normalized in category_mapping.items():
                if normalized == normalized_category:
                    possible_categories.append(original)
                elif original == category:
                    possible_categories.append(normalized)
            
            templates = list(self.db.templates.find({
                "$or": [
                    {"category": {"$in": possible_categories}},
                    {"metadata.category": {"$in": possible_categories}}
                ]
            }).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for template in templates:
                if '_id' in template:
                    template['_id'] = str(template['_id'])
            
            return {
                "success": True,
                "category": category,
                "count": len(templates),
                "templates": templates
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching templates for category {category}: {e}")
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "count": 0,
                "templates": []
            }
    
    def get_category_constraints(self, category: str) -> Dict[str, Any]:
        """Get category-specific constraints and available options"""
        try:
            # Get templates for this category
            templates_result = self.get_templates_by_category(category, limit=50)
            
            if not templates_result["success"]:
                return templates_result
            
            templates = templates_result["templates"]
            
            # Extract unique tags from all templates in this category
            all_tags = []
            for template in templates:
                tags = template.get('tags', [])
                if isinstance(tags, list):
                    all_tags.extend(tags)
            
            unique_tags = list(set(all_tags))
            
            # Categorize tags
            styles = []
            themes = []
            features = []
            layouts = []
            
            for tag in unique_tags:
                tag_lower = tag.lower()
                if any(style in tag_lower for style in ['modern', 'minimal', 'clean', 'professional', 'colorful']):
                    styles.append(tag)
                elif any(theme in tag_lower for theme in ['dark', 'light', 'theme']):
                    themes.append(tag)
                elif any(feature in tag_lower for feature in ['responsive', 'interactive', 'user-friendly', 'form', 'gallery']):
                    features.append(tag)
                elif any(layout in tag_lower for layout in ['card', 'grid', 'flexbox', 'hero']):
                    layouts.append(tag)
                else:
                    # Default to features if not categorized
                    features.append(tag)
            
            return {
                "success": True,
                "category": category,
                "templates_count": len(templates),
                "category_tags": unique_tags,
                "styles": styles,
                "themes": themes,
                "features": features,
                "layouts": layouts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting category constraints for {category}: {e}")
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "templates_count": 0,
                "category_tags": [],
                "styles": [],
                "themes": [],
                "features": [],
                "layouts": []
            }
    
    def search_templates(self, query: str, category: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Search templates by query and optional category filter"""
        try:
            # Build search query
            search_filter = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"tags": {"$in": [query]}}
                ]
            }
            
            # Add category filter if provided
            if category:
                category_mapping = {
                    'About': 'about',
                    'sign-up': 'signup',
                    'Sign-up': 'signup',
                    'Signup': 'signup',
                    'Login': 'login',
                    'Profile': 'profile',
                    'Landing': 'landing'
                }
                
                normalized_category = category_mapping.get(category, category.lower())
                possible_categories = [normalized_category]
                
                for original, normalized in category_mapping.items():
                    if normalized == normalized_category:
                        possible_categories.append(original)
                    elif original == category:
                        possible_categories.append(normalized)
                
                search_filter["$and"] = [{
                    "$or": [
                        {"category": {"$in": possible_categories}},
                        {"metadata.category": {"$in": possible_categories}}
                    ]
                }]
            
            templates = list(self.db.templates.find(search_filter).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for template in templates:
                if '_id' in template:
                    template['_id'] = str(template['_id'])
            
            return {
                "success": True,
                "query": query,
                "category": category,
                "count": len(templates),
                "templates": templates
            }
            
        except Exception as e:
            self.logger.error(f"Error searching templates: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "category": category,
                "count": 0,
                "templates": []
            }
    
    def get_template_by_id(self, template_id: str) -> Dict[str, Any]:
        """Get a specific template by ID"""
        try:
            from bson import ObjectId
            
            template = self.db.templates.find_one({"_id": ObjectId(template_id)})
            
            if template:
                # Convert ObjectId to string for JSON serialization
                template['_id'] = str(template['_id'])
                return {
                    "success": True,
                    "template": template
                }
            else:
                return {
                    "success": False,
                    "error": "Template not found",
                    "template_id": template_id
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching template {template_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "template_id": template_id
            }
    
    def get_available_categories(self) -> Dict[str, Any]:
        """Get all available template categories"""
        try:
            # Get distinct categories
            categories = self.db.templates.distinct("category")
            
            # Also check metadata.category
            metadata_categories = self.db.templates.distinct("metadata.category")
            
            # Combine and deduplicate
            all_categories = list(set(categories + metadata_categories))
            
            # Filter out None/empty values
            all_categories = [cat for cat in all_categories if cat]
            
            return {
                "success": True,
                "categories": all_categories,
                "count": len(all_categories)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching categories: {e}")
            return {
                "success": False,
                "error": str(e),
                "categories": [],
                "count": 0
            } 