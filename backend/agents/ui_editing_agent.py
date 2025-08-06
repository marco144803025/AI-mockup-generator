#!/usr/bin/env python3
"""
UI Editing Agent - Simplified Two-Step LLM Architecture
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

from .base_agent import BaseAgent


class UIEditingAgent(BaseAgent):
    """Simplified UI Editing Agent using two-step LLM process"""
    
    def __init__(self):
        system_message = """You are an expert UI/UX modification agent with deep understanding of web development, HTML, CSS, and user intent analysis.

Your role is to:
1. Analyze user requests and create detailed modification plans
2. Apply those plans to generate complete, working code
3. Handle ambiguity and provide clarification when needed
4. Generate precise, valid CSS selectors and code modifications

**CRITICAL CSS SELECTOR REQUIREMENTS:**
- ✅ ONLY use valid CSS selectors: `.class-name`, `#id-name`, `tag.class`, `tag#id`
- ❌ NEVER use jQuery selectors: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
- ✅ Every selector must be valid CSS that works in a real stylesheet
- ✅ Use exact classes/IDs from the code - don't invent or guess

You use the Claude-3-5-Sonnet model for complex reasoning and code generation."""
        
        super().__init__("UIEditingAgent", system_message, model="claude-3-5-sonnet-20241022")
        self.logger = logging.getLogger(__name__)
    
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
    
    def _analyze_html_structure_with_beautifulsoup(self, html_content: str) -> Dict[str, Any]:
        """Analyze HTML structure using BeautifulSoup for comprehensive understanding"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all text elements with their context
            text_elements = []
            for element in soup.find_all(text=True):
                if element.strip():
                    parent = element.parent
                    text_elements.append({
                        "text": element.strip(),
                        "tag": parent.name if parent else "unknown",
                        "classes": parent.get('class', []) if parent else [],
                        "id": parent.get('id', '') if parent else '',
                        "parent_context": self._get_parent_context(parent) if parent else '',
                        "sibling_context": self._get_sibling_context(parent) if parent else []
                    })
            
            # Group elements by CSS class
            elements_by_class = {}
            for element in soup.find_all(class_=True):
                for class_name in element.get('class', []):
                    if class_name not in elements_by_class:
                        elements_by_class[class_name] = []
                    elements_by_class[class_name].append({
                        "tag": element.name,
                        "text": element.get_text(strip=True)[:50] + "..." if len(element.get_text(strip=True)) > 50 else element.get_text(strip=True),
                        "id": element.get('id', ''),
                        "classes": element.get('class', [])
                    })
            
            # Group elements by ID
            elements_by_id = {}
            for element in soup.find_all(id=True):
                element_id = element.get('id')
                elements_by_id[element_id] = {
                    "tag": element.name,
                    "text": element.get_text(strip=True)[:50] + "..." if len(element.get_text(strip=True)) > 50 else element.get_text(strip=True),
                    "classes": element.get('class', [])
                }
            
            # Find header elements
            header_elements = []
            for element in soup.find_all(['header', 'nav', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                header_elements.append({
                    "tag": element.name,
                    "text": element.get_text(strip=True)[:50] + "..." if len(element.get_text(strip=True)) > 50 else element.get_text(strip=True),
                    "classes": element.get('class', []),
                    "id": element.get('id', '')
                })
            
            # Find navigation elements
            nav_elements = []
            for element in soup.find_all(['nav', 'a']) + soup.find_all(class_=re.compile(r'nav|menu|header')):
                nav_elements.append({
                    "tag": element.name,
                    "text": element.get_text(strip=True)[:50] + "..." if len(element.get_text(strip=True)) > 50 else element.get_text(strip=True),
                    "classes": element.get('class', []),
                    "id": element.get('id', '')
                })
            
            # Build simplified DOM structure
            dom_structure = self._build_dom_structure(soup)
            
            return {
                "text_elements": text_elements,
                "elements_by_class": elements_by_class,
                "elements_by_id": elements_by_id,
                "header_elements": header_elements,
                "navigation_elements": nav_elements,
                "dom_structure": dom_structure,
                "total_elements": len(soup.find_all()),
                "total_text_elements": len(text_elements)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing HTML structure: {e}")
            return {
                "text_elements": [],
                "elements_by_class": {},
                "elements_by_id": {},
                "header_elements": [],
                "navigation_elements": [],
                "dom_structure": {},
                "total_elements": 0,
                "total_text_elements": 0,
                "error": str(e)
            }
    
    def _get_parent_context(self, element) -> str:
        """Get parent context for an element"""
        if element and element.parent:
            parent = element.parent
            context_parts = []
            if parent.name:
                context_parts.append(parent.name)
            if parent.get('class'):
                context_parts.extend(parent.get('class'))
            if parent.get('id'):
                context_parts.append(f"#{parent.get('id')}")
            return ".".join(context_parts)
        return ""
    
    def _get_sibling_context(self, element) -> List[str]:
        """Get sibling context for an element"""
        if element and element.parent:
            siblings = []
            for sibling in element.parent.find_all(recursive=False):
                if sibling != element:
                    sibling_info = []
                    if sibling.name:
                        sibling_info.append(sibling.name)
                    if sibling.get('class'):
                        sibling_info.extend(sibling.get('class'))
                    if sibling.get('id'):
                        sibling_info.append(f"#{sibling.get('id')}")
                    if sibling_info:
                        siblings.append(".".join(sibling_info))
            return siblings
        return []
    
    def _build_dom_structure(self, soup) -> Dict[str, Any]:
        """Build a simplified DOM structure for debugging"""
        structure = {}
        
        # Find main sections
        main_sections = soup.find_all(['main', 'section', 'div'], class_=re.compile(r'main|section|container|wrapper'))
        for i, section in enumerate(main_sections[:5]):  # Limit to first 5
            section_info = {
                "tag": section.name,
                "classes": section.get('class', []),
                "id": section.get('id', ''),
                "children_count": len(section.find_all(recursive=False))
            }
            structure[f"section_{i+1}"] = section_info
        
        return structure
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Process a UI modification request using two-step LLM approach"""
        try:
            self.logger.info(f"Processing modification request: {user_feedback}")
            
            # Extract current UI code
            html_content = current_template.get("html_export", "")
            style_css = current_template.get("style_css", "")
            globals_css = current_template.get("globals_css", "")
            
            if not html_content:
                return {
                    "success": False,
                    "error": "No HTML content found in template"
                }
            
            # Step 1: Create detailed modification plan
            self.logger.debug("Step 1: Creating modification plan...")
            plan_result = self._create_modification_plan(user_feedback, html_content, style_css, globals_css)
            
            if not plan_result.get("success"):
                return plan_result
            
            modification_plan = plan_result["plan"]
            
            # Check if clarification is needed
            if modification_plan.get("requires_clarification", False):
                return {
                    "success": True,
                    "requires_clarification": True,
                    "clarification_options": modification_plan.get("clarification_options", []),
                    "original_request": user_feedback
                }
            
            # Step 2: Execute the plan and generate new code
            self.logger.debug("Step 2: Executing modification plan...")
            execution_result = self._execute_modification_plan(modification_plan, html_content, style_css, globals_css)
            
            if not execution_result.get("success"):
                return execution_result
            
            # Return the complete result
            return {
                "success": True,
                "requires_clarification": False,
                "changes_summary": execution_result.get("changes_summary", []),
                "modified_template": {
                    "html_export": execution_result.get("html", html_content),
                    "style_css": execution_result.get("style_css", style_css),
                    "globals_css": execution_result.get("globals_css", globals_css)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing modification request: {e}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def _create_modification_plan(self, user_feedback: str, html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Step 1: Create a detailed modification plan"""
        try:
            # Analyze HTML structure
            html_analysis = self._analyze_html_structure_with_beautifulsoup(html_content)
            
            # Build the planning prompt
            prompt = self._build_planning_prompt(user_feedback, html_content, style_css, globals_css, html_analysis)
            
            self.logger.debug("Sending planning request to Claude Sonnet...")
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse the planning response
            plan = self._extract_json_from_response(response, "planning response")
            
            if plan:
                return {
                    "success": True,
                    "plan": plan
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to parse modification plan from LLM response"
                }
                
        except Exception as e:
            self.logger.error(f"Error creating modification plan: {e}")
            return {
                "success": False,
                "error": f"Planning failed: {str(e)}"
            }
    
    def _build_planning_prompt(self, user_feedback: str, html_content: str, style_css: str, globals_css: str, html_analysis: Dict[str, Any]) -> str:
        """Build the planning prompt with full code context"""
        
        # Format HTML analysis for the prompt
        structure_analysis_text = f"""
## HTML STRUCTURE ANALYSIS

**Total Elements**: {html_analysis.get('total_elements', 0)}
**Total Text Elements**: {html_analysis.get('total_text_elements', 0)}

## ALL TEXT ELEMENTS
"""
        
        for i, element in enumerate(html_analysis.get('text_elements', [])[:20]):  # Limit to first 20
            structure_analysis_text += f"""
{i+1}. Text: "{element['text']}"
   Tag: {element['tag']}
   Classes: {', '.join(element['classes']) if element['classes'] else 'none'}
   ID: {element['id'] if element['id'] else 'none'}
   Parent: {element['parent_context']}
   Siblings: {', '.join(element['sibling_context'][:3]) if element['sibling_context'] else 'none'}
"""
        
        structure_analysis_text += f"""

## ELEMENTS BY CSS CLASS
"""
        
        for class_name, elements in list(html_analysis.get('elements_by_class', {}).items())[:15]:  # Limit to first 15
            structure_analysis_text += f"""
.{class_name}:
"""
            for element in elements[:3]:  # Limit to first 3 elements per class
                structure_analysis_text += f"  - {element['tag']}: '{element['text']}' (ID: {element['id'] or 'none'})\n"
        
        structure_analysis_text += f"""

## ELEMENTS BY ID
"""
        
        for element_id, element in list(html_analysis.get('elements_by_id', {}).items())[:10]:  # Limit to first 10
            structure_analysis_text += f"""
#{element_id}:
  Tag: {element['tag']}
  Text: '{element['text']}'
  Classes: {', '.join(element['classes']) if element['classes'] else 'none'}
"""
        
        structure_analysis_text += f"""

## HEADER ELEMENTS
"""
        
        for element in html_analysis.get('header_elements', [])[:10]:
            structure_analysis_text += f"""
- {element['tag']}: '{element['text']}' (Classes: {', '.join(element['classes']) if element['classes'] else 'none'}, ID: {element['id'] or 'none'})
"""
        
        structure_analysis_text += f"""

## NAVIGATION ELEMENTS
"""
        
        for element in html_analysis.get('navigation_elements', [])[:10]:
            structure_analysis_text += f"""
- {element['tag']}: '{element['text']}' (Classes: {', '.join(element['classes']) if element['classes'] else 'none'}, ID: {element['id'] or 'none'})
"""
        
        structure_analysis_text += f"""

## DOM STRUCTURE OVERVIEW
"""
        
        for section_name, section_info in html_analysis.get('dom_structure', {}).items():
            structure_analysis_text += f"""
{section_name}: {section_info['tag']} (Classes: {', '.join(section_info['classes']) if section_info['classes'] else 'none'}, ID: {section_info['id'] or 'none'}, Children: {section_info['children_count']})
"""

        return f"""# UI MODIFICATION PLANNING

## USER REQUEST
{user_feedback}

## COMPLETE HTML CODE
```html
{html_content}
```

## COMPLETE STYLE CSS
```css
{style_css}
```

## COMPLETE GLOBALS CSS
```css
{globals_css}
```

{structure_analysis_text}

## CRITICAL CSS SELECTOR RULES - READ CAREFULLY

**VALID CSS SELECTORS ONLY:**
- ✅ `.class-name` (targets elements with class)
- ✅ `#id-name` (targets element with ID)
- ✅ `tag.class` (e.g., `button.btn-primary`)
- ✅ `tag#id` (e.g., `div#header`)
- ✅ `.class1.class2` (multiple classes)

**INVALID SELECTORS - NEVER USE:**
- ❌ `:contains('text')` (jQuery selector)
- ❌ `:has()` (jQuery selector)
- ❌ `:text()` (jQuery selector)
- ❌ `:first`, `:last` (jQuery selectors)
- ❌ `:eq()` (jQuery selector)

## FEW-SHOT EXAMPLES

**Example 1: Valid CSS Selector**
**User Request**: "change the color of the login button to blue"

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the visual appearance of a login button",
    "target_element_type": "button",
    "modification_type": "styling",
    "specific_change": "color change to blue"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Login",
      "css_selector": ".btn-primary",
      "confidence": 0.95,
      "reasoning": "Exact text match found with button class"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "modify_css",
      "target_selector": ".btn-primary",
      "property": "background-color",
      "new_value": "#007bff",
      "description": "Change button background color to blue"
    }}
  ],
  "expected_outcome": "Login button will have a blue background color"
}}
```

**Example 2: Multiple Classes**
**User Request**: "change the connect link color to red"

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the color of a navigation link",
    "target_element_type": "link",
    "modification_type": "styling",
    "specific_change": "text color change to red"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Connect",
      "css_selector": ".text-wrapper-10",
      "confidence": 0.95,
      "reasoning": "Unique class identifier for the Connect link"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "modify_css",
      "target_selector": ".text-wrapper-10",
      "property": "color",
      "new_value": "#ff0000",
      "description": "Change Connect link text color to red"
    }}
  ],
  "expected_outcome": "The Connect link will appear in red color"
}}
```

**Example 3: What NOT to do (INVALID)**
**User Request**: "change the connect button color to red"

**WRONG Plan (DO NOT USE):**
```json
{{
  "steps": [
    {{
      "target_selector": ".text-wrapper-10:contains('Connect')",
      "property": "color",
      "new_value": "#ff0000"
    }}
  ]
}}
```

**CORRECT Plan (USE THIS):**
```json
{{
  "steps": [
    {{
      "target_selector": ".text-wrapper-10",
      "property": "color", 
      "new_value": "#ff0000"
    }}
  ]
}}
```

## MANDATORY VALIDATION CHECKLIST

Before generating any CSS selector, verify:
1. ✅ Does it start with `.` (class), `#` (ID), or tag name?
2. ✅ Does it contain ONLY valid CSS syntax?
3. ✅ Does it NOT contain `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`?
4. ✅ Can it be used in a real CSS file?
5. ✅ Does it target the specific element from the HTML analysis?

**REMEMBER**: If you're unsure about a selector, use the simplest valid option (e.g., `.class-name`).

## FINAL VALIDATION - BEFORE SUBMITTING

**STOP AND CHECK YOUR CSS SELECTORS:**

1. **Does every `target_selector` start with `.`, `#`, or a tag name?**
2. **Does every `target_selector` NOT contain `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`?**
3. **Can every `target_selector` be used in a real CSS file?**
4. **Does every `target_selector` match an element from the HTML analysis above?**

**IF ANY SELECTOR FAILS THESE CHECKS, FIX IT BEFORE SUBMITTING.**

## YOUR TASK
Create a detailed modification plan for the user request above. You have access to the complete HTML structure analysis above AND the full raw code. Use this information to:

1. **Find Exact Matches**: Look for exact text matches in the "ALL TEXT ELEMENTS" section
2. **Identify Target Elements**: Use the detailed element information to find the best targets
3. **Generate Precise Selectors**: Use the class and ID information to create accurate CSS selectors
4. **Handle Ambiguity**: If multiple elements match, identify them for clarification

## ANALYSIS GUIDELINES - EXACT CODE REQUIREMENTS

**CRITICAL: You must return EXACT, VALID code that works immediately**

- **Text Matching**: Look for exact text matches first, then partial matches
- **CSS Selectors**: 
  - ✅ **MUST USE ONLY**: `.class-name`, `#id-name`, `tag.class`, `tag#id`, `.class1.class2`
  - ❌ **NEVER USE**: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
  - **Prefer classes over IDs** for better maintainability
  - **Use the EXACT class/ID from HTML analysis** - don't guess or invent
  - **If targeting by text content**, use the class/ID of the element containing that text
- **Context**: Consider the element's position (header, navigation, etc.)
- **Confidence**: Base confidence on how well the target matches the request
- **Code Quality**: Every selector must be valid CSS that can be used in a real stylesheet

## OUTPUT FORMAT
Return ONLY this JSON structure:
```json
{{
  "intent_analysis": {{
    "user_goal": "string describing what the user wants to achieve",
    "target_element_type": "string (text|button|image|section|etc)",
    "modification_type": "string (styling|content|layout|structure)",
    "specific_change": "string describing the exact change needed"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "string (exact text found)",
      "css_selector": "string (best CSS selector)",
      "confidence": 0.95,
      "reasoning": "string explaining why this target was chosen"
    }},
    "alternative_targets": [
      {{
        "text_content": "string",
        "css_selector": "string",
        "confidence": 0.7,
        "reasoning": "string"
      }}
    ]
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "string (modify_text|modify_css|modify_html|add_element|remove_element)",
      "target_selector": "string (CSS selector)",
      "property": "string (for CSS modifications)",
      "new_value": "string (new value to set)",
      "description": "string (what this step does)"
    }}
  ],
  "expected_outcome": "string describing what the user will see after changes"
}}
```

## IMPORTANT RULES
- **Use the HTML Analysis**: Reference specific elements from the analysis above
- **Be Precise**: Use exact text content and CSS selectors from the analysis
- **Handle Ambiguity**: If multiple elements match, set requires_clarification to true
- **Provide Clear Reasoning**: Explain why you chose specific targets
- **VALIDATE EVERY SELECTOR**: Ensure it's valid CSS before including it
- **Consider Context**: Use header/navigation information when relevant"""
    
    def _execute_modification_plan(self, modification_plan: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Step 2: Execute the modification plan and generate new code"""
        try:
            # Build the execution prompt
            prompt = self._build_execution_prompt(modification_plan, html_content, style_css, globals_css)
            
            self.logger.debug("Sending execution request to Claude Sonnet...")
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse the execution response
            result = self._parse_execution_response(response, html_content, style_css, globals_css)
            
            if result:
                return {
                    "success": True,
                    "html": result.get("html", html_content),
                    "style_css": result.get("style_css", style_css),
                    "globals_css": result.get("globals_css", globals_css),
                    "changes_summary": result.get("changes_summary", [])
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to parse execution result from LLM response"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing modification plan: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    def _build_execution_prompt(self, modification_plan: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> str:
        """Build the execution prompt"""
        
        plan_json = json.dumps(modification_plan, indent=2)
        
        return f"""# UI MODIFICATION EXECUTION

You are an expert web developer. Your task is to apply the changes from the modification plan to the original code and return the new, complete code.

## MODIFICATION PLAN
```json
{plan_json}
```

## ORIGINAL HTML CODE
```html
{html_content}
```

## ORIGINAL STYLE CSS
```css
{style_css}
```

## ORIGINAL GLOBALS CSS
```css
{globals_css}
```

## YOUR TASK
Apply the changes from the modification plan to the original code. You must:

1. **Follow the plan exactly**: Execute each step in the modification plan
2. **Use valid CSS selectors**: Only use valid CSS selectors (no jQuery selectors like `:contains()`)
3. **Return complete code**: Return the complete modified HTML, style.css, and globals.css
4. **Maintain code quality**: Keep the code clean and well-formatted
5. **Track changes**: List what changes you made

## EXECUTION GUIDELINES

**For CSS Modifications:**
- Add new CSS rules to the appropriate CSS file (style.css or globals.css)
- Use the exact CSS selectors from the plan
- Ensure all CSS rules are valid and complete

**For Text Modifications:**
- Modify the text content in the HTML
- Preserve the HTML structure and attributes

**For HTML Modifications:**
- Modify the HTML structure as specified
- Maintain proper HTML syntax and formatting

## OUTPUT FORMAT
Return ONLY this JSON structure:
```json
{{
  "html": "complete modified HTML code",
  "style_css": "complete modified style.css code",
  "globals_css": "complete modified globals.css code",
  "changes_summary": [
    "Description of change 1",
    "Description of change 2",
    "Description of change 3"
  ]
}}
```

## IMPORTANT RULES
- **Return complete files**: Include the entire HTML, style.css, and globals.css content
- **Use valid CSS**: Only valid CSS selectors, no jQuery selectors
- **Apply all steps**: Execute every step in the modification plan
- **Maintain formatting**: Keep the code properly formatted and readable
- **Track changes**: List each change you made in the changes_summary

**CRITICAL**: Ensure all CSS selectors are valid and will work in a real browser."""
    
    def _parse_execution_response(self, response: str, original_html: str, original_style: str, original_globals: str) -> Optional[Dict[str, Any]]:
        """Parse the execution response and extract the modified code"""
        try:
            # Extract JSON from response
            result = self._extract_json_from_response(response, "execution response")
            
            if not result:
                self.logger.error("Failed to extract JSON from execution response")
                return None
            
            # Validate the result structure
            required_keys = ["html", "style_css", "globals_css", "changes_summary"]
            for key in required_keys:
                if key not in result:
                    self.logger.error(f"Missing required key in execution result: {key}")
                    return None
            
            # Validate that the code was actually modified
            if (result["html"] == original_html and 
                result["style_css"] == original_style and 
                result["globals_css"] == original_globals):
                self.logger.warning("Execution result shows no changes were made")
                return None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing execution response: {e}")
            return None