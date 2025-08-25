"""
Keyword Configuration - Legacy compatibility layer
This file now imports the new YAML-based KeywordManager for backward compatibility.
"""

# Import the new YAML-based keyword manager
from .keyword_manager import KeywordManager

# Create a global instance for backward compatibility
keyword_manager = KeywordManager()

# Legacy compatibility functions - these now delegate to the KeywordManager
def get_page_type_keywords():
    """Get page type keywords (legacy compatibility)"""
    return keyword_manager.get_page_type_keywords()

def get_related_categories():
    """Get related categories (legacy compatibility)"""
    return keyword_manager.get_related_categories()

def get_design_style_keywords():
    """Get design style keywords (legacy compatibility)"""
    return keyword_manager.get_design_style_keywords()

def get_component_keywords():
    """Get component keywords (legacy compatibility)"""
    return keyword_manager.get_component_keywords()

def get_feature_keywords():
    """Get feature keywords (legacy compatibility)"""
    return keyword_manager.get_feature_keywords()

def get_content_keywords():
    """Get content keywords (legacy compatibility)"""
    return keyword_manager.get_content_keywords()

def get_business_context_keywords():
    """Get business context keywords (legacy compatibility)"""
    return keyword_manager.get_business_context_keywords()

def get_technical_keywords():
    """Get technical keywords (legacy compatibility)"""
    return keyword_manager.get_technical_keywords()

def get_layout_keywords():
    """Get layout keywords (legacy compatibility)"""
    return keyword_manager.get_layout_keywords()

def get_color_keywords():
    """Get color keywords (legacy compatibility)"""
    return keyword_manager.get_color_keywords()

def get_focus_area_categories():
    """Get focus area categories (legacy compatibility)"""
    return keyword_manager.get_focus_area_categories()

def get_tag_categories():
    """Get tag categories (legacy compatibility)"""
    return keyword_manager.get_tag_categories()

def get_intent_keywords():
    """Get intent keywords (legacy compatibility)"""
    return keyword_manager.get_intent_keywords()

def get_template_selection_keywords():
    """Get template selection keywords (legacy compatibility)"""
    return keyword_manager.get_template_selection_keywords()

def get_default_values():
    """Get default values (legacy compatibility)"""
    return keyword_manager.get_default_values()

def get_required_fields():
    """Get required fields (legacy compatibility)"""
    return keyword_manager.get_required_fields()

def get_design_principles():
    """Get design principles (legacy compatibility)"""
    return keyword_manager.get_design_principles()

def get_quality_checks():
    """Get quality checks (legacy compatibility)"""
    return keyword_manager.get_quality_checks()

def get_validation_criteria():
    """Get validation criteria (legacy compatibility)"""
    return keyword_manager.get_validation_criteria()

# Legacy compatibility class - delegates to KeywordManager
class KeywordManager:
    """Legacy compatibility class that delegates to the new YAML-based KeywordManager"""
    
    def __init__(self):
        """Initialize with the new keyword manager"""
        self._manager = keyword_manager
    
    # Delegate all methods to the new manager
    def get_page_type_keywords(self):
        return self._manager.get_page_type_keywords()
    
    def get_related_categories(self):
        return self._manager.get_related_categories()
    
    def get_design_style_keywords(self):
        return self._manager.get_design_style_keywords()
    
    def get_component_keywords(self):
        return self._manager.get_component_keywords()
    
    def get_feature_keywords(self):
        return self._manager.get_feature_keywords()
    
    def get_content_keywords(self):
        return self._manager.get_content_keywords()
    
    def get_business_context_keywords(self):
        return self._manager.get_business_context_keywords()
    
    def get_technical_keywords(self):
        return self._manager.get_technical_keywords()
    
    def get_layout_keywords(self):
        return self._manager.get_layout_keywords()
    
    def get_color_keywords(self):
        return self._manager.get_color_keywords()
    
    def get_focus_area_categories(self):
        return self._manager.get_focus_area_categories()
    
    def get_tag_categories(self):
        return self._manager.get_tag_categories()
    
    def get_intent_keywords(self):
        return self._manager.get_intent_keywords()
    
    def get_template_selection_keywords(self):
        return self._manager.get_template_selection_keywords()
    
    def get_default_values(self):
        return self._manager.get_default_values()
    
    def get_required_fields(self):
        return self._manager.get_required_fields()
    
    def get_design_principles(self):
        return self._manager.get_design_principles()
    
    def get_quality_checks(self):
        return self._manager.get_quality_checks()
    
    def get_validation_criteria(self):
        return self._manager.get_validation_criteria()
    
    def categorize_focus_area(self, focus_area: str) -> str:
        return self._manager.categorize_focus_area(focus_area)
    
    def categorize_tag(self, tag: str) -> str:
        return self._manager.categorize_tag(tag)
    
    def detect_page_type(self, user_prompt: str) -> str:
        return self._manager.detect_page_type(user_prompt)
    
    def get_related_categories_for(self, category: str):
        return self._manager.get_related_categories_for(category)
    
    def generate_question_for_tag(self, tag: str, count: int, total: int) -> str:
        return self._manager.generate_question_for_tag(tag, count, total) 
