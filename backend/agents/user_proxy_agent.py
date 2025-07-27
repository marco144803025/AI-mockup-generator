from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json

class UserProxyAgent(BaseAgent):
    """User Proxy Agent that handles user interactions and workflow coordination"""
    
    def __init__(self):
        system_message = """You are a User Proxy Agent responsible for:
1. Understanding user requirements and confirming them
2. Coordinating the workflow between different phases
3. Managing user approvals and feedback
4. Ensuring smooth transitions between agents
5. Providing clear explanations for agent decisions

Always be conversational, helpful, and explain the reasoning behind recommendations.
Ask for user confirmation before proceeding with critical decisions."""
        
        super().__init__("UserProxy", system_message)
    
    def understand_requirements(self, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Phase 1: Understand user requirements and get confirmation"""
        
        prompt = f"""
        Analyze the user's requirements for a UI mockup:
        
        User Request: {user_prompt}
        
        Please provide a structured analysis including:
        1. Page Type: What type of page they want (landing, login, signup, profile, etc.)
        2. Style Preferences: Any style mentions (modern, minimal, colorful, etc.)
        3. Key Features: What functionality they need
        4. Target Audience: Who the page is for
        5. Brand Elements: Any brand-specific requirements
        
        Format your response as JSON with these fields:
        {{
            "page_type": "string",
            "style_preferences": ["list", "of", "styles"],
            "key_features": ["list", "of", "features"],
            "target_audience": "string",
            "brand_elements": ["list", "of", "elements"],
            "confidence_score": 0.85,
            "questions_for_clarification": ["list", "of", "questions"]
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