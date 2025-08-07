#!/usr/bin/env python3
"""
Enhanced Template Recommendation Agent with improved JSON parsing
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from tools.tool_utility import ToolUtility


class TemplateRecommendationAgentEnhanced(BaseAgent):
    """Enhanced Template Recommendation Agent with improved JSON parsing"""
    
    def __init__(self):
        system_message = """You are an expert template recommendation agent specializing in UI/UX template selection. You analyze user requirements and match them with the most suitable templates from the database.

Your role is to:
1. Understand user requirements and preferences
2. Analyze template metadata and characteristics
3. Score templates based on suitability
4. Provide detailed reasoning for recommendations
5. Return ONLY valid JSON responses

**CRITICAL**: Always return valid JSON format, no additional text or explanations."""
        
        super().__init__("TemplateRecommendation", system_message, model="claude-3-5-sonnet-20241022")
        self.logger = logging.getLogger(__name__)
        self.tool_utility = ToolUtility("template_recommendation_agent")
    
    def recommend_templates(self, requirements: Dict[str, Any], category: str = None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Recommend templates based on requirements"""
        try:
            # Get templates from database
            templates = self._get_templates_from_database(requirements, category)
            
            if not templates:
                self.logger.warning("No templates found for requirements")
                return []
            
            # Score templates using LLM
            scored_templates = self._score_templates_with_llm(requirements, templates, context)
            
            return scored_templates
            
        except Exception as e:
            self.logger.error(f"Error in template recommendation: {e}")
            return []
    
    def _get_templates_from_database(self, requirements: Dict[str, Any], category: str = None) -> List[Dict[str, Any]]:
        """Get templates from database"""
        try:
            # Use tool utility to get templates
            if category:
                result = self.tool_utility.call_function("get_templates_by_category", {"category": category})
            else:
                # Try to extract category from requirements
                page_type = requirements.get("page_type", "").lower()
                if page_type in ["profile", "landing", "login", "signup"]:
                    result = self.tool_utility.call_function("get_templates_by_category", {"category": page_type})
                else:
                    # Get all categories and search
                    result = self.tool_utility.call_function("search_templates_by_tags", {"tags": [page_type] if page_type else []})
            
            # Handle different return types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "templates" in result:
                return result["templates"]
            elif isinstance(result, dict) and "data" in result:
                return result["data"]
            elif isinstance(result, str):
                # Try to parse JSON string
                try:
                    import json
                    parsed = json.loads(result)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict) and "templates" in parsed:
                        return parsed["templates"]
                    elif isinstance(parsed, dict) and "data" in parsed:
                        return parsed["data"]
                except:
                    pass
            
            self.logger.warning(f"Unexpected template result type: {type(result)}, value: {result}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting templates from database: {e}")
            return []
    
    def _score_templates_with_llm(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Score templates using LLM with enhanced JSON parsing"""
        try:
            # Validate templates input
            if not isinstance(templates, list):
                self.logger.error(f"Invalid templates type: {type(templates)}, expected list")
                return self._fallback_scoring([])
            
            if not templates:
                self.logger.warning("No templates to score")
                return []
            
            # Validate each template
            valid_templates = []
            for template in templates:
                if isinstance(template, dict):
                    valid_templates.append(template)
                else:
                    self.logger.warning(f"Skipping invalid template: {type(template)}")
            
            if not valid_templates:
                self.logger.error("No valid templates found")
                return self._fallback_scoring([])
            
            # Build enhanced scoring prompt
            prompt = self._build_enhanced_scoring_prompt(requirements, valid_templates, context)
            
            # Call LLM with enhanced prompt
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse response with enhanced JSON extraction
            scored_templates = self._parse_enhanced_scoring_response(response, valid_templates)
            
            return scored_templates
            
        except Exception as e:
            self.logger.error(f"Error scoring templates with LLM: {e}")
            return self._fallback_scoring(templates if isinstance(templates, list) else [])
    
    def _build_enhanced_scoring_prompt(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> str:
        """Build enhanced scoring prompt with strict JSON requirements"""
        
        # Format requirements for the prompt
        requirements_text = self._format_requirements_for_prompt(requirements)
        
        # Format templates for the prompt
        templates_text = self._format_templates_for_prompt(templates)
        
        prompt = f"""
You are a template recommendation expert. Analyze templates against user requirements and provide suitability scores.

## USER REQUIREMENTS
{requirements_text}

## AVAILABLE TEMPLATES
{templates_text}

## TASK
Score each template (0.0 to 1.0) based on how well it matches the requirements.

## OUTPUT FORMAT
Return ONLY valid JSON in this exact format:
{{
    "scored_templates": [
        {{
            "template": {{
                "template_id": "string",
                "name": "string",
                "category": "string",
                "description": "string",
                "tags": ["array", "of", "tags"]
            }},
            "score": 0.85,
            "reasoning": "Detailed explanation of suitability",
            "suitability_level": "high|medium|low"
        }}
    ]
}}

## SCORING CRITERIA
- **0.9-1.0**: Perfect match, highly recommended
- **0.7-0.8**: Good match, recommended  
- **0.5-0.6**: Moderate match, acceptable
- **0.3-0.4**: Poor match, not recommended
- **0.0-0.2**: Very poor match, avoid

## CRITICAL INSTRUCTIONS
- **Return ONLY the JSON object, no additional text**
- **Do NOT include any introductory text or explanations**
- **Do NOT use phrases like "I'll help you evaluate..." or "Here's my analysis..."**
- **Start directly with {{ and end with }}**
- **Ensure all JSON is valid and properly formatted**
- **Include all templates in the response**

## FORBIDDEN PHRASES (NEVER USE):
- "I'll help you evaluate..."
- "Here's my analysis..."
- "Let me analyze..."
- "Based on the requirements..."
- Any other introductory or explanatory text

Return ONLY the JSON object.
"""
        
        return prompt
    
    def _format_requirements_for_prompt(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for the prompt"""
        if not requirements:
            return "No specific requirements provided"
        
        formatted = []
        for key, value in requirements.items():
            if isinstance(value, list):
                formatted.append(f"- {key}: {', '.join(value)}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_templates_for_prompt(self, templates: List[Dict[str, Any]]) -> str:
        """Format templates for the prompt"""
        if not templates:
            return "No templates available"
        
        formatted = []
        for i, template in enumerate(templates, 1):
            template_info = f"""
Template {i}:
- ID: {template.get('template_id', 'N/A')}
- Name: {template.get('name', 'N/A')}
- Category: {template.get('category', 'N/A')}
- Description: {template.get('description', 'N/A')}
- Tags: {', '.join(template.get('tags', []))}
"""
            formatted.append(template_info)
        
        return "\n".join(formatted)
    
    def _parse_enhanced_scoring_response(self, response: str, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse enhanced scoring response with robust JSON extraction"""
        try:
            # Extract JSON using enhanced method
            json_str = self._extract_json_enhanced(response)
            
            if not json_str:
                self.logger.warning("No JSON found in response, using fallback scoring")
                return self._fallback_scoring(templates)
            
            # Parse JSON
            result = json.loads(json_str)
            
            if "scored_templates" not in result:
                self.logger.warning("Invalid JSON structure, using fallback scoring")
                return self._fallback_scoring(templates)
            
            return result["scored_templates"]
            
        except Exception as e:
            self.logger.error(f"Error parsing scoring response: {e}")
            return self._fallback_scoring(templates)
    
    def _extract_json_enhanced(self, response: str) -> Optional[str]:
        """Enhanced JSON extraction with multiple strategies"""
        try:
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    # Validate JSON
                    json.loads(json_str)
                    return json_str
            
            # Strategy 2: Find first complete JSON object with proper brace matching
            if "{" in response and "}" in response:
                brace_count = 0
                start_pos = -1
                
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos >= 0:
                            # Found complete JSON object
                            json_str = response[start_pos:i+1]
                            # Try to clean and validate
                            try:
                                json.loads(json_str)
                                return json_str
                            except json.JSONDecodeError:
                                json_str = self._clean_json_string(json_str)
                                json.loads(json_str)
                                return json_str
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                # Try to clean and validate
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    json_str = self._clean_json_string(json_str)
                    json.loads(json_str)
                    return json_str
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting JSON: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove common issues"""
        import re
        
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        
        # Fix common quote issues
        json_str = re.sub(r'(?<!\\)"([^"]*)"', r'"\1"', json_str)
        
        return json_str
    
    def _fallback_scoring(self, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback scoring when LLM fails"""
        scored_templates = []
        
        for template in templates:
            scored_template = {
                "template": template,
                "score": 0.5,  # Default medium score
                "reasoning": "Fallback scoring applied due to LLM parsing error",
                "suitability_level": "medium"
            }
            scored_templates.append(scored_template)
        
        return scored_templates 
"""
Enhanced Template Recommendation Agent with improved JSON parsing
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from tools.tool_utility import ToolUtility


class TemplateRecommendationAgentEnhanced(BaseAgent):
    """Enhanced Template Recommendation Agent with improved JSON parsing"""
    
    def __init__(self):
        system_message = """You are an expert template recommendation agent specializing in UI/UX template selection. You analyze user requirements and match them with the most suitable templates from the database.

Your role is to:
1. Understand user requirements and preferences
2. Analyze template metadata and characteristics
3. Score templates based on suitability
4. Provide detailed reasoning for recommendations
5. Return ONLY valid JSON responses

**CRITICAL**: Always return valid JSON format, no additional text or explanations."""
        
        super().__init__("TemplateRecommendation", system_message, model="claude-3-5-sonnet-20241022")
        self.logger = logging.getLogger(__name__)
        self.tool_utility = ToolUtility("template_recommendation_agent")
    
    def recommend_templates(self, requirements: Dict[str, Any], category: str = None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Recommend templates based on requirements"""
        try:
            # Get templates from database
            templates = self._get_templates_from_database(requirements, category)
            
            if not templates:
                self.logger.warning("No templates found for requirements")
                return []
            
            # Score templates using LLM
            scored_templates = self._score_templates_with_llm(requirements, templates, context)
            
            return scored_templates
            
        except Exception as e:
            self.logger.error(f"Error in template recommendation: {e}")
            return []
    
    def _get_templates_from_database(self, requirements: Dict[str, Any], category: str = None) -> List[Dict[str, Any]]:
        """Get templates from database"""
        try:
            # Use tool utility to get templates
            if category:
                result = self.tool_utility.call_function("get_templates_by_category", {"category": category})
            else:
                # Try to extract category from requirements
                page_type = requirements.get("page_type", "").lower()
                if page_type in ["profile", "landing", "login", "signup"]:
                    result = self.tool_utility.call_function("get_templates_by_category", {"category": page_type})
                else:
                    # Get all categories and search
                    result = self.tool_utility.call_function("search_templates_by_tags", {"tags": [page_type] if page_type else []})
            
            # Handle different return types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "templates" in result:
                return result["templates"]
            elif isinstance(result, dict) and "data" in result:
                return result["data"]
            elif isinstance(result, str):
                # Try to parse JSON string
                try:
                    import json
                    parsed = json.loads(result)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict) and "templates" in parsed:
                        return parsed["templates"]
                    elif isinstance(parsed, dict) and "data" in parsed:
                        return parsed["data"]
                except:
                    pass
            
            self.logger.warning(f"Unexpected template result type: {type(result)}, value: {result}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting templates from database: {e}")
            return []
    
    def _score_templates_with_llm(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Score templates using LLM with enhanced JSON parsing"""
        try:
            # Validate templates input
            if not isinstance(templates, list):
                self.logger.error(f"Invalid templates type: {type(templates)}, expected list")
                return self._fallback_scoring([])
            
            if not templates:
                self.logger.warning("No templates to score")
                return []
            
            # Validate each template
            valid_templates = []
            for template in templates:
                if isinstance(template, dict):
                    valid_templates.append(template)
                else:
                    self.logger.warning(f"Skipping invalid template: {type(template)}")
            
            if not valid_templates:
                self.logger.error("No valid templates found")
                return self._fallback_scoring([])
            
            # Build enhanced scoring prompt
            prompt = self._build_enhanced_scoring_prompt(requirements, valid_templates, context)
            
            # Call LLM with enhanced prompt
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse response with enhanced JSON extraction
            scored_templates = self._parse_enhanced_scoring_response(response, valid_templates)
            
            return scored_templates
            
        except Exception as e:
            self.logger.error(f"Error scoring templates with LLM: {e}")
            return self._fallback_scoring(templates if isinstance(templates, list) else [])
    
    def _build_enhanced_scoring_prompt(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> str:
        """Build enhanced scoring prompt with strict JSON requirements"""
        
        # Format requirements for the prompt
        requirements_text = self._format_requirements_for_prompt(requirements)
        
        # Format templates for the prompt
        templates_text = self._format_templates_for_prompt(templates)
        
        prompt = f"""
You are a template recommendation expert. Analyze templates against user requirements and provide suitability scores.

## USER REQUIREMENTS
{requirements_text}

## AVAILABLE TEMPLATES
{templates_text}

## TASK
Score each template (0.0 to 1.0) based on how well it matches the requirements.

## OUTPUT FORMAT
Return ONLY valid JSON in this exact format:
{{
    "scored_templates": [
        {{
            "template": {{
                "template_id": "string",
                "name": "string",
                "category": "string",
                "description": "string",
                "tags": ["array", "of", "tags"]
            }},
            "score": 0.85,
            "reasoning": "Detailed explanation of suitability",
            "suitability_level": "high|medium|low"
        }}
    ]
}}

## SCORING CRITERIA
- **0.9-1.0**: Perfect match, highly recommended
- **0.7-0.8**: Good match, recommended  
- **0.5-0.6**: Moderate match, acceptable
- **0.3-0.4**: Poor match, not recommended
- **0.0-0.2**: Very poor match, avoid

## CRITICAL INSTRUCTIONS
- **Return ONLY the JSON object, no additional text**
- **Do NOT include any introductory text or explanations**
- **Do NOT use phrases like "I'll help you evaluate..." or "Here's my analysis..."**
- **Start directly with {{ and end with }}**
- **Ensure all JSON is valid and properly formatted**
- **Include all templates in the response**

## FORBIDDEN PHRASES (NEVER USE):
- "I'll help you evaluate..."
- "Here's my analysis..."
- "Let me analyze..."
- "Based on the requirements..."
- Any other introductory or explanatory text

Return ONLY the JSON object.
"""
        
        return prompt
    
    def _format_requirements_for_prompt(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for the prompt"""
        if not requirements:
            return "No specific requirements provided"
        
        formatted = []
        for key, value in requirements.items():
            if isinstance(value, list):
                formatted.append(f"- {key}: {', '.join(value)}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_templates_for_prompt(self, templates: List[Dict[str, Any]]) -> str:
        """Format templates for the prompt"""
        if not templates:
            return "No templates available"
        
        formatted = []
        for i, template in enumerate(templates, 1):
            template_info = f"""
Template {i}:
- ID: {template.get('template_id', 'N/A')}
- Name: {template.get('name', 'N/A')}
- Category: {template.get('category', 'N/A')}
- Description: {template.get('description', 'N/A')}
- Tags: {', '.join(template.get('tags', []))}
"""
            formatted.append(template_info)
        
        return "\n".join(formatted)
    
    def _parse_enhanced_scoring_response(self, response: str, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse enhanced scoring response with robust JSON extraction"""
        try:
            # Extract JSON using enhanced method
            json_str = self._extract_json_enhanced(response)
            
            if not json_str:
                self.logger.warning("No JSON found in response, using fallback scoring")
                return self._fallback_scoring(templates)
            
            # Parse JSON
            result = json.loads(json_str)
            
            if "scored_templates" not in result:
                self.logger.warning("Invalid JSON structure, using fallback scoring")
                return self._fallback_scoring(templates)
            
            return result["scored_templates"]
            
        except Exception as e:
            self.logger.error(f"Error parsing scoring response: {e}")
            return self._fallback_scoring(templates)
    
    def _extract_json_enhanced(self, response: str) -> Optional[str]:
        """Enhanced JSON extraction with multiple strategies"""
        try:
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    # Validate JSON
                    json.loads(json_str)
                    return json_str
            
            # Strategy 2: Find first complete JSON object with proper brace matching
            if "{" in response and "}" in response:
                brace_count = 0
                start_pos = -1
                
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos >= 0:
                            # Found complete JSON object
                            json_str = response[start_pos:i+1]
                            # Try to clean and validate
                            try:
                                json.loads(json_str)
                                return json_str
                            except json.JSONDecodeError:
                                json_str = self._clean_json_string(json_str)
                                json.loads(json_str)
                                return json_str
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                # Try to clean and validate
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    json_str = self._clean_json_string(json_str)
                    json.loads(json_str)
                    return json_str
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting JSON: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove common issues"""
        import re
        
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        
        # Fix common quote issues
        json_str = re.sub(r'(?<!\\)"([^"]*)"', r'"\1"', json_str)
        
        return json_str
    
    def _fallback_scoring(self, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback scoring when LLM fails"""
        scored_templates = []
        
        for template in templates:
            scored_template = {
                "template": template,
                "score": 0.5,  # Default medium score
                "reasoning": "Fallback scoring applied due to LLM parsing error",
                "suitability_level": "medium"
            }
            scored_templates.append(scored_template)
        
        return scored_templates 
 
 