from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import logging
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class OldUIEditingAgent(BaseAgent):
    """OLD VERSION: Advanced UI Editing Agent with single-prompt modification capabilities
    
    This is the previous version that used a single-prompt approach.
    Kept for reference purposes.
    """
    
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
    
    def _analyze_html_structure(self, html_content: str) -> Dict[str, Any]:
        """Enhanced HTML structure analysis to better understand element relationships"""
        analysis = {
            "elements_by_text": {},
            "elements_by_class": {},
            "elements_by_id": {},
            "header_elements": [],
            "navigation_elements": [],
            "content_elements": [],
            "debug_info": {
                "total_elements_found": 0,
                "text_elements_found": 0,
                "sample_texts": []
            }
        }
        
        try:
            # Extract elements with their text content - improved pattern to catch more elements
            # Pattern 1: Standard elements with text content
            text_pattern = r'<([^>]+)>([^<]*)</[^>]+>'
            matches = re.findall(text_pattern, html_content)
            
            # Pattern 2: Self-closing elements with text content (like input with value)
            self_closing_pattern = r'<([^>]+)\s+value=["\']([^"\']*)["\'][^>]*>'
            self_closing_matches = re.findall(self_closing_pattern, html_content)
            
            # Pattern 3: Elements with placeholder or title attributes
            attr_pattern = r'<([^>]+)\s+(?:placeholder|title|alt)=["\']([^"\']*)["\'][^>]*>'
            attr_matches = re.findall(attr_pattern, html_content)
            
            all_matches = matches + [(attrs, text) for attrs, text in self_closing_matches] + [(attrs, text) for attrs, text in attr_matches]
            
            for tag_attrs, text_content in all_matches:
                text_content = text_content.strip()
                if text_content and len(text_content) > 0:
                    # Extract tag name safely
                    tag_match = re.match(r'(\w+)', tag_attrs)
                    tag_name = tag_match.group(1) if tag_match else "unknown"
                    
                    # Extract class names
                    class_match = re.search(r'class=["\']([^"\']*)["\']', tag_attrs)
                    classes = class_match.group(1).split() if class_match else []
                    
                    # Extract ID
                    id_match = re.search(r'id=["\']([^"\']*)["\']', tag_attrs)
                    element_id = id_match.group(1) if id_match else None
                    
                    # Store by class
                    for cls in classes:
                        if cls not in analysis["elements_by_class"]:
                            analysis["elements_by_class"][cls] = []
                        analysis["elements_by_class"][cls].append({
                            "text": text_content,
                            "tag": tag_name,
                            "id": element_id
                        })
                    
                    # Store by text content
                    analysis["elements_by_text"][text_content] = {
                        "tag": tag_name,
                        "classes": classes,
                        "id": element_id,
                        "full_attrs": tag_attrs
                    }
                    
                    # Store by ID if present
                    if element_id:
                        analysis["elements_by_id"][element_id] = {
                            "text": text_content,
                            "tag": tag_name,
                            "classes": classes,
                            "full_attrs": tag_attrs
                        }
                    
                    # Add to debug info
                    analysis["debug_info"]["total_elements_found"] += 1
                    if len(analysis["debug_info"]["sample_texts"]) < 20:  # Keep first 20 for debugging
                        analysis["debug_info"]["sample_texts"].append(text_content)
            
            analysis["debug_info"]["text_elements_found"] = len(analysis["elements_by_text"])
            
            # Identify header-related elements
            header_keywords = ["header", "nav", "logo", "menu", "navigation", "hero", "banner"]
            for text, info in analysis["elements_by_text"].items():
                try:
                    for keyword in header_keywords:
                        if keyword.lower() in text.lower() or any(keyword.lower() in cls.lower() for cls in info.get("classes", [])):
                            analysis["header_elements"].append({
                                "text": text,
                                "tag": info.get("tag", "unknown"),
                                "classes": info.get("classes", []),
                                "id": info.get("id")
                            })
                            break
                except Exception as e:
                    self.logger.warning(f"Error processing header element {text}: {e}")
                    continue
            
            # Identify navigation elements
            nav_keywords = ["nav", "menu", "ul", "li", "a"]
            for text, info in analysis["elements_by_text"].items():
                try:
                    if info.get("tag", "").lower() in nav_keywords:
                        analysis["navigation_elements"].append({
                            "text": text,
                            "tag": info.get("tag", "unknown"),
                            "classes": info.get("classes", []),
                            "id": info.get("id")
                        })
                except Exception as e:
                    self.logger.warning(f"Error processing navigation element {text}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error analyzing HTML structure: {e}")
        
        return analysis
    
    def _find_element_by_text_content(self, target_text: str, html_analysis: Dict[str, Any]) -> List[str]:
        """Find CSS selectors for elements containing specific text"""
        selectors = []
        
        # Direct text match
        if target_text in html_analysis["elements_by_text"]:
            element_info = html_analysis["elements_by_text"][target_text]
            if element_info.get("classes"):
                for cls in element_info["classes"]:
                    selectors.append(f".{cls}")
            else:
                selectors.append(element_info.get("tag", "div"))
        
        # Partial text match
        for text, element_info in html_analysis["elements_by_text"].items():
            if target_text.lower() in text.lower():
                if element_info.get("classes"):
                    for cls in element_info["classes"]:
                        selectors.append(f".{cls}")
                else:
                    selectors.append(element_info.get("tag", "div"))
        
        # Look for elements in header/navigation that might contain the text
        for element in html_analysis["header_elements"]:
            if target_text.lower() in element["text"].lower():
                if element.get("classes"):
                    for cls in element["classes"]:
                        selectors.append(f".{cls}")
        
        return list(set(selectors))  # Remove duplicates
    
    def _generate_css_selector_strategy(self, target_text: str, html_analysis: Dict[str, Any]) -> List[str]:
        """Generate multiple CSS selector strategies for finding an element"""
        strategies = []
        
        # Strategy 1: Direct text content match
        direct_selectors = self._find_element_by_text_content(target_text, html_analysis)
        strategies.extend(direct_selectors)
        
        # Strategy 2: Look for common patterns
        if "logo" in target_text.lower():
            logo_selectors = []
            for cls in html_analysis["elements_by_class"].keys():
                if "logo" in cls.lower():
                    logo_selectors.append(f".{cls}")
            strategies.extend(logo_selectors)
        
        # Strategy 3: Header-specific selectors
        if any(keyword in target_text.lower() for keyword in ["header", "nav", "menu"]):
            header_selectors = []
            for cls in html_analysis["elements_by_class"].keys():
                if any(keyword in cls.lower() for keyword in ["header", "nav", "menu", "logo"]):
                    header_selectors.append(f".{cls}")
            strategies.extend(header_selectors)
        
        # Strategy 4: Text-based selectors
        text_selectors = []
        for text, info in html_analysis["elements_by_text"].items():
            if target_text.lower() in text.lower():
                if info["classes"]:
                    text_selectors.extend([f".{cls}" for cls in info["classes"]])
        strategies.extend(text_selectors)
        
        return list(set(strategies))  # Remove duplicates
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove control characters and fix common issues"""
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
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified single-prompt modification workflow.
        
        Since we're replacing entire files, we can do everything in one LLM call:
        - Analyze the request
        - Generate complete modified code
        - Provide changes summary
        """
        try:
            self.logger.info(f"Starting single-prompt modification process for: {user_feedback}")
            
            # Single step: Analyze, modify, and summarize
            prompt = self._build_single_prompt_modification(user_feedback, current_template)
            
            self.logger.debug("Sending single-prompt modification request to Claude...")
            print(f"DEBUG: UI Editing Agent - Starting single-prompt modification...")
            
            try:
                response = self.call_claude_with_cot(prompt, enable_cot=False)
                print(f"DEBUG: UI Editing Agent - Received response (length: {len(response)})")
                
                # Debug: Log response
                print(f"DEBUG: UI Editing Agent Response: {response[:500]}...")
                if len(response) > 500:
                    print(f"DEBUG: Full UI Editing Agent Response: {response}")
            except Exception as e:
                print(f"ERROR: UI Editing Agent - Modification failed: {e}")
                return {
                    "success": False,
                    "error": f"Modification failed: {str(e)}",
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            # Parse the results
            print(f"DEBUG: UI Editing Agent - Starting to parse response...")
            
            # Check if the response indicates an API error
            if "Error calling Claude API" in response or "overloaded_error" in response:
                print(f"DEBUG: API error detected in response, returning error result")
                return {
                    "success": False,
                    "error": "Claude API is currently overloaded. Please try again in a moment.",
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            final_results = self._parse_final_output_from_response(response, current_template)
            
            # Debug: Log parsing result
            print(f"DEBUG: UI Editing Agent Final Results: {final_results}")
            
            # Check if parsing was successful
            if not final_results or not final_results.get("success", False):
                return {
                    "success": False,
                    "error": final_results.get("error", "Failed to parse LLM response") if final_results else "No response from LLM",
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            # Return the successful result
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error in single-prompt modification process: {e}")
            return {
                "success": False,
                "error": f"Modification process failed: {str(e)}",
                "original_template": current_template,
                "user_feedback": user_feedback
            }
    
    def _parse_final_output_from_response(self, response: str, original_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the final JSON response containing the complete modified code for all three files.
        Simplified approach: LLM outputs complete code for html_export, style_css, and globals_css.
        """
        try:
            print(f"DEBUG: Parsing final output response (length: {len(response)})")
            parsed_response = self._extract_json_from_response(response, "final_output")
            
            if parsed_response:
                print(f"DEBUG: Successfully extracted JSON with keys: {list(parsed_response.keys())}")
                
                # Validate that all required sections are present
                required_keys = ["html_export", "style_css", "globals_css", "changes_summary"]
                missing_keys = [key for key in required_keys if key not in parsed_response]
                
                if not missing_keys:
                    # Check if the response contains placeholder text (which should not happen with our improved prompt)
                    html_content = parsed_response["html_export"]
                    style_content = parsed_response["style_css"]
                    globals_content = parsed_response["globals_css"]
                    
                    placeholder_indicators = [
                        "/* Same as original",
                        "(Same as original",
                        "/* No changes",
                        "/* Unchanged",
                        "/* Original code",
                        "<!-- Same as original",
                        "<!-- No changes",
                        "<!-- Unchanged"
                    ]
                    
                    has_placeholders = any(indicator in html_content or indicator in style_content or indicator in globals_content 
                                         for indicator in placeholder_indicators)
                    
                    if has_placeholders:
                        print(f"WARNING: Placeholder text detected in response, this should not happen with improved prompt")
                        # Return original template with error message
                        return {
                            "success": False,
                            "error": "LLM returned placeholder text instead of actual code. This indicates a prompt compliance issue.",
                            "original_template": original_template,
                            "suggestion": "The system will retry with a stronger prompt."
                        }
                    
                    # Create the modified template structure with complete code replacement
                    modified_template = original_template.copy()
                    
                    # Replace all three files with the complete code from LLM
                    modified_template["html_export"] = parsed_response["html_export"]
                    modified_template["style_css"] = parsed_response["style_css"]
                    modified_template["globals_css"] = parsed_response["globals_css"]
                    
                    # Add modification metadata
                    modified_template["modification_metadata"] = {
                        "changes_applied": parsed_response.get("changes_summary", []),
                        "modification_type": "complete_code_replacement",
                        "modified_at": "2025-01-27T12:00:00Z"
                    }
                    
                    # Check if this was a "no changes" response (text not found)
                    changes_summary = parsed_response.get("changes_summary", [])
                    if any("not found" in summary.lower() or "could not find" in summary.lower() or "no direct match" in summary.lower() 
                           for summary in changes_summary):
                        print(f"INFO: Target text not found, returning original template with error message")
                        return {
                            "success": False,
                            "error": "Target text not found in the HTML structure",
                            "original_template": original_template,
                            "changes_summary": changes_summary,
                            "suggestion": "Please check the exact text you want to modify or provide more context about the element location."
                        }
                    
                    return {
                        "success": True,
                        "modified_template": modified_template,
                        "changes_summary": parsed_response["changes_summary"]
                    }
                else:
                    print(f"ERROR: Missing required sections in final output: {missing_keys}")
                    self.logger.warning(f"Missing required sections in final output: {missing_keys}")
                    return {
                        "success": False,
                        "error": f"Missing required sections: {missing_keys}"
                    }
            else:
                print(f"ERROR: Failed to extract JSON from final output response")
                self.logger.warning("Failed to extract JSON from final output response")
                return {
                    "success": False,
                    "error": "Failed to parse LLM response"
                }
            
        except Exception as e:
            self.logger.error(f"Error parsing final output from response: {e}")
            return {
                "success": False,
                "error": f"Parsing error: {str(e)}"
            }
    
    def _build_single_prompt_modification(self, user_feedback: str, current_template: Dict[str, Any]) -> str:
        """
        [PROMPT ENGINEERING] Creates a single comprehensive prompt that handles:
        - Analysis of the user request
        - HTML structure understanding
        - Complete code generation
        - Changes summary
        
        This replaces the previous two-step approach with a more efficient single-step process.
        """
        # Extract template information for context
        html_content = current_template.get('html_export', '')
        global_css = current_template.get('globals_css', '')
        style_css = current_template.get('style_css', '')
        
        # Combine CSS for analysis
        css_content = f"{global_css}\n{style_css}"
        
        # Enhanced HTML structure analysis
        html_analysis = self._analyze_html_structure(html_content)
        
        template_name = current_template.get('name', 'Unknown Template')
        template_category = current_template.get('category', 'general')
        
        # Generate HTML structure insights with debugging info
        structure_insights = []
        
        # Add debug information
        debug_info = html_analysis.get("debug_info", {})
        structure_insights.append(f"DEBUG: Found {debug_info.get('total_elements_found', 0)} total elements, {debug_info.get('text_elements_found', 0)} text elements")
        
        if html_analysis["elements_by_text"]:
            structure_insights.append("Text elements found:")
            for text, info in list(html_analysis["elements_by_text"].items())[:15]:  # Increased limit for better debugging
                structure_insights.append(f"  - '{text}' (tag: {info['tag']}, classes: {info['classes']}, id: {info.get('id', 'none')})")
        
        if html_analysis["header_elements"]:
            structure_insights.append("Header elements found:")
            for header in html_analysis["header_elements"][:5]:  # Limit to first 5
                structure_insights.append(f"  - {header['tag']}: '{header['text']}' (classes: {header['classes']})")
        
        if html_analysis["navigation_elements"]:
            structure_insights.append("Navigation elements found:")
            for nav in html_analysis["navigation_elements"][:5]:  # Limit to first 5
                structure_insights.append(f"  - {nav['tag']}: '{nav['text']}' (classes: {nav['classes']})")
        
        structure_insights_text = "\n".join(structure_insights) if structure_insights else "No specific structure insights available."
        
        # Truncate long code sections to prevent token limit issues
        max_code_length = 8000  # Conservative limit to prevent truncation
        
        def truncate_code(code: str, max_length: int) -> str:
            if len(code) <= max_length:
                return code
            return code[:max_length] + f"\n/* ... truncated for length ({len(code)} chars total) ... */"
        
        html_content_truncated = truncate_code(html_content, max_code_length)
        global_css_truncated = truncate_code(global_css, max_code_length)
        style_css_truncated = truncate_code(style_css, max_code_length)
        
        prompt = f"""You are an expert web developer. Analyze the user request and generate complete modified code.

## CRITICAL RULE - READ THIS FIRST
**NEVER, EVER use placeholder text or comments like "/* Same as original */" or "(Same as original HTML)". 
ALWAYS return the actual complete code. If you cannot find the target text or cannot make changes, 
return the original code exactly as provided. This is a strict requirement.**

## USER REQUEST
{user_feedback}

## TEMPLATE CONTEXT
- Template Name: {template_name}
- Category: {template_category}

## HTML STRUCTURE ANALYSIS
{structure_insights_text}

## CURRENT CODE

### HTML
```html
{html_content_truncated}
```

### GLOBAL CSS
```css
{global_css_truncated}
```

### STYLE CSS
```css
{style_css_truncated}
```

## TASK
1. **Analyze the request**: Understand what the user wants to change
2. **Identify target elements**: Use the HTML structure analysis to find the right elements
3. **Generate complete code**: Return the complete modified HTML, global CSS, and style CSS
4. **Provide summary**: List what changes were made

## GUIDELINES
- **Text Content Matching**: When targeting elements by text, look for exact matches in the HTML structure analysis
- **CSS Selector Precision**: Use specific, unique selectors (classes, IDs, or combinations)
- **Element Context**: Consider the element's position and surrounding structure
- **Complete Code**: Return the entire modified code for all three files, not just changes
- **Preserve Structure**: Keep the overall layout and structure intact
- **Syntactic Correctness**: Ensure all HTML and CSS is valid

## ERROR HANDLING
If you cannot find the target text in the HTML structure analysis:
1. **DO NOT** use placeholder text or comments
2. **DO** return the original code exactly as provided
3. **DO** include a clear error message in the changes_summary explaining what was not found
4. **DO** suggest similar text that was found (if any)

## OUTPUT FORMAT
Return ONLY this JSON structure:
```json
{{
  "html_export": "complete HTML code with modifications",
  "globals_css": "complete global CSS code with modifications", 
  "style_css": "complete style CSS code with modifications",
  "changes_summary": [
    "change description 1",
    "change description 2"
  ]
}}
```

## FINAL REMINDER - CRITICAL RULES
- **NEVER use placeholder text** like "/* Same as original */" or "(Same as original HTML)"
- **ALWAYS return actual complete code** - if no changes, return the original code exactly
- **If target text not found**, return original code with error message in changes_summary
- **Include ALL the original code** plus your modifications
- **Ensure the code is syntactically correct**
- **Be specific in the changes_summary** about what was modified or why it couldn't be modified"""
        
        return prompt 