"""
Keyword Manager - Utility class for managing keywords from YAML configuration
This class loads keyword data from YAML and provides methods for categorization and analysis.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path

class KeywordManager:
    """Utility class for managing keywords from YAML configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the keyword manager with YAML configuration"""
        if config_path is None:
            # Default to keywords.yaml in the same directory
            current_dir = Path(__file__).parent
            config_path = current_dir / "keywords.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
            
            if not self._config_data:
                raise ValueError("Configuration file is empty or invalid")
                
        except Exception as e:
            print(f"Error loading keyword configuration: {e}")
            # Fallback to minimal configuration
            self._config_data = self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if YAML loading fails"""
        return {
            "page_type_keywords": {
                "landing": ["landing", "homepage"],
                "login": ["login", "signin"],
                "signup": ["signup", "register"]
            },
            "default_values": {
                "max_templates": 5,
                "fallback_category": "landing"
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get the entire configuration data"""
        return self._config_data
    
    def get_page_type_keywords(self) -> Dict[str, List[str]]:
        """Get all page type detection keywords"""
        return self._config_data.get("page_type_keywords", {})
    
    def get_related_categories(self) -> Dict[str, List[str]]:
        """Get related categories mapping"""
        return self._config_data.get("related_categories", {})
    
    def get_design_style_keywords(self) -> Dict[str, List[str]]:
        """Get design style keywords"""
        return self._config_data.get("design_style_keywords", {})
    
    def get_component_keywords(self) -> Dict[str, List[str]]:
        """Get component keywords"""
        return self._config_data.get("component_keywords", {})
    
    def get_feature_keywords(self) -> Dict[str, List[str]]:
        """Get feature keywords"""
        return self._config_data.get("feature_keywords", {})
    
    def get_content_keywords(self) -> Dict[str, List[str]]:
        """Get content keywords"""
        return self._config_data.get("content_keywords", {})
    
    def get_business_context_keywords(self) -> Dict[str, List[str]]:
        """Get business context keywords"""
        return self._config_data.get("business_context_keywords", {})
    
    def get_technical_keywords(self) -> Dict[str, List[str]]:
        """Get technical keywords"""
        return self._config_data.get("technical_keywords", {})
    
    def get_layout_keywords(self) -> Dict[str, List[str]]:
        """Get layout keywords"""
        return self._config_data.get("layout_keywords", {})
    
    def get_color_keywords(self) -> Dict[str, List[str]]:
        """Get color keywords"""
        return self._config_data.get("color_keywords", {})
    
    def get_focus_area_categories(self) -> Dict[str, List[str]]:
        """Get focus area categories"""
        return self._config_data.get("focus_area_categories", {})
    
    def get_tag_categories(self) -> Dict[str, List[str]]:
        """Get tag categories"""
        return self._config_data.get("tag_categories", {})
    
    def get_intent_keywords(self) -> Dict[str, List[str]]:
        """Get intent detection keywords"""
        return self._config_data.get("intent_keywords", {})
    
    def get_template_selection_keywords(self) -> Dict[str, List[str]]:
        """Get template selection keywords"""
        return self._config_data.get("template_selection_keywords", {})
    
    def get_default_values(self) -> Dict[str, Any]:
        """Get default values"""
        return self._config_data.get("default_values", {})
    
    def get_required_fields(self) -> Dict[str, List[str]]:
        """Get required fields for different operations"""
        return self._config_data.get("required_fields", {})
    
    def get_design_principles(self) -> List[str]:
        """Get design principles"""
        return self._config_data.get("design_principles", [])
    
    def get_quality_checks(self) -> List[str]:
        """Get quality checks"""
        return self._config_data.get("quality_checks", [])
    
    def get_validation_criteria(self) -> List[str]:
        """Get validation criteria"""
        return self._config_data.get("validation_criteria", [])
    
    def categorize_focus_area(self, focus_area: str) -> str:
        """Categorize focus areas using loaded keywords"""
        focus_lower = focus_area.lower()
        
        focus_categories = self.get_focus_area_categories()
        for category, keywords in focus_categories.items():
            if any(keyword in focus_lower for keyword in keywords):
                return category
        
        return "general"
    
    def categorize_tag(self, tag: str) -> str:
        """Categorize tags using loaded keywords"""
        tag_lower = tag.lower()
        
        tag_categories = self.get_tag_categories()
        for category, keywords in tag_categories.items():
            if any(keyword in tag_lower for keyword in keywords):
                return category
        
        return "general"
    
    def detect_page_type(self, user_prompt: str) -> str:
        """Detect page type using loaded keywords"""
        prompt_lower = user_prompt.lower()
        
        page_type_keywords = self.get_page_type_keywords()
        for page_type, keywords in page_type_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return page_type
        
        # Default fallback
        default_values = self.get_default_values()
        return default_values.get("fallback_category", "landing")
    
    def get_related_categories_for(self, category: str) -> List[str]:
        """Get related categories for a given category"""
        related_categories = self.get_related_categories()
        return related_categories.get(category, [])
    
    def generate_question_for_tag(self, tag: str, count: int, total: int) -> str:
        """Generate a natural question based on the tag using loaded keywords"""
        tag_lower = tag.lower()
        
        # Style-related questions
        modern_styles = self.get_design_style_keywords().get("modern_styles", [])
        if any(style in tag_lower for style in modern_styles):
            return f"Would you prefer a {tag} design style?"
        
        # Component-related questions
        ui_components = self.get_component_keywords().get("ui_components", [])
        if any(comp in tag_lower for comp in ui_components):
            return f"How important is having a prominent {tag} section?"
        
        # Feature-related questions
        responsive_features = self.get_feature_keywords().get("responsive_features", [])
        if any(feature in tag_lower for feature in responsive_features):
            return f"Do you need {tag} compatibility?"
        
        # Content-related questions
        content_types = self.get_content_keywords().get("content_types", [])
        if any(content in tag_lower for content in content_types):
            return f"Would you like to focus on {tag}-heavy content?"
        
        # Business-related questions
        business_styles = self.get_business_context_keywords().get("business_styles", [])
        if any(business in tag_lower for business in business_styles):
            return f"Is this for a {tag} context?"
        
        # Default question
        return f"Are you looking for templates with {tag} features?"
    
    def reload_config(self):
        """Reload configuration from file (useful for hot reloading)"""
        self._load_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate the loaded configuration"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Check required sections
            required_sections = [
                "page_type_keywords",
                "design_style_keywords", 
                "component_keywords",
                "default_values"
            ]
            
            for section in required_sections:
                if section not in self._config_data:
                    validation_result["errors"].append(f"Missing required section: {section}")
                    validation_result["is_valid"] = False
            
            # Count keywords
            total_keywords = 0
            for section_name, section_data in self._config_data.items():
                if isinstance(section_data, dict):
                    section_count = sum(len(keywords) for keywords in section_data.values() if isinstance(keywords, list))
                    total_keywords += section_count
                elif isinstance(section_data, list):
                    total_keywords += len(section_data)
            
            validation_result["stats"]["total_keywords"] = total_keywords
            validation_result["stats"]["total_sections"] = len(self._config_data)
            
            if total_keywords < 10:
                validation_result["warnings"].append("Very few keywords found - consider expanding vocabulary")
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {e}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    def get_keyword_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded keywords"""
        stats = {
            "total_sections": len(self._config_data),
            "section_counts": {},
            "total_keywords": 0
        }
        
        for section_name, section_data in self._config_data.items():
            if isinstance(section_data, dict):
                section_count = sum(len(keywords) for keywords in section_data.values() if isinstance(keywords, list))
                stats["section_counts"][section_name] = section_count
                stats["total_keywords"] += section_count
            elif isinstance(section_data, list):
                stats["section_counts"][section_name] = len(section_data)
                stats["total_keywords"] += len(section_data)
        
        return stats 