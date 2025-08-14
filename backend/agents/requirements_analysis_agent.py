from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
import logging
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
        self.logger = logging.getLogger(__name__)
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
            
            self.logger.info(f"Logo analysis context - filename: {logo_filename}, image_length: {len(logo_image) if logo_image else 0}")
            
            if not logo_image:
                self.logger.error("No logo image provided in context")
                return self.create_standardized_response(
                    success=False,
                    data={"error": "No logo image provided"}
                )
            
            # Validate base64 data
            try:
                import base64
                # Try to decode a small portion to validate base64
                test_decode = base64.b64decode(logo_image[:100] + "==")
                self.logger.info("Base64 validation successful")
            except Exception as base64_error:
                self.logger.error(f"Invalid base64 data: {base64_error}")
                return self.create_standardized_response(
                    success=False,
                    data={"error": f"Invalid image data format: {str(base64_error)}"}
                )
            
            # Build logo analysis prompt
            self.logger.info("Building logo analysis prompt")
            prompt = self._build_logo_analysis_prompt(user_message, logo_filename, current_ui_codes)
            
            # Call Claude with vision capabilities
            self.logger.info("Calling Claude with vision capabilities")
            response = self._call_claude_with_vision(prompt, logo_image)
            self.logger.info(f"Received vision API response, length: {len(response)}")
            
            # Parse logo analysis results
            logo_analysis = self._parse_logo_analysis_response(response, context)
            
            # Extract design preferences
            design_preferences = self._extract_design_preferences(logo_analysis, context)
            
            return self.create_standardized_response(
                success=True,
                data={
                    "logo_analysis": logo_analysis,
                    "design_preferences": design_preferences
                },
                metadata={"logo_filename": logo_filename, "context_used": context}
            )
            
        except Exception as e:
            self.logger.error(f"Error in logo analysis: {e}")
            import traceback
            self.logger.error(f"Logo analysis traceback: {traceback.format_exc()}")
            return self.create_standardized_response(
                success=False,
                data={"error": f"Logo analysis failed: {str(e)}"}
            )
    
    def _build_requirements_prompt(self, user_prompt: str, context: Dict[str, Any], logo_image: Optional[str] = None) -> str:
        """Build the requirements analysis prompt"""
        base_prompt = f"""
You are a Requirements Analysis Agent. Analyze the user's request and extract structured requirements.

USER REQUEST: {user_prompt}

CONTEXT:
- Page Type: {context.get('page_type', 'unknown')}
- Available Categories: {context.get('available_categories', [])}
- Available Tags: {context.get('available_tags', [])}
- Category Templates Count: {len(context.get('category_templates', []))}

TASK: Extract comprehensive requirements for UI mockup creation.

REQUIRED OUTPUT FORMAT (JSON only):
{{
  "page_type": "string",
  "target_audience": "string", 
  "style_preferences": ["array", "of", "strings"],
  "key_features": ["array", "of", "strings"],
  "color_scheme": "string",
  "layout_preferences": "string",
  "ui_specifications": {{
    "required_elements": ["array", "of", "strings"],
    "interactive_elements": ["array", "of", "strings"],
    "content_priorities": ["array", "of", "strings"],
    "accessibility_requirements": ["array", "of", "strings"]
  }},
  "technical_requirements": {{
    "responsive_design": boolean,
    "browser_compatibility": ["array", "of", "strings"],
    "performance_requirements": "string"
  }},
  "business_context": {{
    "brand_guidelines": "string",
    "conversion_goals": "string",
    "success_metrics": ["array", "of", "strings"]
  }},
  "questions_for_clarification": ["array", "of", "strings"],
  "constraints": ["array", "of", "strings"]
}}

IMPORTANT: 
- Respond with ONLY the JSON object above
- NO explanatory text before or after
- NO markdown formatting
- Use the available tools to gather information if needed
"""
        
        if logo_image:
            base_prompt += "\n\nLOGO ANALYSIS: Analyze the uploaded logo for design preferences and color schemes."
        
        return base_prompt
    
    def _build_logo_analysis_prompt(self, user_message: str, logo_filename: str, current_ui_codes: Dict[str, str]) -> str:
        """Build the logo analysis prompt"""
        return f"""
You are analyzing a logo image to extract design preferences for UI modification.

USER REQUEST: {user_message}

LOGO FILENAME: {logo_filename}

CURRENT UI CONTEXT:
- HTML: {len(current_ui_codes.get('html', ''))} characters
- CSS: {len(current_ui_codes.get('style_css', ''))} characters

ANALYZE THE LOGO FOR:
1. **Color Scheme**: Extract dominant colors, color temperature, brightness
2. **Design Style**: Modern, minimalist, professional, creative, etc.
3. **Brand Personality**: What does the logo convey about the brand?
4. **Visual Elements**: Shapes, typography, composition style
5. **Accessibility**: Color contrast and readability considerations

PROVIDE ANALYSIS IN THIS JSON FORMAT:
{{
  "color_analysis": {{
    "dominant_colors": ["#hex1", "#hex2"],
    "color_temperature": "warm/cool/neutral",
    "brightness": "light/medium/dark",
    "saturation": "high/medium/low"
  }},
  "design_style": "string",
  "brand_personality": "string",
  "visual_elements": ["array", "of", "strings"],
  "accessibility_notes": "string",
  "recommended_ui_changes": [
    {{
      "element": "string",
      "change_type": "color/style/layout",
      "description": "string",
      "priority": "high/medium/low"
    }}
  ]
}}

IMPORTANT: Respond with ONLY the JSON object above. NO explanatory text.
"""
    
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

            # Call Claude
            response = client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=messages,
                tools=tools if tools else None,
                tool_choice={"type": "auto"} if tools else None
            )

                                # Debug: Log LLM response
            response_text = response.content[0].text
            print(f"DEBUG: Requirements Analysis Agent LLM Response Length: {len(response_text)} chars")
            print(f"DEBUG: Requirements Analysis Agent LLM Response Preview: {response_text[:200]}...")
                    
            # Only log full response if it's very short (for debugging)
            if len(response_text) < 1000:
                print(f"DEBUG: Requirements Analysis Agent Full Response: {response_text}")
            else:
                print(f"DEBUG: Requirements Analysis Agent Response truncated for logging (too long)")

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

                    IMPORTANT: You MUST respond with ONLY a valid JSON object. Do NOT include any explanatory text, introductions, or conclusions before or after the JSON.

                    REQUIRED FORMAT:
                    {{
                      "page_type": "string",
                      "target_audience": "string", 
                      "style_preferences": ["array", "of", "strings"],
                      "key_features": ["array", "of", "strings"],
                      "color_scheme": "string",
                      "layout_preferences": "string",
                      "ui_specifications": {{
                        "required_elements": ["array", "of", "strings"],
                        "interactive_elements": ["array", "of", "strings"],
                        "content_priorities": ["array", "of", "strings"],
                        "accessibility_requirements": ["array", "of", "strings"]
                      }},
                      "technical_requirements": {{
                        "responsive_design": boolean,
                        "browser_compatibility": ["array", "of", "strings"],
                        "performance_requirements": "string"
                      }},
                      "business_context": {{
                        "brand_guidelines": "string",
                        "conversion_goals": "string",
                        "success_metrics": ["array", "of", "strings"]
                      }},
                      "questions_for_clarification": ["array", "of", "strings"],
                      "constraints": ["array", "of", "strings"]
                    }}

                    RULES:
                    - NO TEXT BEFORE OR AFTER THE JSON OBJECT
                    - NO EXPLANATIONS OUTSIDE THE JSON
                    - ONLY VALID JSON
                    """
                    
                    final_response = client.messages.create(
                        model=self.model,
                        max_tokens=8000,
                        messages=[{"role": "user", "content": tool_response_prompt}]
                    )

                    # Debug: Log final LLM response after tool calls
                    print(f"DEBUG: Requirements Analysis Agent Final Response: {final_response.content[0].text[:500]}...")
                    if len(final_response.content[0].text) > 500:
                        print(f"DEBUG: Full Requirements Analysis Final Response: {final_response.content[0].text}")

                    return final_response.content[0].text

            return response.content[0].text

        except Exception as e:
            print(f"ERROR: Error calling Claude with tools: {e}")
            return f"Error: {str(e)}"
    
    def _parse_requirements_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM response and return structured requirements"""
        print(f"DEBUG: Requirements Analysis Agent - Parsing response")
        print(f"DEBUG: Requirements Analysis Agent - Raw response preview: {response[:200]}...")
        
        try:
            # Simple JSON extraction - look for JSON object in response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                print(f"DEBUG: Requirements Analysis Agent - Extracted JSON: {json_str[:200]}...")
                
                try:
                    specifications = json.loads(json_str)
                    print("DEBUG: Requirements Analysis Agent - JSON parsing successful")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Requirements Analysis Agent - JSON parsing failed: {e}")
                    specifications = self._get_default_specifications()
            else:
                print("DEBUG: Requirements Analysis Agent - No JSON structure found, using default specifications")
                specifications = self._get_default_specifications()
            
            # CRITICAL FIX: Don't override the LLM's page_type analysis with old context
            # The LLM has analyzed the user's request and determined the correct page_type
            print(f"DEBUG: LLM returned page_type: '{specifications.get('page_type', 'None')}'")
            print(f"DEBUG: Context has page_type: '{context.get('page_type', 'None')}'")
            
            if context.get("page_type") and not specifications.get("page_type"):
                # Only use context page_type if LLM didn't provide one
                specifications["page_type"] = context["page_type"]
                print(f"Fallback: Using page_type '{context['page_type']}' from context (LLM didn't provide one)")
            elif specifications.get("page_type"):
                print(f"Using LLM-analyzed page_type: '{specifications['page_type']}'")
            
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
            # Only use context page_type on error if we don't have one from LLM
            if context.get("page_type") and not specifications.get("page_type"):
                specifications["page_type"] = context["page_type"]
                print(f"Error fallback: Using page_type '{context['page_type']}' from context")
            return specifications
        except Exception as e:
            print(f"ERROR: Unexpected error in parse_requirements_response: {e}")
            specifications = self._get_default_specifications()
            # Only use context page_type on error if we don't have one from LLM
            if context.get("page_type") and not specifications.get("page_type"):
                specifications["page_type"] = context["page_type"]
                print(f"Error fallback: Using page_type '{context['page_type']}' from context")
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
    
    def _parse_logo_analysis_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the logo analysis response"""
        try:
            # Simple JSON extraction
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"error": "No JSON found in response"}
        except Exception as e:
            self.logger.error(f"Error parsing logo analysis: {e}")
            return {"error": f"Parsing failed: {str(e)}"}
    
    def _extract_design_preferences(self, logo_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract design preferences from logo analysis"""
        try:
            if "error" in logo_analysis:
                return {"error": logo_analysis["error"]}
            
            # Extract key design elements
            color_analysis = logo_analysis.get("color_analysis", {})
            design_style = logo_analysis.get("design_style", "modern")
            brand_personality = logo_analysis.get("brand_personality", "professional")
            
            return {
                "color_scheme": color_analysis.get("dominant_colors", ["#000000"]),
                "design_style": design_style,
                "brand_personality": brand_personality,
                "recommended_changes": logo_analysis.get("recommended_ui_changes", [])
            }
        except Exception as e:
            self.logger.error(f"Error extracting design preferences: {e}")
            return {"error": f"Extraction failed: {str(e)}"}
    
    def _get_database_context(self, page_type: str) -> Dict[str, Any]:
        """Get database context for the given page type"""
        try:
            # Get available categories
            categories = list(self.db.templates.distinct("category"))
            
            # Get templates for the specific page type
            category_templates = list(self.db.templates.find({"category": page_type}))
            
            # Get all available tags
            all_tags = []
            for template in self.db.templates.find():
                if "tags" in template:
                    all_tags.extend(template["tags"])
            all_tags = list(set(all_tags))  # Remove duplicates
            
            return {
                "available_categories": categories,
                "category_templates": category_templates,
                "available_tags": all_tags
            }
        except Exception as e:
            print(f"Error getting database context: {e}")
            return {
                "available_categories": [],
                "category_templates": [],
                "available_tags": []
            }
    
    def _merge_contexts(self, db_context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge database context with user context"""
        merged = db_context.copy()
        merged.update(user_context)
        return merged
