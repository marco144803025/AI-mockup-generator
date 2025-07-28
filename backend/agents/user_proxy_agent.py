from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json

class UserProxyAgent(BaseAgent):
    """User Proxy Agent that handles user interactions and workflow coordination"""
    
    def __init__(self):
        # Get database constraints for prompt engineering
        db = self.get_db()
        categories = db.templates.distinct('category')
        metadata_categories = db.templates.distinct('metadata.category')
        all_categories = list(set(categories + metadata_categories))
        all_categories = [cat for cat in all_categories if cat]
        
        # Get available tags
        all_tags = []
        templates = list(db.templates.find())
        for template in templates:
            tags = template.get('tags', [])
            if tags:
                all_tags.extend(tags)
        unique_tags = list(set(all_tags))
        
        system_message = f"""You are a User Proxy Agent responsible for:
1. Understanding user requirements and confirming them
2. Coordinating the workflow between different phases
3. Managing user approvals and feedback
4. Ensuring smooth transitions between agents
5. Providing clear explanations for agent decisions

DATABASE CONSTRAINTS - You can ONLY work with these available options:
- Available Categories: {', '.join(all_categories)}
- Available Design Tags: {', '.join(unique_tags[:50])}... (and {len(unique_tags)-50} more)

IMPORTANT RULES:
1. Only ask questions about categories and design elements that exist in the database
2. If user requests something not available, suggest alternatives from the available options
3. Always be conversational, helpful, and explain the reasoning behind recommendations
4. Ask for user confirmation before proceeding with critical decisions
5. Guide users toward the available design options in your database"""
        
        super().__init__("UserProxy", system_message)
    
    def understand_requirements(self, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Phase 1: Understand user requirements and get confirmation"""
        
        # Get database constraints
        db = self.get_db()
        categories = db.templates.distinct('category')
        metadata_categories = db.templates.distinct('metadata.category')
        all_categories = list(set(categories + metadata_categories))
        all_categories = [cat for cat in all_categories if cat]
        
        # Get available tags
        all_tags = []
        templates = list(db.templates.find())
        for template in templates:
            tags = template.get('tags', [])
            if tags:
                all_tags.extend(tags)
        unique_tags = list(set(all_tags))
        
        prompt = f"""
        Analyze the user's requirements for a UI mockup:
        
        User Request: {user_prompt}
        
        DATABASE CONSTRAINTS - You can ONLY work with these available options:
        - Available Categories: {', '.join(all_categories)}
        - Available Design Tags: {', '.join(unique_tags[:30])}... (and {len(unique_tags)-30} more)
        
        Please provide a structured analysis including:
        1. Page Type: What type of page they want (MUST be one of: {', '.join(all_categories)})
        2. Style Preferences: Any style mentions (MUST be from available tags)
        3. Key Features: What functionality they need (MUST be from available tags)
        4. Target Audience: Who the page is for
        5. Brand Elements: Any brand-specific requirements (MUST be from available tags)
        
        IMPORTANT: Only suggest categories and design elements that exist in the database.
        If the user requests something not available, suggest the closest alternative from the available options.
        
        Format your response as JSON with these fields:
        {{
            "page_type": "string (must be from available categories)",
            "style_preferences": ["list", "of", "available", "tags"],
            "key_features": ["list", "of", "available", "features"],
            "target_audience": "string",
            "brand_elements": ["list", "of", "available", "elements"],
            "confidence_score": 0.85,
            "questions_for_clarification": ["list", "of", "questions", "within", "database", "constraints"]
        }}
        """
        
        if logo_image:
            prompt += f"\n\nA logo image has been provided. Please analyze it for brand colors, style, and design elements."
        
        response = self.call_claude(prompt, logo_image)
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return {
                    "page_type": "landing",
                    "style_preferences": ["modern"],
                    "key_features": ["responsive"],
                    "target_audience": "general",
                    "brand_elements": [],
                    "confidence_score": 0.5,
                    "questions_for_clarification": ["Could you provide more details about your specific needs?"]
                }
        except json.JSONDecodeError:
            return {
                "page_type": "landing",
                "style_preferences": ["modern"],
                "key_features": ["responsive"],
                "target_audience": "general",
                "brand_elements": [],
                "confidence_score": 0.5,
                "questions_for_clarification": ["Could you provide more details about your specific needs?"]
            }
    
    def confirm_requirements(self, requirements: Dict[str, Any]) -> str:
        """Ask user to confirm the understood requirements"""
        
        confirmation_prompt = f"""
        Based on your request, I understand you want:
        
        **Page Type**: {requirements.get('page_type', 'Not specified')}
        **Style**: {', '.join(requirements.get('style_preferences', ['Not specified']))}
        **Key Features**: {', '.join(requirements.get('key_features', ['Not specified']))}
        **Target Audience**: {requirements.get('target_audience', 'Not specified')}
        
        Confidence Score: {requirements.get('confidence_score', 0) * 100}%
        
        Questions for clarification:
        {chr(10).join(f"- {q}" for q in requirements.get('questions_for_clarification', []))}
        
        Please confirm if this understanding is correct, or let me know what needs to be adjusted.
        """
        
        return confirmation_prompt
    
    def confirm_template_selection(self, template_info: Dict[str, Any], reasoning: str) -> str:
        """Ask user to confirm template selection"""
        
        confirmation_prompt = f"""
        I've selected a UI template for you:
        
        **Template**: {template_info.get('title', 'Unknown')}
        **Category**: {template_info.get('category', 'Unknown')}
        **Description**: {template_info.get('description', 'No description available')}
        
        **Reasoning for Selection**:
        {reasoning}
        
        Would you like me to proceed with this template, or would you prefer to see other options?
        """
        
        return confirmation_prompt
    
    def confirm_master_style(self, template_info: Dict[str, Any]) -> str:
        """Confirm the selected template as master style for the whole site"""
        
        confirmation_prompt = f"""
        Great! The selected template will serve as the 'master style' for your entire website.
        
        **Master Style Template**: {template_info.get('title', 'Unknown')}
        
        This means all additional pages (about, contact, pricing, etc.) will maintain the same:
        - Color scheme
        - Typography
        - Layout patterns
        - Visual elements
        - Overall design language
        
        This ensures a cohesive and professional look across your entire site.
        
        Shall we proceed to create additional pages using this master style?
        """
        
        return confirmation_prompt
    
    def get_additional_pages_suggestions(self, page_type: str) -> List[str]:
        """Suggest common additional pages based on the first page type"""
        
        suggestions = {
            "landing": ["about", "contact", "pricing", "features", "testimonials"],
            "login": ["signup", "forgot-password", "dashboard", "profile"],
            "signup": ["login", "verification", "welcome", "onboarding"],
            "profile": ["dashboard", "settings", "portfolio", "achievements"],
            "dashboard": ["profile", "settings", "analytics", "reports"]
        }
        
        return suggestions.get(page_type, ["about", "contact"])
    
    def confirm_functionality_requirements(self, interactive_elements: List[str]) -> str:
        """Ask user about functionality requirements for interactive elements"""
        
        confirmation_prompt = f"""
        I've identified these interactive elements in your site:
        
        {chr(10).join(f"- {element}" for element in interactive_elements)}
        
        To make these functional, I need to know:
        
        1. **Forms**: What data should be collected? Where should it be sent?
        2. **Buttons**: What should happen when clicked?
        3. **Navigation**: Any special routing requirements?
        4. **Authentication**: Any login/signup requirements?
        
        Please provide details for each element you want to make functional.
        """
        
        return confirmation_prompt 
    
    def get_database_constraints(self) -> Dict[str, Any]:
        """Get current database constraints for prompt engineering"""
        db = self.get_db()
        
        # Get categories
        categories = db.templates.distinct('category')
        metadata_categories = db.templates.distinct('metadata.category')
        all_categories = list(set(categories + metadata_categories))
        all_categories = [cat for cat in all_categories if cat]
        
        # Get tags
        all_tags = []
        templates = list(db.templates.find())
        for template in templates:
            tags = template.get('tags', [])
            if tags:
                all_tags.extend(tags)
        unique_tags = list(set(all_tags))
        
        return {
            'categories': all_categories,
            'tags': unique_tags,
            'templates_count': len(templates)
        }
    
    def ask_constrained_questions(self, category: str) -> List[str]:
        """Generate questions based on database constraints for a specific category"""
        db = self.get_db()
        
        # Get templates for this category
        category_templates = []
        for template in db.templates.find():
            template_category = template.get('category') or template.get('metadata', {}).get('category')
            if template_category == category:
                category_templates.append(template)
        
        # Get unique tags for this category
        category_tags = []
        for template in category_templates:
            tags = template.get('tags', [])
            category_tags.extend(tags)
        unique_category_tags = list(set(category_tags))
        
        # Categorize tags for better questions
        styles = []
        themes = []
        features = []
        
        for tag in unique_category_tags:
            tag_lower = tag.lower()
            if any(style in tag_lower for style in ['modern', 'minimal', 'clean', 'sleek', 'elegant', 'professional', 'playful', 'colorful', 'bold', 'soft', 'natural', 'futuristic']):
                styles.append(tag)
            elif any(theme in tag_lower for theme in ['dark', 'light', 'theme', 'aesthetic']):
                themes.append(tag)
            elif any(feature in tag_lower for feature in ['form', 'authentication', 'dashboard', 'gallery', 'portfolio', 'analytics', 'social', 'login', 'signup', 'profile', 'navigation', 'hero', 'call-to-action']):
                features.append(tag)
        
        questions = []
        
        # Style questions
        if styles:
            questions.append(f"What style do you prefer for your {category} page? Available styles: {', '.join(styles[:5])}...")
        
        # Theme questions
        if themes:
            questions.append(f"What theme would you like? Available themes: {', '.join(themes)}")
        
        # Feature questions
        if features:
            questions.append(f"What key features are most important for your {category} page? Available features: {', '.join(features[:5])}...")
        
        # General questions
        questions.extend([
            f"Who is your target audience for this {category} page?",
            f"Any specific color preferences for your {category} page?"
        ])
        
        return questions[:5]  # Limit to 5 questions 