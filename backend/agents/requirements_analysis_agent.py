from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class RequirementsAnalysisAgent(BaseAgent):
    """Focused agent with single responsibility: Analyze user requirements"""
    
    def __init__(self):
        system_message = """You are a Requirements Analysis Agent specialized in:
1. Understanding user needs and preferences for UI mockups
2. Extracting structured requirements from natural language
3. Identifying design patterns and user expectations
4. Creating comprehensive requirement specifications

You focus ONLY on requirements analysis. You do not recommend templates or generate questions."""
        
        super().__init__("RequirementsAnalysis", system_message)
        self.tool_utility = ToolUtility("requirements_analysis_agent")
        self.keyword_manager = KeywordManager()
    
    def analyze_requirements(self, user_prompt: str, category: str = None, logo_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Single job: Analyze user requirements from prompt"""
        
        # Detect page type from prompt
        detected_page_type = self.keyword_manager.detect_page_type(user_prompt)
        print(f"Detected page type: {detected_page_type} from prompt: '{user_prompt}'")
        
        # Override with provided category if available
        if category:
            detected_page_type = category
            print(f"OVERRIDE: page_type = {category}")
        
        # Get database context
        db_context = self._get_database_context(detected_page_type)
        
        # Merge contexts
        merged_context = self._merge_contexts(db_context, context or {})
        merged_context["page_type"] = detected_page_type
        merged_context["selected_category"] = detected_page_type
        
        # Build and execute analysis
        prompt = self._build_requirements_prompt(user_prompt, merged_context, logo_image)
        response = self._call_claude_with_tools(prompt, logo_image)
        
        # Parse and return results
        specifications = self._parse_requirements_response(response, merged_context)
        
        return self.create_standardized_response(
            success=True,
            data=specifications,
            metadata={"page_type": detected_page_type, "context_used": merged_context}
        )
    
    def analyze_logo_and_requirements(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze uploaded logo and extract design preferences for UI modification"""
        try:
            self.logger.info("Starting logo analysis and requirements extraction")
            
            # Extract logo image from context
            logo_image = context.get("logo_image")
            logo_filename = context.get("logo_filename", "uploaded_logo")
            current_ui_codes = context.get("current_ui_codes", {})
            
            if not logo_image:
                return self.create_standardized_response(
                    success=False,
                    error="No logo image provided"
                )
            
            # Build logo analysis prompt
            prompt = self._build_logo_analysis_prompt(user_message, logo_filename, current_ui_codes)
            
            # Call Claude with vision capabilities
            response = self._call_claude_with_vision(prompt, logo_image)
            
            # Parse logo analysis results
            logo_analysis = self._parse_logo_analysis_response(response)
            
            # Create design preferences based on logo analysis
            design_preferences = self._create_design_preferences_from_logo(logo_analysis, user_message)
            
            return self.create_standardized_response(
                success=True,
                data={
                    "logo_analysis": logo_analysis,
                    "design_preferences": design_preferences,
                    "user_request": user_message
                },
                metadata={
                    "logo_filename": logo_filename,
                    "analysis_type": "logo_design_extraction"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in logo analysis: {e}")
            return self.create_standardized_response(
                success=False,
                error=f"Failed to analyze logo: {str(e)}"
            )
    
    def _build_logo_analysis_prompt(self, user_message: str, logo_filename: str, current_ui_codes: Dict[str, Any]) -> str:
        """Build prompt for logo analysis"""
        prompt = f"""You are a design expert analyzing a logo to extract design preferences for UI modification.

LOGO ANALYSIS TASK:
Analyze the uploaded logo image and extract the following design elements:

1. **Color Palette**: Identify the primary, secondary, and accent colors used in the logo
2. **Style Characteristics**: Determine the design style (modern, classic, minimalist, bold, etc.)
3. **Typography**: Identify font styles and characteristics if text is present
4. **Visual Elements**: Note any shapes, patterns, or visual motifs
5. **Brand Personality**: Infer the brand's personality and values

USER REQUEST: {user_message}

CURRENT UI CONTEXT:
The user wants to apply the logo's design preferences to their current UI template.

ANALYSIS REQUIREMENTS:
- Be precise and specific about colors (use hex codes when possible)
- Identify the overall design aesthetic and style
- Note any unique visual elements that could be incorporated
- Consider how the logo's design principles can be applied to UI elements

Please provide a detailed analysis in the following JSON format:
{{
    "colors": ["#hex1", "#hex2", "#hex3"],
    "style": "modern|classic|minimalist|bold|playful|professional",
    "fonts": ["font_name_1", "font_name_2"],
    "visual_elements": ["element1", "element2"],
    "brand_personality": "description",
    "design_principles": ["principle1", "principle2"],
    "ui_application_notes": "specific suggestions for applying to UI"
}}

Focus on extracting actionable design information that can be used to modify the UI template."""
        
        return prompt
    
    def _call_claude_with_vision(self, prompt: str, logo_image: str) -> str:
        """Call Claude with vision capabilities for logo analysis"""
        try:
            # Prepare the message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": logo_image
                            }
                        }
                    ]
                }
            ]
            
            # Call Claude with vision model
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Use vision-capable model
                max_tokens=2000,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Error calling Claude with vision: {e}")
            raise e
    
    def _parse_logo_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the logo analysis response from Claude"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                return analysis
            else:
                # Fallback: create structured analysis from text
                return self._create_structured_analysis_from_text(response)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON from logo analysis: {e}")
            return self._create_structured_analysis_from_text(response)
        except Exception as e:
            self.logger.error(f"Error parsing logo analysis response: {e}")
            return {
                "colors": [],
                "style": "modern",
                "fonts": [],
                "visual_elements": [],
                "brand_personality": "professional",
                "design_principles": [],
                "ui_application_notes": "Apply modern design principles"
            }
    
    def _create_structured_analysis_from_text(self, response: str) -> Dict[str, Any]:
        """Create structured analysis from text response when JSON parsing fails"""
        analysis = {
            "colors": [],
            "style": "modern",
            "fonts": [],
            "visual_elements": [],
            "brand_personality": "professional",
            "design_principles": [],
            "ui_application_notes": "Apply modern design principles"
        }
        
        # Extract colors (look for hex codes)
        color_matches = re.findall(r'#[0-9A-Fa-f]{6}', response)
        if color_matches:
            analysis["colors"] = color_matches[:5]  # Limit to 5 colors
        
        # Extract style keywords
        style_keywords = ["modern", "classic", "minimalist", "bold", "playful", "professional", "elegant", "clean"]
        for keyword in style_keywords:
            if keyword.lower() in response.lower():
                analysis["style"] = keyword
                break
        
        # Extract font mentions
        font_keywords = ["sans-serif", "serif", "helvetica", "arial", "times", "roboto", "open sans"]
        found_fonts = []
        for font in font_keywords:
            if font.lower() in response.lower():
                found_fonts.append(font)
        analysis["fonts"] = found_fonts
        
        return analysis
    
    def _create_design_preferences_from_logo(self, logo_analysis: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """Create design preferences based on logo analysis"""
        preferences = {
            "color_scheme": {
                "primary_colors": logo_analysis.get("colors", [])[:3],
                "accent_colors": logo_analysis.get("colors", [])[3:5] if len(logo_analysis.get("colors", [])) > 3 else []
            },
            "style_preferences": {
                "overall_style": logo_analysis.get("style", "modern"),
                "brand_personality": logo_analysis.get("brand_personality", "professional")
            },
            "typography": {
                "font_families": logo_analysis.get("fonts", []),
                "font_style": "sans-serif" if "sans" in str(logo_analysis.get("fonts", [])).lower() else "serif"
            },
            "visual_elements": logo_analysis.get("visual_elements", []),
            "design_principles": logo_analysis.get("design_principles", []),
            "ui_modification_guidelines": logo_analysis.get("ui_application_notes", "")
        }
        
        return preferences
    
    def _get_database_context(self, category: str = None) -> Dict[str, Any]:
        """Get database context for requirements analysis"""
        context = {
            "available_categories": [],
            "available_tags": [],
            "category_templates": []
        }
        
        try:
            # Get available categories
            categories_result = self.tool_utility.call_function("get_available_categories", {})
            if categories_result.get("success"):
                context["available_categories"] = categories_result.get("categories", [])
            
            # Get templates for the category
            if category:
                templates_result = self.tool_utility.call_function("get_templates_by_category", {"category": category, "limit": 10})
                if templates_result.get("success"):
                    templates = templates_result.get("templates", [])
                    context["category_templates"] = templates
                    context["available_tags"] = self._extract_tags_from_templates(templates)
            
        except Exception as e:
            print(f"ERROR: Error getting database context: {e}")
        
        return context
    
    def _extract_tags_from_templates(self, templates: List[Dict[str, Any]]) -> List[str]:
        """Extract unique tags from templates"""
        all_tags = set()
        for template in templates:
            tags = template.get("tags", [])
            all_tags.update(tags)
        return list(all_tags)
    
    def _merge_contexts(self, db_context: Dict[str, Any], frontend_context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge database and frontend contexts"""
        merged = db_context.copy()
        
        # Add frontend context
        if frontend_context:
            merged.update(frontend_context)
        
        return merged
    
    def _build_requirements_prompt(self, user_prompt: str, context: Dict[str, Any], logo_image: Optional[str] = None) -> str:
        """Build prompt for requirements analysis"""
        
        # Extract context information
        available_categories = context.get("available_categories", [])
        available_tags = context.get("available_tags", [])
        category_templates = context.get("category_templates", [])
        page_type = context.get("page_type", "landing")
        
        # Build template information
        template_info = ""
        if category_templates:
            template_info = "AVAILABLE TEMPLATES IN CATEGORY:\n"
            for i, template in enumerate(category_templates[:5], 1):  # Show first 5 templates
                name = template.get("name", f"Template {i}")
                tags = template.get("tags", [])
                template_info += f"{i}. {name} - Tags: {', '.join(tags) if tags else 'None'}\n"
        
        # Build logo context
        logo_context = ""
        if logo_image:
            logo_context = f"""
LOGO CONTEXT:
- Logo image provided: {logo_image}
- Consider logo integration in design requirements
- Ensure brand consistency with logo colors and style
"""
        
        prompt = f"""
You are an expert UI/UX requirements analyst. Analyze the user's request and extract comprehensive requirements.

USER REQUEST:
"{user_prompt}"

CONTEXT:
- Page Type: {page_type}
- Available Categories: {', '.join(available_categories)}
- Available Design Tags: {', '.join(available_tags[:20])}  # Show first 20 tags
- Templates in Category: {len(category_templates)} templates

{template_info}

{logo_context}

TASK:
Analyze the user's requirements and provide a comprehensive specification. Return a JSON object with this structure:

{{
    "page_type": "{page_type}",
    "target_audience": "Description of target users",
    "style_preferences": ["list", "of", "style", "preferences"],
    "key_features": ["list", "of", "required", "features"],
    "color_scheme": "Preferred color scheme or theme",
    "layout_preferences": "Layout preferences (e.g., single column, grid, etc.)",
    "ui_specifications": {{
        "required_elements": ["list", "of", "UI", "elements"],
        "interactive_elements": ["list", "of", "features"],
        "content_priorities": ["list", "of", "content", "priorities"],
        "accessibility_requirements": ["list", "of", "accessibility", "needs"]
    }},
    "technical_requirements": {{
        "responsive_design": true/false,
        "browser_compatibility": ["list", "of", "browsers"],
        "performance_requirements": "Performance expectations"
    }},
    "business_context": {{
        "brand_guidelines": "Brand considerations",
        "conversion_goals": "Business objectives",
        "success_metrics": ["list", "of", "success", "metrics"]
    }},
    "questions_for_clarification": ["list", "of", "questions"],
    "constraints": ["list", "of", "constraints"]
}}

IMPORTANT:
- Be specific and actionable
- Consider the available templates and tags
- Focus on what can be implemented
- Identify any missing information that needs clarification
"""
        
        return prompt
    
    def _call_claude_with_tools(self, prompt: str, logo_image: Optional[str] = None) -> str:
        """Call Claude with tool calling capabilities"""
        try:
            client = self.claude_client
            messages = [{"role": "user", "content": prompt}]
            
            # Add logo image if provided
            if logo_image:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please consider this logo in your analysis:"},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": logo_image}}
                    ]
                })
            
            # Get available tools
            tools = self.tool_utility.get_tools()
            print(f"DEBUG: Tools being passed to Claude: {json.dumps(tools, indent=2)}")
            
            # Call Claude
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=messages,
                tools=tools if tools else None,
                tool_choice={"type": "auto"} if tools else None
            )
            
            # Handle tool calls if any
            if response.content and hasattr(response.content[0], 'tool_calls') and response.content[0].tool_calls:
                tool_results = []
                for tool_call in response.content[0].tool_calls:
                    tool_name = tool_call.name
                    
                    # Handle different tool call formats
                    if hasattr(tool_call, 'input'):
                        # Custom tool format
                        tool_args = json.loads(tool_call.input)
                    elif hasattr(tool_call, 'arguments'):
                        # Function call format
                        tool_args = json.loads(tool_call.arguments)
                    else:
                        # Fallback
                        tool_args = {}
                    
                    # Call the tool
                    tool_result = self.tool_utility.call_function(tool_name, tool_args)
                    tool_results.append({
                        "tool_call_id": getattr(tool_call, 'id', 'unknown'),
                        "name": tool_name,
                        "result": tool_result
                    })
                
                # If we have tool results, make another call with the results
                if tool_results:
                    tool_response_prompt = f"""
                    Based on the tool results below, please provide your final requirements analysis:

                    TOOL RESULTS:
                    {json.dumps(tool_results, indent=2)}

                    ORIGINAL PROMPT:
                    {prompt}

                    Please provide your requirements analysis in the requested JSON format.
                    """
                    
                    final_response = client.messages.create(
                        model=self.model,
                        max_tokens=4000,
                        messages=[{"role": "user", "content": tool_response_prompt}]
                    )
                    
                    return final_response.content[0].text
            
            return response.content[0].text
            
        except Exception as e:
            print(f"ERROR: Error calling Claude with tools: {e}")
            return f"Error: {str(e)}"
    
    def _parse_requirements_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM response and return structured requirements"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                # Clean up common JSON issues
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                try:
                    specifications = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"ERROR: Failed to parse JSON response: {e}")
                    print(f"JSON string: {json_str}")
                    specifications = self._get_default_specifications()
            else:
                specifications = self._get_default_specifications()
            
            # Ensure page_type from context is preserved
            if context.get("page_type"):
                specifications["page_type"] = context["page_type"]
                print(f"Preserved page_type from context: {context['page_type']}")
            
            # Add database context to specifications
            specifications["database_context"] = {
                "available_categories": context.get("available_categories", []),
                "available_tags": context.get("available_tags", []),
                "category_templates_count": len(context.get("category_templates", []))
            }
            
            return specifications
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            specifications = self._get_default_specifications()
            # Ensure page_type from context is preserved even on error
            if context.get("page_type"):
                specifications["page_type"] = context["page_type"]
                print(f"Preserved page_type from context on error: {context['page_type']}")
            return specifications
        except Exception as e:
            print(f"ERROR: Unexpected error in parse_requirements_response: {e}")
            specifications = self._get_default_specifications()
            # Ensure page_type from context is preserved even on error
            if context.get("page_type"):
                specifications["page_type"] = context["page_type"]
                print(f"Preserved page_type from context on error: {context['page_type']}")
            return specifications
    
    def _get_default_specifications(self) -> Dict[str, Any]:
        """Return default specifications when analysis fails"""
        return {
            "page_type": "landing",
            "target_audience": "general users",
            "style_preferences": ["modern", "clean"],
            "key_features": ["responsive", "user-friendly"],
            "color_scheme": "neutral",
            "layout_preferences": "single column",
            "ui_specifications": {
                "required_elements": ["header", "main content", "footer"],
                "interactive_elements": ["navigation"],
                "content_priorities": ["clarity", "accessibility"],
                "accessibility_requirements": ["basic accessibility"]
            },
            "technical_requirements": {
                "responsive_design": True,
                "browser_compatibility": ["modern browsers"],
                "performance_requirements": "standard performance"
            },
            "business_context": {
                "brand_guidelines": "flexible",
                "conversion_goals": "user engagement",
                "success_metrics": ["user satisfaction"]
            },
            "questions_for_clarification": ["What specific features are most important?"],
            "constraints": ["time and budget constraints"]
        } 