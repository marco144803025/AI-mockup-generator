#!/usr/bin/env python3
"""
UI Editing Agent - Simplified Two-Step LLM Architecture
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List

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
-  ONLY use valid CSS selectors: `.class-name`, `#id-name`, `tag.class`, `tag#id`
-  NEVER use jQuery selectors: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
-  Every selector must be valid CSS that works in a real stylesheet
-  Use exact classes/IDs from the code - don't invent or guess
"""
        
        super().__init__("UIEditingAgent", system_message, model="claude-3-5-haiku-20241022")
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
            self.logger.debug(f"🔍 JSON EXTRACTION: Extracting JSON from {context}: {response[:200]}...")
            
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
                    self.logger.warning(f"🔍 JSON EXTRACTION: Failed to parse JSON in {context}: {e}")
                    return None
            
            self.logger.warning(f"🔍 JSON EXTRACTION: No JSON found in {context}")
            return None
            
        except Exception as e:
            self.logger.error(f"🔍 JSON EXTRACTION: Error extracting JSON from {context}: {e}")
            return None
    
    # Note: All HTML analysis is now done by the LLM in the enhanced prompt
    # No need for hardcoded BeautifulSoup analysis methods
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Process a UI modification request using two-step LLM approach"""
        try:
            self.logger.info(f"🔄 UI EDITING AGENT: Starting modification request: {user_feedback}")
            
            # Extract current UI code
            html_content = current_template.get("html_export", "")
            style_css = current_template.get("style_css", "")
            globals_css = current_template.get("globals_css", "")
            
            self.logger.info(f"📊 UI EDITING AGENT: Template loaded - HTML: {len(html_content)} chars, CSS: {len(style_css)} chars")
            
            if not html_content:
                self.logger.error(f"❌ UI EDITING AGENT: No HTML content found in template")
                return {
                    "success": False,
                    "error": "No HTML content found in template"
                }
            
            # Step 1: Create detailed modification plan
            self.logger.info(f"🎯 PLANNER PHASE: Creating modification plan...")
            plan_result = self._create_modification_plan(user_feedback, html_content, style_css, globals_css)
            
            if not plan_result.get("success"):
                self.logger.error(f"❌ PLANNER PHASE: Failed to create modification plan")
                return plan_result
            
            modification_plan = plan_result["plan"]
            self.logger.info(f"✅ PLANNER PHASE: Plan created successfully")
            
            # Check if clarification is needed
            if modification_plan.get("requires_clarification", False):
                self.logger.info(f"❓ PLANNER PHASE: Clarification needed from user")
                return {
                    "success": True,
                    "requires_clarification": True,
                    "clarification_options": modification_plan.get("clarification_options", []),
                    "original_request": user_feedback
                }
            
            # Step 2: Execute the plan and generate new code
            self.logger.info(f"⚡ EXECUTOR PHASE: Executing modification plan...")
            execution_result = self._execute_modification_plan(modification_plan, html_content, style_css, globals_css)
            
            if not execution_result.get("success"):
                self.logger.error(f"❌ EXECUTOR PHASE: Failed to execute modification plan")
                return execution_result
            
            self.logger.info(f"✅ EXECUTOR PHASE: Plan executed successfully")
            self.logger.info(f"🎉 UI EDITING AGENT: Modification completed successfully")
            
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
            self.logger.error(f"💥 UI EDITING AGENT: Error processing modification request: {e}")
            return {
                    "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def _create_modification_plan(self, user_feedback: str, html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Step 1: Create a detailed modification plan using LLM analysis"""
        try:
            self.logger.info(f"🎯 PLANNER: Building enhanced planning prompt...")
            
            # Build the enhanced planning prompt that lets LLM do all analysis
            prompt = self._build_enhanced_planning_prompt(user_feedback, html_content, style_css, globals_css)
            
            self.logger.info(f"🎯 PLANNER: Sending planning request to Claude Haiku...")
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            self.logger.info(f"🎯 PLANNER: Received response from Claude Haiku (length: {len(response)})")
            
            # Parse the planning response
            self.logger.info(f"🎯 PLANNER: Parsing JSON from planning response...")
            plan = self._extract_json_from_response(response, "planning response")
            
            if plan:
                self.logger.info(f"🎯 PLANNER: Successfully parsed modification plan")
                return {
                    "success": True,
                    "plan": plan
                }
            else:
                self.logger.error(f"🎯 PLANNER: Failed to parse modification plan from LLM response")
                return {
                    "success": False,
                    "error": "Failed to parse modification plan from LLM response"
            }
            
        except Exception as e:
            self.logger.error(f"🎯 PLANNER: Error creating modification plan: {e}")
            return {
                "success": False,
                "error": f"Planning failed: {str(e)}"
            }
    
    def _build_enhanced_planning_prompt(self, user_feedback: str, html_content: str, style_css: str, globals_css: str) -> str:
        """Build an enhanced prompt that lets the LLM do comprehensive analysis"""
        
        return f"""# COMPREHENSIVE UI MODIFICATION ANALYSIS & PLANNING

You are an expert UI/UX analyst and web developer with deep understanding of:
- HTML structure and semantics
- CSS styling and visual properties
- UI/UX patterns and conventions
- Spatial relationships and layout
- Visual design principles
- User intent interpretation

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

## YOUR COMPREHENSIVE ANALYSIS TASK

**Step 1: Analyze the Complete UI Structure**
Analyze the HTML and CSS to understand:
- **Visual Layout**: Identify top, bottom, left, right, center areas
- **UI Patterns**: Recognize headers, navigation, hero sections, footers, sidebars, forms, buttons, cards
- **Spatial Relationships**: Map element positions and visual hierarchy
- **Visual Properties**: Identify colors, sizes, fonts, spacing, borders
- **Interactive Elements**: Find buttons, links, forms, CTAs
- **Content Structure**: Understand text content, images, sections

**Step 2: Understand User Intent**
Interpret the user's request by considering:
- **Location Descriptors**: "top", "bottom", "left", "right", "center", "side", "above", "below"
- **Visual Descriptors**: "red", "blue", "large", "small", "bright", "dark", "bold"
- **Semantic Descriptors**: "header", "navigation", "hero", "footer", "button", "form"
- **Functional Descriptors**: "clickable", "interactive", "prominent", "hidden"

**Step 3: Identify Target Elements**
Find the best matching elements based on:
- **Exact Text Matches**: Direct text content matches
- **Spatial Location**: Position-based identification
- **Visual Properties**: Color, size, style-based identification
- **Semantic Role**: Function-based identification (button, link, etc.)
- **Context Clues**: Surrounding elements and layout context

**Step 4: Generate Precise CSS Selectors**
Create valid CSS selectors that:
- Target the exact intended elements
- Use valid CSS syntax (no jQuery selectors)
- Are specific enough to avoid conflicts
- Follow best practices for maintainability

## ANALYSIS GUIDELINES

### **Spatial Understanding**
- **Top/Bottom**: Elements in upper/lower 25% of viewport
- **Left/Right**: Elements in left/right 25% of viewport  
- **Center**: Elements in middle 50% of viewport
- **Above/Below Fold**: Visible without scrolling vs. requires scroll

### **UI Pattern Recognition**
- **Header/Navigation**: Top navigation bars, menus, logos
- **Hero Sections**: Large banner areas, main headlines, prominent CTAs
- **Content Areas**: Main text sections, articles, descriptions
- **Sidebars**: Side navigation, secondary content, panels
- **Footers**: Bottom sections, links, copyright info
- **Forms**: Input fields, buttons, data entry areas
- **Cards/Tiles**: Content containers, product cards, info boxes
- **Modals/Popups**: Overlay dialogs, notifications

### **Visual Property Analysis**
- **Colors**: Background colors, text colors, border colors
- **Sizes**: Width, height, font sizes, padding, margins
- **Typography**: Font families, weights, styles
- **Layout**: Position, display, flexbox, grid properties
- **Effects**: Borders, shadows, gradients, animations

### **CSS Selector Best Practices**
- ✅ **Valid Selectors**: `.class-name`, `#id-name`, `tag.class`, `tag#id`
- ❌ **Invalid Selectors**: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
- **Specificity**: Use specific enough selectors to target intended elements
- **Maintainability**: Prefer classes over IDs, avoid overly complex selectors

## FEW-SHOT EXAMPLES

### **Example 1: Location-Based Request**
**User Request**: "change the top navigation button to blue"

**Analysis**:
- Identifies navigation elements at the top of the page
- Finds buttons within the navigation area
- Analyzes current styling to understand the target

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the color of a navigation button at the top of the page",
    "target_element_type": "button",
    "modification_type": "styling",
    "specific_change": "change button color to blue"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Login",
      "css_selector": ".nav-top .btn-primary",
      "confidence": 0.95,
      "reasoning": "Found navigation button in top area with class .btn-primary"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "modify_css",
      "target_selector": ".nav-top .btn-primary",
      "property": "background-color",
      "new_value": "#007bff",
      "description": "Change top navigation button background to blue"
    }}
  ],
  "expected_outcome": "The top navigation button will have a blue background"
}}
```

### **Example 2: Visual-Based Request**
**User Request**: "make the red button green"

**Analysis**:
- Scans all elements for red background colors
- Identifies buttons with red styling
- Determines the specific target element

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the color of a red button to green",
    "target_element_type": "button",
    "modification_type": "styling",
    "specific_change": "change button color from red to green"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Submit",
      "css_selector": ".submit-btn",
      "confidence": 0.95,
      "reasoning": "Found button with red background-color: #ff0000"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
        {{
            "step_number": 1,
      "action": "modify_css",
      "target_selector": ".submit-btn",
      "property": "background-color",
      "new_value": "#28a745",
      "description": "Change button background from red to green"
    }}
  ],
  "expected_outcome": "The red button will now have a green background"
}}
```

### **Example 3: Semantic-Based Request**
**User Request**: "update the hero section background"

**Analysis**:
- Identifies large banner/hero areas
- Analyzes current background styling
- Determines the main hero section

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Modify the background of the main hero section",
    "target_element_type": "section",
    "modification_type": "styling",
    "specific_change": "update hero section background"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Welcome to Our Platform",
      "css_selector": ".hero-section",
      "confidence": 0.95,
      "reasoning": "Identified large banner section with main headline as hero area"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
                    "step_number": 1,
      "action": "modify_css",
      "target_selector": ".hero-section",
      "property": "background",
      "new_value": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      "description": "Update hero section with gradient background"
    }}
  ],
  "expected_outcome": "The hero section will have a new gradient background"
}}
```

## YOUR TASK

1. **Analyze the complete UI structure** using the HTML and CSS provided
2. **Understand the user's intent** from their request
3. **Identify the target elements** using spatial, visual, and semantic analysis
4. **Generate a precise modification plan** with valid CSS selectors
5. **Handle ambiguity** by providing clarification options if multiple targets match

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

## CRITICAL REQUIREMENTS
- **Use ONLY valid CSS selectors**: `.class-name`, `#id-name`, `tag.class`, `tag#id`
- **NEVER use jQuery selectors**: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
- **Be precise and specific**: Target exactly what the user intends
- **Handle ambiguity gracefully**: Provide clarification options when needed
- **Consider all context**: Spatial, visual, semantic, and functional aspects"""
    
    def _execute_modification_plan(self, modification_plan: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Step 2: Execute the modification plan and generate new code"""
        try:
            self.logger.info(f"⚡ EXECUTOR: Building execution prompt...")
            
            # Build the execution prompt
            prompt = self._build_execution_prompt(modification_plan, html_content, style_css, globals_css)
            
            self.logger.info(f"⚡ EXECUTOR: Sending execution request to Claude Haiku...")
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            self.logger.info(f"⚡ EXECUTOR: Received response from Claude Haiku (length: {len(response)})")
            
            # Parse the execution response
            self.logger.info(f"⚡ EXECUTOR: Parsing execution response...")
            result = self._parse_execution_response(response, html_content, style_css, globals_css)
            
            if result:
                self.logger.info(f"⚡ EXECUTOR: Successfully parsed execution result")
                return {
                    "success": True,
                    "html": result.get("html", html_content),
                    "style_css": result.get("style_css", style_css),
                    "globals_css": result.get("globals_css", globals_css),
                    "changes_summary": result.get("changes_summary", [])
                }
            else:
                self.logger.error(f"⚡ EXECUTOR: Failed to parse execution result from LLM response")
                return {
                    "success": False,
                    "error": "Failed to parse execution result from LLM response"
                }
                
        except Exception as e:
            self.logger.error(f"⚡ EXECUTOR: Error executing modification plan: {e}")
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
- **CRITICAL**: Ensure all CSS selectors are valid and will work in a real browser
- **CRITICAL**: NEVER use placeholder comments like "/* Rest of the CSS remains unchanged */" or "// ... existing code ..."
- **CRITICAL**: NEVER use ellipsis (...) or "and so on" in your code
- **CRITICAL**: If you make ANY changes to a file, return the COMPLETE file content

**SPECIAL INSTRUCTION FOR NO CHANGES:**
- If no changes are needed to a file, return exactly: "no change to this file"
- This is the ONLY acceptable way to indicate no changes needed
- Do NOT use any other placeholder text or descriptions

**EXAMPLES OF CORRECT OUTPUT:**
- If only HTML text changes: Return original CSS files unchanged
- If only CSS changes: Return original HTML unchanged  
- If no changes needed to CSS: Return "no change to this file" for style_css and globals_css
- If no changes needed to HTML: Return "no change to this file" for html
- If you modify CSS: Return the COMPLETE CSS file with all rules, not just the changed parts
- If you modify HTML: Return the COMPLETE HTML file with all elements, not just the changed parts

**FORBIDDEN PHRASES (NEVER USE THESE):**
- "/* Rest of the CSS remains unchanged */"
- "// ... existing code ..."
- "and so on"
- "..."
- "/* unchanged */"
- "/* same as before */"
- Any other placeholder or abbreviated text"""
    
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
            
            # Handle "no change to this file" responses
            if result["style_css"].lower().strip() == "no change to this file":
                self.logger.info("Detected 'no change to this file' for style_css, using original CSS")
                result["style_css"] = original_style
                
            if result["globals_css"].lower().strip() == "no change to this file":
                self.logger.info("Detected 'no change to this file' for globals_css, using original CSS")
                result["globals_css"] = original_globals
                
            if result["html"].lower().strip() == "no change to this file":
                self.logger.info("Detected 'no change to this file' for html, using original HTML")
                result["html"] = original_html
            
            # Validate that no forbidden placeholder phrases are used
            forbidden_phrases = [
                "/* rest of the css remains unchanged */",
                "// ... existing code ...",
                "and so on",
                "/* unchanged */",
                "/* same as before */",
                "/* unchanged */",
                "/* same as before */"
            ]
            
            for field_name, field_content in [("html", result["html"]), ("style_css", result["style_css"]), ("globals_css", result["globals_css"])]:
                field_lower = field_content.lower()
                for phrase in forbidden_phrases:
                    if phrase in field_lower:
                        self.logger.error(f"Detected forbidden placeholder phrase '{phrase}' in {field_name}")
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