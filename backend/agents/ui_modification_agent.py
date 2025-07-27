from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re

class UIModificationAgent(BaseAgent):
    """Agent that understands what users want to change in HTML code"""
    
    def __init__(self):
        system_message = """You are a UI Modification Request Understanding Agent specialized in:
1. Analyzing user feedback and modification requests
2. Converting natural language requests into structured HTML/CSS changes
3. Understanding context and intent behind modification requests
4. Identifying specific elements that need to be modified
5. Generating detailed modification specifications

Always provide clear, actionable modification instructions that can be executed by the UI editing agent."""
        
        super().__init__("UIModification", system_message)
    
    def analyze_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user feedback and generate structured modification request"""
        
        prompt = f"""
        Analyze the following user feedback for UI modifications:
        
        USER FEEDBACK: {user_feedback}
        
        CURRENT TEMPLATE INFO:
        - Title: {current_template.get('title', 'Unknown')}
        - Category: {current_template.get('category', 'Unknown')}
        - Tags: {', '.join(current_template.get('tags', []))}
        
        Please provide a structured analysis in JSON format with the following structure:
        {{
            "modification_type": "string (e.g., layout, styling, content, functionality, color-scheme, typography)",
            "priority": "string (high, medium, low)",
            "affected_elements": ["list", "of", "elements", "to", "modify"],
            "specific_changes": [
                {{
                    "element_selector": "string (CSS selector or element description)",
                    "change_type": "string (e.g., color, size, position, text, layout, add, remove)",
                    "current_value": "string (current state/value)",
                    "new_value": "string (desired new state/value)",
                    "reasoning": "string (why this change is needed)"
                }}
            ],
            "overall_intent": "string (what the user is trying to achieve)",
            "constraints": ["list", "of", "constraints", "or", "limitations"],
            "suggestions": ["list", "of", "additional", "improvements"],
            "confidence_score": 0.85
        }}
        
        Be specific about which elements need to be changed and how. Consider the context and user intent.
        """
        
        response = self.call_claude(prompt)
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return self._get_default_modification_request(user_feedback)
        except json.JSONDecodeError:
            return self._get_default_modification_request(user_feedback)
    
    def _get_default_modification_request(self, user_feedback: str) -> Dict[str, Any]:
        """Return default modification request when analysis fails"""
        return {
            "modification_type": "general",
            "priority": "medium",
            "affected_elements": ["general"],
            "specific_changes": [
                {
                    "element_selector": "general",
                    "change_type": "improvement",
                    "current_value": "current state",
                    "new_value": "improved state",
                    "reasoning": f"User requested: {user_feedback}"
                }
            ],
            "overall_intent": f"Improve the UI based on: {user_feedback}",
            "constraints": ["maintain existing functionality"],
            "suggestions": ["Consider user feedback carefully"],
            "confidence_score": 0.5
        }
    
    def extract_element_selectors(self, html_content: str, modification_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract specific CSS selectors for elements that need modification"""
        
        affected_elements = modification_request.get("affected_elements", [])
        specific_changes = modification_request.get("specific_changes", [])
        
        selectors = []
        
        for change in specific_changes:
            element_selector = change.get("element_selector", "")
            
            # Try to find the actual CSS selector in the HTML
            actual_selector = self._find_actual_selector(html_content, element_selector)
            
            selectors.append({
                "description": element_selector,
                "css_selector": actual_selector,
                "change_type": change.get("change_type", "general"),
                "current_value": change.get("current_value", ""),
                "new_value": change.get("new_value", ""),
                "reasoning": change.get("reasoning", "")
            })
        
        return selectors
    
    def _find_actual_selector(self, html_content: str, element_description: str) -> str:
        """Find actual CSS selector based on element description"""
        
        # Common patterns for finding elements
        patterns = {
            "header": ["header", ".header", "#header", "nav", ".nav", "#nav"],
            "footer": ["footer", ".footer", "#footer"],
            "button": ["button", ".btn", ".button", "[type='button']"],
            "form": ["form", ".form", "#form"],
            "input": ["input", ".input", "[type='text']", "[type='email']", "[type='password']"],
            "title": ["h1", "h2", "h3", ".title", ".heading"],
            "text": ["p", ".text", ".content", "span", "div"],
            "image": ["img", ".image", ".img"],
            "container": [".container", ".wrapper", ".content", "main"],
            "navigation": ["nav", ".nav", ".navigation", ".menu"],
            "logo": [".logo", "#logo", "img[alt*='logo']"],
            "background": ["body", ".background", ".bg", "main"],
            "color": ["*"],  # Color changes can affect multiple elements
            "font": ["*"],   # Font changes can affect multiple elements
        }
        
        # Find the best matching pattern
        for key, selectors in patterns.items():
            if key.lower() in element_description.lower():
                # Check which selectors exist in the HTML
                for selector in selectors:
                    if self._selector_exists_in_html(html_content, selector):
                        return selector
        
        # Fallback to general selector
        return "*"
    
    def _selector_exists_in_html(self, html_content: str, selector: str) -> bool:
        """Check if a CSS selector exists in the HTML content"""
        
        if selector == "*":
            return True
        
        # Simple pattern matching for common selectors
        if selector.startswith("."):
            # Class selector
            class_name = selector[1:]
            return f'class="{class_name}"' in html_content or f"class='{class_name}'" in html_content
        elif selector.startswith("#"):
            # ID selector
            id_name = selector[1:]
            return f'id="{id_name}"' in html_content or f"id='{id_name}'" in html_content
        else:
            # Tag selector
            return f"<{selector}" in html_content
        
        return False
    
    def generate_modification_plan(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed plan for implementing modifications"""
        
        html_content = current_template.get("html_content", "")
        css_content = current_template.get("css_content", "")
        
        # Extract element selectors
        selectors = self.extract_element_selectors(html_content, modification_request)
        
        # Generate modification plan
        plan = {
            "modification_request": modification_request,
            "implementation_steps": [],
            "html_changes": [],
            "css_changes": [],
            "new_elements": [],
            "removed_elements": [],
            "validation_checks": []
        }
        
        for selector in selectors:
            step = self._generate_implementation_step(selector, html_content, css_content)
            plan["implementation_steps"].append(step)
            
            # Categorize changes
            if selector["change_type"] in ["add", "new"]:
                plan["new_elements"].append(selector)
            elif selector["change_type"] in ["remove", "delete"]:
                plan["removed_elements"].append(selector)
            elif selector["change_type"] in ["color", "background", "font", "size", "position"]:
                plan["css_changes"].append(selector)
            else:
                plan["html_changes"].append(selector)
        
        # Add validation checks
        plan["validation_checks"] = self._generate_validation_checks(modification_request)
        
        return plan
    
    def _generate_implementation_step(self, selector: Dict[str, Any], html_content: str, css_content: str) -> Dict[str, Any]:
        """Generate a specific implementation step for a modification"""
        
        change_type = selector["change_type"]
        css_selector = selector["css_selector"]
        
        step = {
            "element": selector["description"],
            "css_selector": css_selector,
            "action": change_type,
            "current_value": selector["current_value"],
            "new_value": selector["new_value"],
            "implementation": "",
            "reasoning": selector["reasoning"]
        }
        
        # Generate implementation details based on change type
        if change_type in ["color", "background-color"]:
            step["implementation"] = f"CSS: {css_selector} {{ {change_type}: {selector['new_value']}; }}"
        elif change_type in ["font-size", "font-family", "font-weight"]:
            step["implementation"] = f"CSS: {css_selector} {{ {change_type}: {selector['new_value']}; }}"
        elif change_type in ["width", "height", "padding", "margin"]:
            step["implementation"] = f"CSS: {css_selector} {{ {change_type}: {selector['new_value']}; }}"
        elif change_type == "text":
            step["implementation"] = f"HTML: Update text content in {css_selector}"
        elif change_type == "add":
            step["implementation"] = f"HTML: Add new element with {css_selector}"
        elif change_type == "remove":
            step["implementation"] = f"HTML: Remove element with {css_selector}"
        else:
            step["implementation"] = f"General modification to {css_selector}"
        
        return step
    
    def _generate_validation_checks(self, modification_request: Dict[str, Any]) -> List[str]:
        """Generate validation checks for the modification"""
        
        checks = []
        
        # General checks
        checks.append("Ensure HTML structure remains valid")
        checks.append("Verify CSS syntax is correct")
        checks.append("Check for broken links or references")
        
        # Specific checks based on modification type
        modification_type = modification_request.get("modification_type", "")
        
        if "color" in modification_type:
            checks.append("Verify color contrast meets accessibility standards")
            checks.append("Ensure color scheme remains consistent")
        
        if "layout" in modification_type:
            checks.append("Verify responsive design still works")
            checks.append("Check for layout breaking on different screen sizes")
        
        if "content" in modification_type:
            checks.append("Verify all text content is readable")
            checks.append("Check for proper text hierarchy")
        
        if "functionality" in modification_type:
            checks.append("Test all interactive elements")
            checks.append("Verify form validation still works")
        
        return checks
    
    def prioritize_modifications(self, modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize modifications based on importance and dependencies"""
        
        # Define priority weights
        priority_weights = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        # Sort modifications by priority
        sorted_modifications = sorted(
            modifications,
            key=lambda x: priority_weights.get(x.get("priority", "medium"), 1),
            reverse=True
        )
        
        return sorted_modifications 