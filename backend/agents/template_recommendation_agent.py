from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class TemplateRecommendationAgent(BaseAgent):
    """Focused agent with single responsibility: Recommend templates based on requirements"""
    
    def __init__(self):
        system_message = """You are a Template Recommendation Agent specialized in:
1. Analyzing requirements and matching them to available templates
2. Scoring templates based on multiple criteria
3. Providing detailed reasoning for recommendations
4. Suggesting alternatives when exact matches aren't available

You focus ONLY on template recommendation and scoring. You do not analyze requirements or generate questions."""
        
        super().__init__("TemplateRecommendation", system_message)
        self.tool_utility = ToolUtility("template_recommendation_agent")
        self.keyword_manager = KeywordManager()
    
    def recommend_templates(self, requirements: Dict[str, Any], category: str = None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Single job: Recommend templates based on requirements"""
        
        # Get templates from database
        templates = self._get_templates_from_database(requirements, category)
        print(f"DEBUG: Templates after database fetch: {len(templates)} templates")
        
        if not templates:
            print("DEBUG: No templates found, returning empty list")
            return []
        
        # Let the LLM do the scoring and recommendation
        scored_templates = self._score_templates_with_llm(requirements, templates, context)
        print(f"DEBUG: Scored templates result: {len(scored_templates)} templates")
        
        return scored_templates[:self.keyword_manager.get_default_values()["max_templates"]]
    
    def _get_templates_from_database(self, requirements: Dict[str, Any], category: str = None) -> List[Dict[str, Any]]:
        """Get templates from database based on requirements"""
        templates = []
        
        # DEBUG: Print what we received
        print(f"DEBUG: _get_templates_from_database called with:")
        print(f"  requirements type: {type(requirements)}")
        print(f"  requirements content: {requirements}")
        print(f"  category parameter: {category}")
        
        # Get category from requirements or use provided category
        target_category = requirements.get("page_type") or category or self.keyword_manager.get_default_values()["fallback_category"]
        print(f"Searching for templates in category: {target_category}")
        
        # Get templates for the target category
        result = self.tool_utility.call_function("get_templates_by_category", {"category": target_category, "limit": 20})
        if result.get("success"):
            templates.extend(result.get("templates", []))
            print(f"Found {len(result.get('templates', []))} templates in {target_category}")
        
        # If no templates found, try related categories
        if not templates:
            related_categories = self.keyword_manager.get_related_categories_for(target_category)
            print(f"No templates found in {target_category}, trying related categories: {related_categories}")
            
            for cat in related_categories:
                cat_result = self.tool_utility.call_function("get_templates_by_category", {"category": cat, "limit": 10})
                if cat_result.get("success") and cat_result.get("templates"):
                    templates.extend(cat_result.get("templates", []))
                    print(f"Found {len(cat_result.get('templates', []))} templates in related category {cat}")
        
        # If still no templates, try all available categories
        if not templates:
            print("No templates found in related categories, trying all available categories")
            categories_result = self.tool_utility.call_function("get_available_categories", {})
            if categories_result.get("success"):
                available_categories = categories_result.get("categories", [])
                for cat in available_categories[:3]:  # Try first 3 categories
                    if cat != target_category and cat not in self.keyword_manager.get_related_categories_for(target_category):
                        cat_result = self.tool_utility.call_function("get_templates_by_category", {"category": cat, "limit": 5})
                        if cat_result.get("success") and cat_result.get("templates"):
                            templates.extend(cat_result.get("templates", []))
                            print(f"Found {len(cat_result.get('templates', []))} templates in fallback category {cat}")
        
        print(f"Total templates found: {len(templates)}")
        return templates
    
    def _score_templates_with_llm(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Use LLM to score templates based on requirements"""
        
        print(f"DEBUG: Starting LLM scoring with {len(templates)} templates")
        prompt = self._build_scoring_prompt(requirements, templates, context)
        response = self._call_claude_with_tools(prompt)
        print(f"DEBUG: LLM response length: {len(response)} characters")
        print(f"DEBUG: LLM response preview: {response[:200]}...")
        
        result = self._parse_scoring_response(response, templates)
        print(f"DEBUG: Parsed result: {len(result)} templates")
        return result
    
    def _build_scoring_prompt(self, requirements: Dict[str, Any], templates: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for LLM-based template scoring"""
        
        # Extract key requirements
        page_type = requirements.get("page_type", "landing")
        style_prefs = requirements.get("style_preferences", [])
        key_features = requirements.get("key_features", [])
        target_audience = requirements.get("target_audience", "general users")
        ui_specs = requirements.get("ui_specifications", {})
        
        # Build template information
        template_info = "AVAILABLE TEMPLATES:\n"
        for i, template in enumerate(templates, 1):
            name = template.get("name", f"Template {i}")
            description = template.get("description", "No description")
            tags = template.get("tags", [])
            category = template.get("category", "unknown")
            
            template_info += f"""
{i}. {name}
   Category: {category}
   Description: {description}
   Tags: {', '.join(tags) if tags else 'None'}
   Template ID: {template.get('template_id', 'N/A')}
"""
        
        prompt = f"""
You are an expert UI template recommendation system. Score these templates based on the user requirements.

USER REQUIREMENTS:
- Page Type: {page_type}
- Style Preferences: {', '.join(style_prefs)}
- Key Features: {', '.join(key_features)}
- Target Audience: {target_audience}
- UI Specifications: {json.dumps(ui_specs, indent=2)}

{template_info}

EVALUATION CRITERIA:
1. Category Match (30% weight): How well does the template serve the intended page type?
2. Style Alignment (25% weight): Does the visual style match user preferences?
3. Component Coverage (20% weight): Does it include required functional elements?
4. Brand Consistency (15% weight): Does it align with the target audience?
5. Technical Quality (10% weight): Is the implementation solid and maintainable?

 TASK:
 Score each template and provide detailed reasoning. Return ONLY a JSON array with this structure and NO extra text before or after:

[
    {{
        "template_id": "string (from template database)",
        "template_name": "string",
        "overall_score": 0.85,
        "category_match": 0.9,
        "style_alignment": 0.8,
        "component_coverage": 0.7,
        "brand_consistency": 0.85,
        "technical_quality": 0.8,
        "detailed_reasoning": "Comprehensive explanation of why this template is recommended",
        "strengths": ["List of specific strengths"],
        "considerations": ["List of potential considerations"],
        "suitability_level": "high|medium|low"
    }}
]

IMPORTANT:
- Score from 0.0 to 1.0 for each criterion
- Provide detailed reasoning for each recommendation
- Consider both explicit matches and implicit design principles
- Sort by overall_score (highest first)
"""
        
        return prompt
    
    def _call_claude_with_tools(self, prompt: str) -> str:
        """Call Claude with tool calling capabilities"""
        try:
            client = self.claude_client
            messages = [{"role": "user", "content": prompt}]
            
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
            print(f"DEBUG: Template Recommendation Agent LLM Response: {response.content[0].text[:500]}...")
            if len(response.content[0].text) > 500:
                print(f"DEBUG: Full Template Recommendation Response: {response.content[0].text}")
            
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
                    Based on the tool results below, please provide your final template recommendations:

                    TOOL RESULTS:
                    {json.dumps(tool_results, indent=2)}

                    ORIGINAL PROMPT:
                    {prompt}

                    Please provide your template recommendations in the requested JSON format.
                    """
                    
                    final_response = client.messages.create(
                        model=self.model,
                        max_tokens=8000,
                        messages=[{"role": "user", "content": tool_response_prompt}]
                    )
                    
                    # Debug: Log final LLM response after tool calls
                    print(f"DEBUG: Template Recommendation Agent Final Response: {final_response.content[0].text[:500]}...")
                    if len(final_response.content[0].text) > 500:
                        print(f"DEBUG: Full Template Recommendation Final Response: {final_response.content[0].text}")
                    
                    return final_response.content[0].text
            
            return response.content[0].text
            
        except Exception as e:
            print(f"ERROR: Error calling Claude with tools: {e}")
            return f"Error: {str(e)}"
    
    def _parse_scoring_response(self, response: str, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the LLM response and convert to the expected format"""
        
        print(f"DEBUG: Parsing response with {len(templates)} templates available")
        try:
            # Prefer robust base extractor first
            extracted = self._extract_json_from_text(response)
            if extracted is None:
                # Preserve legacy extractor behavior for arrays in strings
                json_str = self._extract_json_from_response(response)
                if not json_str:
                    print("No JSON found in response, using fallback scoring")
                    fallback_result = self._fallback_scoring(templates)
                    print(f"DEBUG: Fallback scoring returned {len(fallback_result)} templates")
                    return fallback_result
                print(f"DEBUG: Extracted JSON: {json_str[:200]}...")
                recommendations = json.loads(json_str)
            else:
                recommendations = extracted
            print(f"DEBUG: Parsed JSON has {len(recommendations)} recommendations")
            
            scored_templates = []
            
            for rec in recommendations:
                template_id = rec.get("template_id")
                template_name = rec.get("template_name")
                
                # Find the corresponding template
                template = None
                for t in templates:
                    if (str(t.get("template_id")) == template_id or 
                        t.get("name") == template_name):
                        template = t
                        break
                
                if template:
                    scored_templates.append({
                        "template": template,
                        "score": rec.get("overall_score", 0.0),
                        "reasoning": rec.get("detailed_reasoning", ""),
                        "strengths": rec.get("strengths", []),
                        "considerations": rec.get("considerations", []),
                        "suitability_level": rec.get("suitability_level", "medium"),
                        "detailed_scores": {
                            "category_match": rec.get("category_match", 0.0),
                            "style_alignment": rec.get("style_alignment", 0.0),
                            "component_coverage": rec.get("component_coverage", 0.0),
                            "brand_consistency": rec.get("brand_consistency", 0.0),
                            "technical_quality": rec.get("technical_quality", 0.0)
                        }
                    })
            
            # Sort by score (highest first)
            scored_templates.sort(key=lambda x: x["score"], reverse=True)
            
            return scored_templates
            
        except Exception as e:
            print(f"ERROR: Error parsing scoring response: {e}")
            return self._fallback_scoring(templates)
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON using multiple strategies"""
        
        # Strategy 1: Find JSON array (most common format)
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group())
                return json_match.group()
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Find JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group())
                return json_match.group()
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Look for specific patterns like "recommendations:" or "templates:"
        patterns = [
            r'recommendations:\s*(\[.*?\])',
            r'templates:\s*(\[.*?\])',
            r'scored_templates:\s*(\[.*?\])',
            r'results:\s*(\[.*?\])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    json.loads(match.group(1))
                    return match.group(1)
                except json.JSONDecodeError:
                    pass
        
        # Strategy 4: Try to find JSON between markdown code blocks
        code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
        if code_block_match:
            try:
                json.loads(code_block_match.group(1))
                return code_block_match.group(1)
            except json.JSONDecodeError:
                pass
        
        # Strategy 5: Look for JSON after common prefixes
        prefix_patterns = [
            r'here are the scored templates:\s*(\[.*?\])',
            r'here are my recommendations:\s*(\[.*?\])',
            r'template scores:\s*(\[.*?\])',
            r'final recommendations:\s*(\[.*?\])'
        ]
        
        for pattern in prefix_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    json.loads(match.group(1))
                    return match.group(1)
                except json.JSONDecodeError:
                    pass
        
        # Strategy 6: Try to extract and fix common JSON issues
        # Look for array-like structure and try to fix common issues
        array_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if array_match:
            potential_json = array_match.group()
            # Try to fix common issues
            fixed_json = self._fix_common_json_issues(potential_json)
            if fixed_json:
                try:
                    json.loads(fixed_json)
                    return fixed_json
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def _fix_common_json_issues(self, json_str: str) -> Optional[str]:
        """Try to fix common JSON formatting issues"""
        try:
            # Remove trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Fix unquoted keys
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Remove any non-ASCII characters that might cause issues
            json_str = ''.join(char for char in json_str if ord(char) < 128)
            
            return json_str
        except Exception:
            return None
    
    def _fallback_scoring(self, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple fallback scoring if LLM parsing fails"""
        scored_templates = []
        for template in templates:
            # Simple fallback scoring
            score = 0.5  # Default score
            if template.get("category") == "landing":
                score += 0.2
            if template.get("tags"):
                score += 0.1
            
            scored_templates.append({
                "template": template,
                "score": score,
                "reasoning": "Fallback scoring applied due to LLM parsing error",
                "suitability_level": "medium"
            })
        
        scored_templates.sort(key=lambda x: x["score"], reverse=True)
        return scored_templates 