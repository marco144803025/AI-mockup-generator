from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json

class RequirementUnderstandingAgent(BaseAgent):
    """Agent that understands internal user needs and wants from prompts and logos"""
    
    def __init__(self):
        system_message = """You are a Requirement Understanding Agent specialized in:
1. Analyzing user prompts to extract UI requirements
2. Analyzing logos and brand elements to understand design preferences
3. Converting vague requirements into structured UI specifications
4. Identifying implicit needs based on context and industry standards
5. Providing detailed UI feature recommendations

Always provide structured, actionable outputs that can be used by UI agents."""
        
        super().__init__("RequirementUnderstanding", system_message)
    
    def analyze_requirements(self, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Analyze user requirements and logo to extract UI specifications"""
        
        prompt = f"""
        Analyze the following user requirements and extract detailed UI specifications:
        
        USER PROMPT: {user_prompt}
        
        Please provide a comprehensive analysis in JSON format with the following structure:
        {{
            "ui_specifications": {{
                "layout_type": "string (e.g., single-column, multi-column, grid, hero-section)",
                "color_scheme": {{
                    "primary_colors": ["list", "of", "colors"],
                    "secondary_colors": ["list", "of", "colors"],
                    "accent_colors": ["list", "of", "colors"],
                    "background_style": "string (e.g., solid, gradient, image, glassmorphism)"
                }},
                "typography": {{
                    "font_family": "string (e.g., sans-serif, serif, modern)",
                    "font_weights": ["list", "of", "weights"],
                    "text_style": "string (e.g., clean, bold, elegant, playful)"
                }},
                "components": {{
                    "required_elements": ["list", "of", "required", "components"],
                    "optional_elements": ["list", "of", "optional", "components"],
                    "interactive_elements": ["list", "of", "interactive", "elements"]
                }},
                "style_preferences": {{
                    "overall_style": "string (e.g., modern, minimal, corporate, creative)",
                    "visual_elements": ["list", "of", "visual", "elements"],
                    "animations": "string (e.g., subtle, none, prominent)",
                    "spacing": "string (e.g., compact, spacious, balanced)"
                }}
            }},
            "brand_analysis": {{
                "brand_personality": "string",
                "target_audience": "string",
                "industry_context": "string",
                "brand_colors": ["list", "of", "brand", "colors"],
                "design_elements": ["list", "of", "design", "elements"]
            }},
            "technical_requirements": {{
                "responsive_design": "boolean",
                "accessibility": "boolean",
                "performance_requirements": "string",
                "browser_compatibility": ["list", "of", "browsers"]
            }},
            "content_structure": {{
                "sections": ["list", "of", "required", "sections"],
                "navigation": "string (e.g., header, footer, sidebar)",
                "call_to_actions": ["list", "of", "cta", "types"],
                "information_architecture": "string"
            }}
        }}
        
        Be specific and detailed in your analysis. Consider industry best practices and user experience principles.
        """
        
        if logo_image:
            prompt += f"""
            
            LOGO ANALYSIS:
            A logo image has been provided. Please analyze it for:
            - Brand colors and color palette
            - Design style and aesthetic
            - Typography used in the logo
            - Visual elements and symbols
            - Overall brand personality conveyed
            
            Incorporate these findings into the brand_analysis section.
            """
        
        response = self.call_claude(prompt, logo_image)
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback response
                return self._get_default_specifications()
        except json.JSONDecodeError:
            return self._get_default_specifications()
    
    def _get_default_specifications(self) -> Dict[str, Any]:
        """Return default UI specifications when analysis fails"""
        return {
            "ui_specifications": {
                "layout_type": "single-column",
                "color_scheme": {
                    "primary_colors": ["#3B82F6", "#1F2937"],
                    "secondary_colors": ["#6B7280", "#F3F4F6"],
                    "accent_colors": ["#10B981"],
                    "background_style": "solid"
                },
                "typography": {
                    "font_family": "sans-serif",
                    "font_weights": ["400", "600", "700"],
                    "text_style": "clean"
                },
                "components": {
                    "required_elements": ["header", "main-content", "footer"],
                    "optional_elements": ["sidebar", "hero-section"],
                    "interactive_elements": ["buttons", "forms"]
                },
                "style_preferences": {
                    "overall_style": "modern",
                    "visual_elements": ["cards", "shadows"],
                    "animations": "subtle",
                    "spacing": "balanced"
                }
            },
            "brand_analysis": {
                "brand_personality": "professional",
                "target_audience": "general",
                "industry_context": "technology",
                "brand_colors": ["#3B82F6"],
                "design_elements": ["clean-lines", "modern-typography"]
            },
            "technical_requirements": {
                "responsive_design": True,
                "accessibility": True,
                "performance_requirements": "standard",
                "browser_compatibility": ["chrome", "firefox", "safari", "edge"]
            },
            "content_structure": {
                "sections": ["header", "main", "footer"],
                "navigation": "header",
                "call_to_actions": ["primary-button"],
                "information_architecture": "hierarchical"
            }
        }
    
    def extract_ui_tags(self, specifications: Dict[str, Any]) -> List[str]:
        """Extract UI tags from specifications for template matching"""
        
        tags = []
        
        # Extract tags from UI specifications
        ui_specs = specifications.get("ui_specifications", {})
        
        # Layout tags
        tags.append(ui_specs.get("layout_type", "single-column"))
        
        # Style tags
        style_prefs = ui_specs.get("style_preferences", {})
        tags.append(style_prefs.get("overall_style", "modern"))
        tags.extend(style_prefs.get("visual_elements", []))
        
        # Component tags
        components = ui_specs.get("components", {})
        tags.extend(components.get("required_elements", []))
        tags.extend(components.get("interactive_elements", []))
        
        # Brand tags
        brand_analysis = specifications.get("brand_analysis", {})
        tags.append(brand_analysis.get("brand_personality", "professional"))
        tags.extend(brand_analysis.get("design_elements", []))
        
        # Technical tags
        tech_reqs = specifications.get("technical_requirements", {})
        if tech_reqs.get("responsive_design"):
            tags.append("responsive")
        if tech_reqs.get("accessibility"):
            tags.append("accessible")
        
        return list(set(tags))  # Remove duplicates
    
    def generate_template_search_criteria(self, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Generate search criteria for template matching"""
        
        ui_specs = specifications.get("ui_specifications", {})
        brand_analysis = specifications.get("brand_analysis", {})
        
        return {
            "category": "landing",  # Default, should be updated based on user input
            "style": ui_specs.get("style_preferences", {}).get("overall_style", "modern"),
            "layout": ui_specs.get("layout_type", "single-column"),
            "components": ui_specs.get("components", {}).get("required_elements", []),
            "brand_personality": brand_analysis.get("brand_personality", "professional"),
            "target_audience": brand_analysis.get("target_audience", "general"),
            "tags": self.extract_ui_tags(specifications)
        } 