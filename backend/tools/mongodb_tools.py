"""
MongoDB Tools - Functions for agents to interact with MongoDB database
"""

import logging
from typing import Dict, List, Any, Optional
from db import get_db

class MongoDBTools:
    """MongoDB tool functions that can be called by agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = get_db()
    
    def get_templates_by_category(self, category: str, limit: int = 10) -> Dict[str, Any]:
        """Get templates filtered by category with metadata and tags"""
        try:
            # Normalize category name
            category_mapping = {
                'About': 'about',
                'sign-up': 'signup',
                'Sign-up': 'signup',
                'Signup': 'signup',
                'Login': 'login',
                'Profile': 'profile',
                'Landing': 'landing',
                'Portfolio': 'portfolio'
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
            
            if not templates:
                return {
                    "success": True,
                    "category": category,
                    "templates": [],
                    "count": 0,
                    "message": f"No templates found for category '{category}'. Available categories: {self._get_available_categories()}"
                }
            
            # Extract specific fields for agent analysis
            extracted_templates = []
            for template in templates:
                extracted_template = {
                    "template_id": str(template.get('_id', '')),
                    "name": template.get('name', 'Unknown'),
                    "category": template.get('metadata', {}).get('category', template.get('category', 'unknown')),
                    "description": template.get('metadata', {}).get('description', ''),
                    "tags": template.get('tags', []),
                    "figma_url": template.get('metadata', {}).get('figma_url', '')
                }
                extracted_templates.append(extracted_template)
            
            return {
                "success": True,
                "category": category,
                "templates": extracted_templates,
                "count": len(extracted_templates)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching templates for category {category}: {e}")
            return {
                "success": False,
                "error": f"Database connection failed. Please try again later.",
                "agent_response": "I'm having trouble accessing the database right now. Could you please try again in a few moments?"
            }
    
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get specific template's metadata and tags"""
        try:
            from bson import ObjectId
            
            template = self.db.templates.find_one({"_id": ObjectId(template_id)})
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template with ID '{template_id}' not found",
                    "agent_response": f"I couldn't find the template you're referring to. Please check the template ID and try again."
                }
            
            # Extract specific fields
            extracted_template = {
                "template_id": str(template.get('_id', '')),
                "name": template.get('name', 'Unknown'),
                "category": template.get('metadata', {}).get('category', template.get('category', 'unknown')),
                "description": template.get('metadata', {}).get('description', ''),
                "tags": template.get('tags', []),
                "figma_url": template.get('metadata', {}).get('figma_url', ''),
                "html_export": template.get('html_export', ''),
                "globals_css": template.get('globals_css', ''),
                "style_css": template.get('style_css', '')
            }
            
            return {
                "success": True,
                "template": extracted_template
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching template metadata for {template_id}: {e}")
            return {
                "success": False,
                "error": f"Database connection failed. Please try again later.",
                "agent_response": "I'm having trouble accessing the database right now. Could you please try again in a few moments?"
            }
    
    def search_templates_by_tags(self, tags: List[str], category: str = None, limit: int = 10) -> Dict[str, Any]:
        """Search templates by tags with optional category filter"""
        try:
            # Build search query
            search_filter = {"tags": {"$in": tags}}
            
            # Add category filter if provided
            if category:
                category_mapping = {
                    'About': 'about',
                    'sign-up': 'signup',
                    'Sign-up': 'signup',
                    'Signup': 'signup',
                    'Login': 'login',
                    'Profile': 'profile',
                    'Landing': 'landing',
                    'Portfolio': 'portfolio'
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
            
            if not templates:
                return {
                    "success": True,
                    "tags": tags,
                    "category": category,
                    "templates": [],
                    "count": 0,
                    "message": f"No templates found with tags {tags} for category '{category}'"
                }
            
            # Extract specific fields
            extracted_templates = []
            for template in templates:
                extracted_template = {
                    "template_id": str(template.get('_id', '')),
                    "name": template.get('name', 'Unknown'),
                    "category": template.get('metadata', {}).get('category', template.get('category', 'unknown')),
                    "description": template.get('metadata', {}).get('description', ''),
                    "tags": template.get('tags', []),
                    "figma_url": template.get('metadata', {}).get('figma_url', '')
                }
                extracted_templates.append(extracted_template)
            
            return {
                "success": True,
                "tags": tags,
                "category": category,
                "templates": extracted_templates,
                "count": len(extracted_templates)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching templates by tags {tags}: {e}")
            return {
                "success": False,
                "error": f"Database connection failed. Please try again later.",
                "agent_response": "I'm having trouble accessing the database right now. Could you please try again in a few moments?"
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
                "error": f"Database connection failed. Please try again later.",
                "agent_response": "I'm having trouble accessing the database right now. Could you please try again in a few moments."
            }
    
    def _get_available_categories(self) -> List[str]:
        """Helper method to get available categories as a list"""
        try:
            categories = self.db.templates.distinct("category")
            metadata_categories = self.db.templates.distinct("metadata.category")
            all_categories = list(set(categories + metadata_categories))
            return [cat for cat in all_categories if cat]
        except:
            return ["landing", "login", "signup", "profile", "about"] 