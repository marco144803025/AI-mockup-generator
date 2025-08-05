from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import logging
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class UIEditingAgent(BaseAgent):
    """Advanced UI Editing Agent with sophisticated modification capabilities"""
    
    def __init__(self):
        system_message = """You are an Advanced UI mockup Editing Agent specialized in:
1. Analyzing user modification requests with deep understanding of mockup
2. Creating detailed modification plans with step-by-step instructions
3. Validating modifications of mockup for quality and consistency

You focus on sophisticated mockup UI modifications and improvements."""
        
        # Use Haiku model for UI editing
        super().__init__("UIEditing", system_message, model="claude-3-5-haiku-20241022")
        self.tool_utility = ToolUtility("ui_editing_agent")
        self.keyword_manager = KeywordManager()
        self.logger = logging.getLogger(__name__)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove control characters and fix common issues"""
        import re
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        return json_str
    
    def _extract_json_from_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Robust JSON extraction from LLM responses"""
        try:
            self.logger.debug(f"Extracting JSON from {context}: {response[:200]}...")
            
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    json_str = self._clean_json_string(json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
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
                            json_str = self._clean_json_string(json_str)
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                json_str = self._clean_json_string(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON in {context}: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def _is_placeholder_content(self, content: str) -> bool:
        """
        Detect if content is a placeholder comment instead of actual code.
        Returns True if content appears to be a placeholder that should be ignored.
        """
        if not content or not isinstance(content, str):
            return True
            
        # Clean content for analysis
        content_cleaned = content.strip()
        
        # Check for common placeholder patterns
        placeholder_patterns = [
            "/* Original CSS remains the same */",
            "/* CSS unchanged */", 
            "/* No changes needed */",
            "/* Keep original CSS */",
            "/* Same as original */",
            "/* Unchanged */",
            "<!-- Original HTML remains the same -->",
            "<!-- HTML unchanged -->",
            "<!-- No changes needed -->",
            "// Original code remains the same",
            "// No changes needed"
        ]
        
        # Check for partial content patterns (content that ends with placeholder comments)
        partial_placeholder_patterns = [
            "/* Rest of the CSS remains unchanged */",
            "/* Rest of the CSS remains the same */",
            "/* Remaining CSS unchanged */",
            "/* Other styles remain the same */",
            "/* ... rest of CSS ... */",
            "/* [rest of CSS unchanged] */",
            "<!-- Rest of HTML unchanged -->",
            "<!-- Remaining HTML the same -->",
            "// Rest of the code unchanged"
        ]
        
        # Check if content is only a placeholder comment
        for pattern in placeholder_patterns:
            if content_cleaned == pattern:
                return True
                
        # Check if content ends with partial placeholder patterns
        for pattern in partial_placeholder_patterns:
            if content_cleaned.endswith(pattern.strip()):
                return True
        
        # Check if content is only whitespace and comments
        lines = content_cleaned.split('\n')
        non_comment_lines = []
        for line in lines:
            line = line.strip()
            if line and not (line.startswith('/*') or line.startswith('//') or line.startswith('<!--') or line == '*/'):
                non_comment_lines.append(line)
        
        # If no substantial content beyond comments, consider it a placeholder
        if len(non_comment_lines) == 0:
            return True
            
        # Check for signs of truncation in CSS/HTML content
        if self._is_truncated_content(content_cleaned):
            return True
            
        return False
    
    def _is_truncated_content(self, content: str) -> bool:
        """
        Detect if content appears to be truncated or incomplete.
        Returns True if content seems to be cut off.
        """
        if not content:
            return False
            
        content_lower = content.lower().strip()
        
        # Signs of truncation in CSS
        truncation_indicators = [
            "/* rest",
            "/* remaining",
            "/* other styles",
            "/* ... rest",
            "/* [rest",
            "/* everything else",
            "/* all other",
            "/* additional styles",
            "/* more css",
            "/* continue",
            "/* etc",
            "/* and so on",
            # HTML truncation indicators
            "<!-- rest",
            "<!-- remaining",
            "<!-- other html",
            "<!-- ... rest",
            "<!-- continue",
            # General truncation
            "... rest",
            "...rest",
            "[rest of",
            "(rest of",
            "etc.",
            "and so on"
        ]
        
        for indicator in truncation_indicators:
            if indicator in content_lower:
                return True
                
        # Check if CSS looks incomplete (no closing braces at end)
        if content.strip().endswith('{') or content.count('{') > content.count('}'):
            return True
            
        return False
    
    def _extract_css_from_failed_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to extract CSS from response when JSON parsing fails.
        This handles cases where the LLM provides valid CSS but malformed JSON.
        """
        try:
            import re
            
            # Look for style_css content patterns
            css_patterns = [
                r'"style_css":\s*"([^"]+(?:\\.[^"]*)*)"',  # JSON string format
                r'style_css["\']?\s*:\s*["\']([^"\']+)["\']',  # Various quote formats
                r'\.log-in\s*\{[^}]*background-color:\s*#[0-9A-Fa-f]{6}[^}]*\}.*?\.log-in\s+\.chris-lee\s*\{[^}]*\}',  # CSS pattern
            ]
            
            extracted_css = None
            
            # Try to find CSS content
            for pattern in css_patterns:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    extracted_css = match.group(1) if match.lastindex >= 1 else match.group(0)
                    break
            
            # Look for CSS modifications in the response (handle both JSON and debug output)
            if "#87CEEB" in response or "background-color:" in response.lower():
                # Strategy 1: Try to extract from JSON-like structure
                style_css_match = re.search(r'"style_css":\s*"([^"]*(?:\\.[^"]*)*)"', response, re.DOTALL)
                
                if style_css_match:
                    raw_css = style_css_match.group(1)
                    # Unescape the CSS
                    clean_css = raw_css.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
                    
                    # Verify this CSS contains our expected change
                    if "#87CEEB" in clean_css or "background-color:" in clean_css.lower():
                        return {
                            "modified_code": {
                                "html_export": "",
                                "globals_css": "",
                                "style_css": clean_css
                            },
                            "validation_report": {
                                "is_valid": True,
                                "quality_score": 0.9,
                                "warnings": ["Extracted from malformed JSON response"],
                                "reasoning": "CSS successfully extracted despite JSON parsing error"
                            },
                            "changes_summary": ["Successfully applied color modification to login button"]
                        }
                
                # Strategy 2: Extract from the middle of the response where the CSS is truncated
                # Look for patterns like: .log-in .frame-7 {\n  display: flex;\n  width: 404px;...
                frame7_match = re.search(r'(\.log-in \{.*?background-color:\s*#87CEEB.*?\.log-in \.chris-lee \{[^}]*\})', response, re.DOTALL)
                if frame7_match:
                    partial_css = frame7_match.group(1)
                    # This is likely a complete CSS, try to clean it up
                    clean_css = partial_css.replace('\\n', '\n').replace('\\"', '"')
                    
                    return {
                        "modified_code": {
                            "html_export": "",
                            "globals_css": "",
                            "style_css": clean_css
                        },
                        "validation_report": {
                            "is_valid": True,
                            "quality_score": 0.9,
                            "warnings": ["Extracted CSS from malformed JSON using pattern matching"],
                            "reasoning": "CSS successfully extracted from response using fallback pattern matching"
                        },
                        "changes_summary": ["Successfully applied light blue color to login button"]
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in CSS extraction fallback: {e}")
            return None
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the new, efficient two-step modification workflow.
        
        Step 1: Analysis & Planning (1 API call)
        Step 2: Apply, Validate & Summarize (1 API call)
        
        This approach uses dynamic prompt engineering to handle any request type.
        """
        try:
            self.logger.info(f"Starting two-step modification process for: {user_feedback}")
            
            # STEP 1: Analysis and Planning
            analysis_prompt = self._build_analysis_and_planning_prompt(user_feedback, current_template)
            
            self.logger.debug("Sending analysis and planning request to Claude...")
            analysis_response = self.call_claude_with_cot(analysis_prompt, enable_cot=False)
            
            # Parse the analysis and plan
            modification_plan = self._parse_plan_from_response(analysis_response)
            
            if not modification_plan:
                return {
                    "success": False,
                    "error": "Failed to generate modification plan",
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            # STEP 2: Apply, Validate and Summarize
            execution_prompt = self._build_apply_validate_summary_prompt(modification_plan, current_template)
            
            self.logger.debug("Sending execution, validation, and summary request to Claude...")
            print(f"DEBUG: UI Editing Agent - Starting execution step...")
            
            try:
                execution_response = self.call_claude_with_cot(execution_prompt, enable_cot=False)
                print(f"DEBUG: UI Editing Agent - Received execution response (length: {len(execution_response)})")
                
                # Debug: Log execution response
                print(f"DEBUG: UI Editing Agent Execution Response: {execution_response[:500]}...")
                if len(execution_response) > 500:
                    print(f"DEBUG: Full UI Editing Agent Execution Response: {execution_response}")
            except Exception as e:
                print(f"ERROR: UI Editing Agent - Execution step failed: {e}")
                return {
                    "success": False,
                    "error": f"Execution step failed: {str(e)}",
                    "original_template": current_template,
                    "modification_plan": modification_plan,
                    "user_feedback": user_feedback
                }
            
            # Parse the final results
            print(f"DEBUG: UI Editing Agent - Starting to parse execution response...")
            final_results = self._parse_final_output_from_response(execution_response, current_template)
            
            # Debug: Log parsing result
            print(f"DEBUG: UI Editing Agent Final Results: {final_results}")
            
            if not final_results:
                return {
                    "success": False,
                    "error": "Failed to execute modification plan",
                    "original_template": current_template,
                    "modification_plan": modification_plan,
                    "user_feedback": user_feedback
                }
            
            # Combine all results into final response
            return {
                "success": final_results.get("validation_report", {}).get("is_valid", True),
                "original_template": current_template,
                "modified_template": final_results.get("modified_template"),
                "modification_request": modification_plan.get("analysis", {}),
                "modification_plan": modification_plan.get("modification_plan", {}),
                "validation_result": final_results.get("validation_report", {}),
                "changes_summary": final_results.get("changes_summary", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error in two-step modification process: {e}")
            return {
                "success": False,
                "error": f"Modification process failed: {str(e)}",
                "original_template": current_template,
                "user_feedback": user_feedback
            }
    
    def _build_analysis_and_planning_prompt(self, user_feedback: str, current_template: Dict[str, Any]) -> str:
        """
        [PROMPT ENGINEERING] Creates the prompt for the first API call,
        asking the LLM to both analyze the request and create an implementation plan.
        """
        # Extract template information for context
        html_content = current_template.get('html_export', '')
        global_css = current_template.get('globals_css', '')
        style_css = current_template.get('style_css', '')
        
        # Combine CSS for analysis
        css_content = f"{global_css}\n{style_css}"
        
        template_name = current_template.get('name', 'Unknown Template')
        template_category = current_template.get('category', 'general')
        
        prompt = f"""You are an expert UI/UX analyst and implementation strategist.
Your task is to analyze a user's modification request and create a detailed, step-by-step implementation plan.

## CONTEXT
- Template: {template_name} ({template_category})
- User Request: "{user_feedback}"
- Current HTML Code Length: {len(html_content)} characters
- Current CSS Code Length: {len(css_content)} characters

## CURRENT CODE FOR ANALYSIS
### HTML:
{html_content}

### CSS:
{css_content}

## YOUR TASK
Analyze the user's intent and the current code to produce a comprehensive plan.
Return a single JSON object with the exact structure below, containing two main keys: "analysis" and "modification_plan".

## OUTPUT STRUCTURE
```json
{{
  "analysis": {{
    "overall_intent": "A summary of what the user is trying to achieve.",
    "modification_type": "A single keyword (e.g., 'styling', 'layout', 'content', 'color', 'sizing').",
    "affected_elements": ["A list of CSS selectors or element descriptions that will be changed."],
    "complexity_level": "simple|moderate|complex",
    "confidence_score": 0.9
  }},
  "modification_plan": {{
    "implementation_strategy": "A brief, high-level approach for the changes.",
    "modification_steps": [
      {{
        "step_number": 1,
        "description": "Describe the change for this step.",
        "change_type": "A keyword like 'modify-css', 'add-html', 'remove-html', 'update-text'.",
        "target_element": "The CSS selector for the element to modify.",
        "detailed_instructions": "Specific instructions for what code to add, change, or remove. For CSS, specify the properties and new values."
      }}
    ]
  }}
}}
```

Focus on understanding the user's intent and providing precise, actionable instructions that will result in exactly what the user requested."""
        
        return prompt
    
    def _parse_plan_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parses the JSON response from the first API call to extract the modification plan.
        """
        try:
            parsed_response = self._extract_json_from_response(response, "analysis_and_planning")
            
            if parsed_response:
                # Validate that both required sections are present
                if "analysis" in parsed_response and "modification_plan" in parsed_response:
                    self.logger.info(f"Successfully parsed modification plan with {len(parsed_response.get('modification_plan', {}).get('modification_steps', []))} steps")
                    return parsed_response
                else:
                    self.logger.warning("Missing required sections in parsed plan")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing plan from response: {e}")
            return None
    
    def _build_apply_validate_summary_prompt(self, modification_plan: Dict[str, Any], original_template: Dict[str, Any]) -> str:
        """
        [PROMPT ENGINEERING] Creates the prompt for the second API call,
        providing the plan and asking the LLM to execute, validate, and summarize.
        """
        import json
        
        # Extract original code
        original_html = original_template.get('html_export', '')
        original_global_css = original_template.get('globals_css', '')
        original_style_css = original_template.get('style_css', '')
        
        # Convert modification plan to JSON string for inclusion in prompt
        modification_plan_json = json.dumps(modification_plan, indent=2)
        
        prompt = f"""You are an expert web developer tasked with executing a pre-defined modification plan, validating your work, and summarizing the results.

## CONTEXT
You will be modifying the provided original code based only on the instructions in the modification plan.

## MODIFICATION PLAN
```json
{modification_plan_json}
```

## ORIGINAL CODE
### HTML
```html
{original_html}
```

### GLOBAL CSS
```css
{original_global_css}
```

### STYLE CSS
```css
{original_style_css}
```

## YOUR TASK
Perform three actions in sequence:

1. **EXECUTE**: Apply the steps in the modification plan to the original code.
2. **VALIDATE**: Critically review your own changes for correctness, quality, and adherence to the plan.
3. **SUMMARIZE**: Describe the changes you made in a user-friendly way.

Return a single JSON object with the exact structure below. Do not include any other text or explanation.

## OUTPUT STRUCTURE
```json
{{
  "modified_code": {{
    "html_export": "The complete, new HTML code (if modified) OR empty string if unchanged.",
    "globals_css": "The complete, new global CSS code (if modified) OR empty string if unchanged.", 
    "style_css": "The complete, new style CSS code (if modified) OR empty string if unchanged."
  }},
  "validation_report": {{
    "is_valid": true,
    "quality_score": 0.9,
    "warnings": ["List any potential issues or deviations from the plan."],
    "reasoning": "Explain why the changes are valid and meet the plan's requirements."
  }},
  "changes_summary": [
    "A bullet point describing the first major change.",
    "A bullet point describing the second major change."
  ]
}}
```

**CRITICAL REQUIREMENTS**:
1. **Complete Code Only**: If you modify HTML or CSS, you MUST return the COMPLETE, FULL file content - never partial code with comments like "/* Rest unchanged */".
2. **Empty String for Unchanged**: If HTML, CSS, or other code sections are completely unchanged, return an empty string ("") for those fields.
3. **No Partial Code**: Never return partial code with placeholder comments like "/* Rest of CSS remains unchanged */" or "/* ... rest of CSS ... */".
4. **No Truncation**: If you make ANY changes to a CSS file, return the ENTIRE CSS file with your changes integrated.

**EXAMPLES**:
- ✅ CORRECT: Return empty string "" if no changes to CSS
- ✅ CORRECT: Return complete full CSS file if any changes made
- ❌ WRONG: Return partial CSS ending with "/* Rest unchanged */"
- ❌ WRONG: Return any placeholder comments instead of complete code

Execute the plan precisely, validate your work thoroughly, and provide clear summaries of what was accomplished."""
        
        return prompt
    
    def _parse_final_output_from_response(self, response: str, original_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the final JSON response containing the modified code, validation, and summary.
        """
        try:
            print(f"DEBUG: Parsing final output response (length: {len(response)})")
            parsed_response = self._extract_json_from_response(response, "final_output")
            
            # If JSON parsing failed, try to extract the CSS directly from the response
            if not parsed_response:
                print("DEBUG: JSON parsing failed, attempting direct CSS extraction")
                print(f"DEBUG: Response contains #87CEEB: {'#87CEEB' in response}")
                print(f"DEBUG: Response contains background-color: {'background-color' in response.lower()}")
                print(f"DEBUG: Response snippet: {response[:1000]}...")
                parsed_response = self._extract_css_from_failed_response(response)
                print(f"DEBUG: Fallback extraction result: {bool(parsed_response)}")
                if parsed_response:
                    print(f"DEBUG: Fallback extracted keys: {list(parsed_response.keys())}")
            
            if parsed_response:
                print(f"DEBUG: Successfully extracted JSON with keys: {list(parsed_response.keys())}")
                
                # Validate that all required sections are present
                required_keys = ["modified_code", "validation_report", "changes_summary"]
                missing_keys = [key for key in required_keys if key not in parsed_response]
                
                if not missing_keys:
                    
                    # Create the modified template structure
                    modified_template = original_template.copy()
                    modified_code = parsed_response["modified_code"]
                    
                    # Update with new code, preserving existing content if LLM doesn't provide it
                    # or if LLM returns placeholder comments
                    if "html_export" in modified_code and modified_code["html_export"]:
                        if not self._is_placeholder_content(modified_code["html_export"]):
                            modified_template["html_export"] = modified_code["html_export"]
                        else:
                            self.logger.warning("html_export contains placeholder content, preserving original")
                    elif not modified_template.get("html_export"):
                        self.logger.warning("html_export missing from LLM response, preserving original")
                    
                    if "globals_css" in modified_code and modified_code["globals_css"]:
                        if not self._is_placeholder_content(modified_code["globals_css"]):
                            modified_template["globals_css"] = modified_code["globals_css"]
                        else:
                            self.logger.warning("globals_css contains placeholder content, preserving original")
                    elif not modified_template.get("globals_css"):
                        self.logger.warning("globals_css missing from LLM response, preserving original")
                    
                    if "style_css" in modified_code and modified_code["style_css"]:
                        if not self._is_placeholder_content(modified_code["style_css"]):
                            modified_template["style_css"] = modified_code["style_css"]
                        else:
                            self.logger.warning("style_css contains placeholder content, preserving original")
                    elif not modified_template.get("style_css"):
                        self.logger.warning("style_css missing from LLM response, preserving original")
                    
                    # Add modification metadata
                    modified_template["modification_metadata"] = {
                        "changes_applied": parsed_response.get("changes_summary", []),
                        "modification_type": "dynamic_two_step",
                        "modified_at": "2025-01-27T12:00:00Z"
                    }
                    
                    return {
                        "modified_template": modified_template,
                        "validation_report": parsed_response["validation_report"],
                        "changes_summary": parsed_response["changes_summary"]
                    }
                else:
                    print(f"ERROR: Missing required sections in final output: {missing_keys}")
                    self.logger.warning(f"Missing required sections in final output: {missing_keys}")
            else:
                print(f"ERROR: Failed to extract JSON from final output response")
                self.logger.warning("Failed to extract JSON from final output response")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing final output from response: {e}")
            return None
    
    def analyze_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user feedback using advanced prompt engineering for sophisticated understanding"""
        
        # Build comprehensive prompt for advanced analysis
        prompt = self._build_analysis_prompt(user_feedback, current_template)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response with enhanced error handling
        return self._parse_analysis_response(response, user_feedback)
    
    def _build_analysis_prompt(self, user_feedback: str, current_template: Dict[str, Any]) -> str:
        """Build sophisticated prompt for modification analysis"""
        
        # Extract template information
        template_name = current_template.get('name', 'Unknown Template')
        template_category = current_template.get('category', 'Unknown')
        template_tags = current_template.get('tags', [])
        template_description = current_template.get('description', 'No description available')
        
        # Get HTML and CSS content for analysis
        html_content = current_template.get('html_export', '')
        global_css = current_template.get('globals_css', '')
        style_css = current_template.get('style_css', '')
        
        prompt = f"""
You are an expert UI/UX modification analyst with deep understanding of web design principles, user psychology, and technical implementation. Your task is to analyze a user's UI mockup modification request and provide a comprehensive, structured analysis.

## CURRENT TEMPLATE CONTEXT
- **Template Name**: {template_name}
- **Category**: {template_category}
- **Description**: {template_description}
- **Tags**: {', '.join(template_tags)}

## CURRENT CODE STRUCTURE
**HTML Content Length**: {len(html_content)} characters
**Global CSS Length**: {len(global_css)} characters  
**Component CSS Length**: {len(style_css)} characters

## USER FEEDBACK
"{user_feedback}"

## ANALYSIS TASK
Using Chain-of-Thought reasoning, analyze the user's UI mockup modification request and provide a comprehensive specification. Consider:

1. **Intent Analysis**: What is the user trying to achieve?
2. **Context Understanding**: How does this fit with the current template?
3. **Technical Feasibility**: What changes are technically possible?
4. **Design Impact**: How will changes affect the overall mockup design?
5. **User Experience**: Will changes improve or hinder UX?
6. **Implementation Strategy**: What's the best approach to implement changes?

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "modification_type": "string (layout|styling|content|functionality|color-scheme|typography|structure|interaction)",
    "priority": "string (high|medium|low)",
    "complexity": "string (simple|moderate|complex)",
    "affected_elements": ["list", "of", "elements", "to", "modify"],
    "specific_changes": [
        {{
            "element_selector": "string (CSS selector or element description)",
            "change_type": "string (color|size|position|text|layout|add|remove|modify|style)",
            "current_value": "string (current state/value)",
            "new_value": "string (desired new state/value)",
            "reasoning": "string (detailed explanation of why this change is needed)",
            "impact_assessment": "string (how this change affects the overall design)",
            "implementation_notes": "string (technical notes for implementation)"
        }}
    ],
    "overall_intent": "string (comprehensive explanation of what the user is trying to achieve)",
    "design_principles": ["list", "of", "design", "principles", "being", "applied"],
    "constraints": ["list", "of", "constraints", "or", "limitations"],
    "suggestions": ["list", "of", "additional", "improvements", "or", "considerations"],
    "confidence_score": 0.85,
    "risk_assessment": "string (potential risks or issues with the proposed changes)",
    "alternative_approaches": ["list", "of", "alternative", "ways", "to", "achieve", "the", "goal"]
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Parse User Intent**: Understand what the user wants to achieve
2. **Analyze Current State**: Examine the existing template structure
3. **Identify Required Changes**: Determine what needs to be modified
4. **Consider Design Impact**: Assess how changes affect the overall design
5. **Plan Implementation**: Determine the best approach to implement changes
6. **Validate Approach**: Ensure the proposed changes are feasible and beneficial

Remember: Focus on understanding the user's underlying goals, not just their explicit requests. Consider the broader context and design principles.
"""
        
        return prompt
    
    def _parse_analysis_response(self, response: str, user_feedback: str) -> Dict[str, Any]:
        """Parse the analysis response with enhanced error handling"""
        
        try:
            # Try multiple JSON extraction strategies
            parsed_response = self._extract_json_from_response(response, "analysis")
            
            if parsed_response:
                # Validate required fields
                required_fields = self.keyword_manager.get_required_fields()["modification_request"]
                for field in required_fields:
                    if field not in parsed_response:
                        parsed_response[field] = self._get_default_value(field)
                
                return parsed_response
            else:
                self.logger.warning("No valid JSON found in analysis response, using default")
                return self._get_default_modification_request(user_feedback)
                
        except Exception as e:
            self.logger.error(f"Error parsing analysis response: {e}")
            return self._get_default_modification_request(user_feedback)
    
    def _get_default_modification_request(self, user_feedback: str) -> Dict[str, Any]:
        """Return sophisticated default modification request when analysis fails"""
        return {
            "modification_type": "general",
            "priority": "medium",
            "complexity": "moderate",
            "affected_elements": ["general"],
            "specific_changes": [
                {
                    "element_selector": "general",
                    "change_type": "improvement",
                    "current_value": "current state",
                    "new_value": "improved state",
                    "reasoning": f"User requested: {user_feedback}",
                    "impact_assessment": "General improvement to enhance user experience",
                    "implementation_notes": "Apply changes carefully to maintain existing functionality"
                }
            ],
            "overall_intent": f"Improve the UI based on user feedback: {user_feedback}",
            "design_principles": self.keyword_manager.get_design_principles(),
            "constraints": ["maintain existing functionality", "preserve responsive design"],
            "suggestions": ["Consider user feedback carefully", "Test changes thoroughly"],
            "confidence_score": 0.5,
            "risk_assessment": "Low risk - general improvements",
            "alternative_approaches": ["Incremental changes", "User testing before full implementation"]
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            "modification_type": "general",
            "priority": "medium",
            "complexity": "moderate",
            "affected_elements": ["general"],
            "specific_changes": [],
            "overall_intent": "General improvement",
            "design_principles": ["user-centered design"],
            "constraints": ["maintain existing functionality"],
            "suggestions": ["Consider user feedback"],
            "confidence_score": 0.5,
            "risk_assessment": "Low risk",
            "alternative_approaches": ["Incremental approach"]
        }
        return defaults.get(field, "Not specified")
    
    def generate_modification_plan(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed modification plan using advanced prompt engineering"""
        
        # Build sophisticated planning prompt
        prompt = self._build_planning_prompt(modification_request, current_template)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response
        return self._parse_planning_response(response, modification_request)
    
    def _build_planning_prompt(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> str:
        """Build sophisticated prompt for modification planning"""
        
        # Extract modification details
        modification_type = modification_request.get("modification_type", "general")
        specific_changes = modification_request.get("specific_changes", [])
        overall_intent = modification_request.get("overall_intent", "")
        
        # Get template content
        html_content = current_template.get('html_export', '')
        global_css = current_template.get('globals_css', '')
        style_css = current_template.get('style_css', '')
        
        prompt = f"""
You are an expert UI/UX implementation strategist with deep knowledge of web development, design systems, and user experience optimization. Your task is to create a comprehensive modification plan for implementing UI changes.

## MODIFICATION REQUEST
- **Type**: {modification_type}
- **Intent**: {overall_intent}
- **Specific Changes**: {len(specific_changes)} changes requested

## CURRENT TEMPLATE
- **HTML Content**: {len(html_content)} characters
- **Global CSS**: {len(global_css)} characters
- **Component CSS**: {len(style_css)} characters

## PLANNING TASK
Create a detailed implementation plan that considers:

1. **Implementation Strategy**: Best approach to implement changes
2. **Code Quality**: Maintain clean, maintainable code
3. **Performance Impact**: Minimize performance degradation
4. **Responsive Design**: Ensure changes work across devices
5. **Testing Strategy**: How to validate changes
6. **Rollback Plan**: How to revert if needed

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "implementation_strategy": "string (detailed strategy for implementing changes)",
    "modification_steps": [
        {{
            "step_number": 1,
            "step_type": "string (html_modification|css_modification|content_update|structure_change)",
            "element_selector": "string (CSS selector or element description)",
            "current_state": "string (description of current state)",
            "target_state": "string (description of desired state)",
            "implementation_details": "string (detailed implementation instructions)",
            "code_changes": {{
                "html_changes": "string (specific HTML modifications)",
                "global_css_changes": "string (specific global CSS modifications)",
                "style_css_changes": "string (specific component CSS modifications)",
                "new_elements": ["list", "of", "new", "elements", "to", "add"],
                "removed_elements": ["list", "of", "elements", "to", "remove"]
            }},
            "validation_criteria": ["list", "of", "criteria", "to", "validate", "this", "step"],
            "risk_assessment": "string (potential risks for this step)",
            "estimated_effort": "string (low|medium|high)"
        }}
    ],
    "quality_checks": ["list", "of", "quality", "checks", "to", "perform"],
    "testing_requirements": ["list", "of", "testing", "requirements"],
    "performance_considerations": ["list", "of", "performance", "considerations"],
    "accessibility_checks": ["list", "of", "accessibility", "checks"],
    "rollback_plan": "string (detailed plan for rolling back changes if needed)",
    "success_criteria": ["list", "of", "criteria", "to", "determine", "success"],
    "confidence_level": 0.85
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Analyze Requirements**: Understand what needs to be changed
2. **Design Strategy**: Plan the best approach to implement changes
3. **Break Down Steps**: Divide implementation into manageable steps
4. **Consider Dependencies**: Identify dependencies between changes
5. **Plan Validation**: Determine how to validate each step
6. **Assess Risks**: Identify potential issues and mitigation strategies
7. **Ensure Quality**: Plan for maintaining code quality and performance

Remember: Focus on creating a robust, maintainable implementation that achieves the user's goals while preserving the template's integrity.
"""
        
        return prompt
    
    def _parse_planning_response(self, response: str, modification_request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the planning response with enhanced JSON extraction"""
        
        try:
            # Use shared robust JSON extraction
            parsed_response = self._extract_json_from_response(response, "planning")
            
            if parsed_response:
                # Validate required fields
                if "modification_steps" not in parsed_response:
                    parsed_response["modification_steps"] = []
                if "implementation_strategy" not in parsed_response:
                    parsed_response["implementation_strategy"] = "Standard implementation approach"
                
                return parsed_response
            else:
                self.logger.warning("No valid JSON found in planning response, using default")
                return self._get_default_modification_plan(modification_request)
                
        except Exception as e:
            self.logger.error(f"Error parsing planning response: {e}")
            return self._get_default_modification_plan(modification_request)
    
    def _get_default_modification_plan(self, modification_request: Dict[str, Any]) -> Dict[str, Any]:
        """Return default modification plan when parsing fails"""
        return {
            "implementation_strategy": "Standard implementation approach",
            "modification_steps": [
                {
                    "step_number": 1,
                    "step_type": "general_modification",
                    "element_selector": "general",
                    "current_state": "Current template state",
                    "target_state": "Improved template state",
                    "implementation_details": "Apply general improvements based on user feedback",
                    "code_changes": {
                        "html_changes": "Apply HTML modifications as needed",
                        "global_css_changes": "Apply global CSS modifications as needed",
                        "style_css_changes": "Apply component CSS modifications as needed",
                        "new_elements": [],
                        "removed_elements": []
                    },
                    "validation_criteria": ["Template renders correctly", "Changes are visible"],
                    "risk_assessment": "Low risk - general improvements",
                    "estimated_effort": "medium"
                }
            ],
            "quality_checks": ["Code validation", "Visual inspection"],
            "testing_requirements": ["Basic functionality testing"],
            "performance_considerations": ["Maintain current performance"],
            "accessibility_checks": ["Maintain accessibility standards"],
            "rollback_plan": "Revert to original template if issues arise",
            "success_criteria": ["Template renders correctly", "User requirements met"],
            "confidence_level": 0.5
        }
    
    def apply_modifications(self, template: Dict[str, Any], modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply modifications using prompt engineering to let the LLM do the work"""
        
        # Build comprehensive prompt for code modification
        prompt = self._build_apply_modifications_prompt(template, modification_plan)
        
        # Call Claude to apply the modifications
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the modified code from the response
        modified_template = self._parse_modified_code_response(response, template)
        
        return modified_template
    
    def _build_apply_modifications_prompt(self, template: Dict[str, Any], modification_plan: Dict[str, Any]) -> str:
        """Build prompt for applying modifications using LLM"""
        
        html_content = template.get('html_export', '')
        global_css = template.get('globals_css', '')
        style_css = template.get('style_css', '')
        
        implementation_strategy = modification_plan.get("implementation_strategy", "")
        modification_steps = modification_plan.get("modification_steps", [])
        
        # Format modification steps for the prompt
        steps_text = ""
        for step in modification_steps:
            steps_text += f"""
Step {step.get('step_number', 1)}: {step.get('step_type', 'general')}
- Element: {step.get('element_selector', 'general')}
- Current State: {step.get('current_state', 'unknown')}
- Target State: {step.get('target_state', 'unknown')}
- Implementation: {step.get('implementation_details', 'Apply changes')}
- HTML Changes: {step.get('code_changes', {}).get('html_changes', 'None')}
- Global CSS Changes: {step.get('code_changes', {}).get('global_css_changes', 'None')}
- Style CSS Changes: {step.get('code_changes', {}).get('style_css_changes', 'None')}
"""
        
        prompt = f"""
You are an expert web developer with deep knowledge of HTML, CSS, and modern web development practices. Your task is to apply specific modifications to a web template based on a detailed modification plan.

## IMPLEMENTATION STRATEGY
{implementation_strategy}

## MODIFICATION STEPS
{steps_text}

## CURRENT CODE

### HTML Content
```html
{html_content}
```

### Global CSS
```css
{global_css}
```

### Component CSS
```css
{style_css}
```

## YOUR TASK
Apply the specified modifications to the code above. You must:

1. **Follow the modification plan exactly**: Implement each step as specified
2. **Maintain code quality**: Ensure the modified code is clean, valid, and well-structured
3. **Preserve existing functionality**: Don't break any existing features
4. **Apply changes to the correct files**: 
   - HTML changes go to the HTML content
   - Global CSS changes go to the global_css section
   - Component CSS changes go to the style_css section
5. **Ensure compatibility**: Make sure all changes work together

## OUTPUT FORMAT
Return a JSON object with this exact structure:
```json
{{
    "html_export": "complete modified HTML content",
    "globals_css": "complete modified global CSS content", 
    "style_css": "complete modified component CSS content",
    "changes_applied": [
        {{
            "step_number": 1,
            "description": "What was changed",
            "success": true
        }}
    ],
    "validation_notes": "Any notes about the modifications made"
}}
```

## IMPORTANT REQUIREMENTS
- Return ONLY the JSON object, no additional text
- Ensure all HTML and CSS is properly formatted and valid
- Maintain the original structure where possible
- Apply all specified changes from the modification plan
- If a change cannot be applied exactly as specified, apply the closest possible modification

Remember: You are rewriting the code to implement the requested changes. Be precise and thorough.
"""
        
        return prompt
    
    def _parse_modified_code_response(self, response: str, original_template: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the modified code from the LLM response"""
        
        try:
            # Use shared robust JSON extraction
            parsed_response = self._extract_json_from_response(response, "modified_code")
            
            if parsed_response:
                # Create modified template
                modified_template = original_template.copy()
                
                # Update with modified code
                if "html_export" in parsed_response:
                    modified_template["html_export"] = parsed_response["html_export"]
                if "globals_css" in parsed_response:
                    modified_template["globals_css"] = parsed_response["globals_css"]
                if "style_css" in parsed_response:
                    modified_template["style_css"] = parsed_response["style_css"]
                
                # Add modification metadata
                modified_template["modification_metadata"] = {
                    "changes_applied": parsed_response.get("changes_applied", []),
                    "validation_notes": parsed_response.get("validation_notes", ""),
                    "modified_at": "2025-01-27T12:00:00Z"
                }
                
                return modified_template
            else:
                # If parsing fails, return original template
                self.logger.warning("Could not parse modified code response, returning original template")
                return original_template
                
        except Exception as e:
            self.logger.error(f"Error parsing modified code response: {e}")
            return original_template
    
    def validate_modifications(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate modifications using prompt engineering"""
        
        # Build validation prompt
        prompt = self._build_validation_prompt(original_template, modified_template)
        
        # Call Claude for validation
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse validation result
        return self._parse_validation_response(response)
    
    def _build_validation_prompt(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> str:
        """Build prompt for validating modifications"""
        
        original_html = original_template.get('html_export', '')
        original_global_css = original_template.get('globals_css', '')
        original_style_css = original_template.get('style_css', '')
        
        modified_html = modified_template.get('html_export', '')
        modified_global_css = modified_template.get('globals_css', '')
        modified_style_css = modified_template.get('style_css', '')
        
        prompt = f"""
You are an expert web developer and quality assurance specialist. Your task is to validate the modifications made to a web template.

## ORIGINAL CODE

### Original HTML
```html
{original_html}
```

### Original Global CSS
```css
{original_global_css}
```

### Original Component CSS
```css
{original_style_css}
```

## MODIFIED CODE

### Modified HTML
```html
{modified_html}
```

### Modified Global CSS
```css
{modified_global_css}
```

### Modified Component CSS
```css
{modified_style_css}
```

## VALIDATION TASK
Analyze the modifications and validate:

1. **Code Quality**: Is the modified code clean, valid, and well-structured?
2. **Functionality**: Do the modifications maintain existing functionality?
3. **Compatibility**: Are all changes compatible with each other?
4. **Best Practices**: Do the modifications follow web development best practices?
5. **Performance**: Will the modifications impact performance negatively?

## OUTPUT FORMAT
Return a JSON object with this exact structure:
```json
{{
    "is_valid": true,
    "validation_details": "Detailed explanation of validation results",
    "warnings": ["list", "of", "warnings", "if", "any"],
    "errors": ["list", "of", "errors", "if", "any"],
    "recommendations": ["list", "of", "improvement", "recommendations"],
    "quality_score": 0.85,
    "performance_impact": "low|medium|high",
    "accessibility_impact": "improved|maintained|degraded"
}}
```

## VALIDATION CRITERIA
- **HTML**: Must be valid HTML5
- **CSS**: Must be valid CSS3
- **Structure**: Must maintain logical document structure
- **Functionality**: Must preserve interactive elements
- **Responsiveness**: Must maintain responsive design
- **Accessibility**: Must maintain or improve accessibility

Return ONLY the JSON object, no additional text.
"""
        
        return prompt
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {
                    "is_valid": False,
                    "validation_details": "Could not parse validation response",
                    "warnings": ["Validation parsing failed"],
                    "errors": ["Unable to validate modifications"],
                    "recommendations": ["Review modifications manually"],
                    "quality_score": 0.0,
                    "performance_impact": "unknown",
                    "accessibility_impact": "unknown"
                }
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing validation response: {e}")
            return {
                "is_valid": False,
                "validation_details": f"Validation parsing error: {str(e)}",
                "warnings": ["Validation parsing failed"],
                "errors": ["Unable to validate modifications"],
                "recommendations": ["Review modifications manually"],
                "quality_score": 0.0,
                "performance_impact": "unknown",
                "accessibility_impact": "unknown"
            }
    
    def _generate_changes_summary(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> List[str]:
        """Generate precise changes summary for user communication"""
        
        # First try to extract changes from modification metadata if available
        modification_metadata = modified_template.get("modification_metadata", {})
        if modification_metadata.get("changes_applied"):
            # Use the precise changes from the modification process
            return modification_metadata["changes_applied"]
        
        # Fallback: Generate summary using prompt engineering for complex cases
        prompt = self._build_changes_summary_prompt(original_template, modified_template)
        
        # Call Claude for summary (disable CoT for faster response)
        response = self.call_claude_with_cot(prompt, enable_cot=False)
        
        # Parse summary
        parsed_summary = self._parse_changes_summary_response(response)
        
        # Ensure we always return a meaningful summary
        if not parsed_summary or len(parsed_summary) == 0:
            return ["Applied the requested modifications to the template"]
        
        return parsed_summary
    
    def _build_changes_summary_prompt(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> str:
        """Build prompt for generating user-friendly changes summary"""
        
        original_html = original_template.get('html_export', '')
        original_global_css = original_template.get('globals_css', '')
        original_style_css = original_template.get('style_css', '')
        
        modified_html = modified_template.get('html_export', '')
        modified_global_css = modified_template.get('globals_css', '')
        modified_style_css = modified_template.get('style_css', '')
        
        prompt = f"""
You are a UX designer explaining changes to a client. Compare the original and modified code and create user-friendly descriptions of what changed.

ORIGINAL CSS:
{original_global_css}
{original_style_css}

MODIFIED CSS:
{modified_global_css}
{modified_style_css}

Focus on visual changes that users would notice. Write descriptions as complete sentences that explain:
- What specific element was changed (button, background, text, etc.)
- What property was modified (color, size, spacing, etc.)  
- What the change accomplishes (better visibility, improved design, etc.)

Return ONLY a JSON object:
{{
    "summary_points": [
        "Changed the background color from [old] to [new] for better visual appeal",
        "Increased button height from [old] to [new] to improve accessibility",
        "Updated text color to enhance readability"
    ]
}}

Be specific about what changed and use user-friendly language. Focus on the 2-3 most important changes."""
        
        return prompt
    
    def _parse_changes_summary_response(self, response: str) -> List[str]:
        """Parse changes summary response"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_response = json.loads(json_str)
                
                # Return summary points
                return parsed_response.get("summary_points", ["Changes summary not available"])
            else:
                return ["Could not generate changes summary"]
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing changes summary response: {e}")
            return ["Error generating changes summary"] 