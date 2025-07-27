from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from bs4 import BeautifulSoup

class UIEditingAgent(BaseAgent):
    """Agent that modifies UI templates based on modification requests"""
    
    def __init__(self):
        system_message = """You are a UI Editing Agent specialized in:
1. Modifying HTML and CSS code based on structured requests
2. Maintaining code quality and best practices
3. Ensuring responsive design and accessibility
4. Implementing changes while preserving existing functionality
5. Generating clean, maintainable code

Always follow web standards and ensure the modified code is valid and functional."""
        
        super().__init__("UIEditing", system_message)
    
    def apply_modifications(self, template: Dict[str, Any], modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply modifications to the template based on the modification plan"""
        
        html_content = template.get("html_content", "")
        css_content = template.get("css_content", "")
        
        # Apply modifications
        modified_html = self._apply_html_modifications(html_content, modification_plan)
        modified_css = self._apply_css_modifications(css_content, modification_plan)
        
        # Create modified template
        modified_template = template.copy()
        modified_template["html_content"] = modified_html
        modified_template["css_content"] = modified_css
        modified_template["modification_history"] = template.get("modification_history", []) + [modification_plan]
        
        return modified_template
    
    def _apply_html_modifications(self, html_content: str, modification_plan: Dict[str, Any]) -> str:
        """Apply HTML modifications based on the plan"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Apply each modification step
            for step in modification_plan.get("implementation_steps", []):
                if step["action"] in ["text", "add", "remove"]:
                    self._apply_html_step(soup, step)
            
            return str(soup)
        except Exception as e:
            print(f"Error applying HTML modifications: {e}")
            return html_content
    
    def _apply_html_step(self, soup: BeautifulSoup, step: Dict[str, Any]):
        """Apply a single HTML modification step"""
        
        action = step["action"]
        css_selector = step["css_selector"]
        new_value = step["new_value"]
        
        if action == "text":
            # Update text content
            elements = soup.select(css_selector)
            for element in elements:
                element.string = new_value
        
        elif action == "add":
            # Add new element
            new_element = soup.new_tag("div")
            new_element.string = new_value
            if css_selector != "*":
                new_element["class"] = css_selector.replace(".", "")
            soup.body.append(new_element) if soup.body else soup.append(new_element)
        
        elif action == "remove":
            # Remove element
            elements = soup.select(css_selector)
            for element in elements:
                element.decompose()
    
    def _apply_css_modifications(self, css_content: str, modification_plan: Dict[str, Any]) -> str:
        """Apply CSS modifications based on the plan"""
        
        # Parse existing CSS
        css_rules = self._parse_css(css_content)
        
        # Apply each modification step
        for step in modification_plan.get("implementation_steps", []):
            if step["action"] in ["color", "background-color", "font-size", "font-family", "font-weight", "width", "height", "padding", "margin"]:
                self._apply_css_step(css_rules, step)
        
        # Generate new CSS content
        return self._generate_css(css_rules)
    
    def _parse_css(self, css_content: str) -> Dict[str, Dict[str, str]]:
        """Parse CSS content into a structured format"""
        
        css_rules = {}
        
        # Simple CSS parsing (this could be enhanced with a proper CSS parser)
        rule_pattern = r'([^{}]+)\s*\{([^{}]+)\}'
        matches = re.findall(rule_pattern, css_content, re.DOTALL)
        
        for selector, properties in matches:
            selector = selector.strip()
            css_rules[selector] = {}
            
            # Parse properties
            prop_pattern = r'([^:]+):\s*([^;]+);'
            prop_matches = re.findall(prop_pattern, properties)
            
            for prop_name, prop_value in prop_matches:
                css_rules[selector][prop_name.strip()] = prop_value.strip()
        
        return css_rules
    
    def _apply_css_step(self, css_rules: Dict[str, Dict[str, str]], step: Dict[str, Any]):
        """Apply a single CSS modification step"""
        
        css_selector = step["css_selector"]
        action = step["action"]
        new_value = step["new_value"]
        
        # Find or create the CSS rule
        if css_selector not in css_rules:
            css_rules[css_selector] = {}
        
        # Apply the property
        css_rules[css_selector][action] = new_value
    
    def _generate_css(self, css_rules: Dict[str, Dict[str, str]]) -> str:
        """Generate CSS content from structured rules"""
        
        css_content = ""
        
        for selector, properties in css_rules.items():
            css_content += f"{selector} {{\n"
            for prop_name, prop_value in properties.items():
                css_content += f"    {prop_name}: {prop_value};\n"
            css_content += "}\n\n"
        
        return css_content
    
    def validate_modifications(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that modifications are correct and don't break functionality"""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "changes_summary": []
        }
        
        # Check HTML validity
        html_validation = self._validate_html(modified_template["html_content"])
        if not html_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(html_validation["errors"])
        
        # Check CSS validity
        css_validation = self._validate_css(modified_template["css_content"])
        if not css_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(css_validation["errors"])
        
        # Check for broken references
        reference_validation = self._validate_references(original_template, modified_template)
        validation_result["warnings"].extend(reference_validation["warnings"])
        
        # Generate changes summary
        validation_result["changes_summary"] = self._generate_changes_summary(original_template, modified_template)
        
        return validation_result
    
    def _validate_html(self, html_content: str) -> Dict[str, Any]:
        """Validate HTML content"""
        
        result = {"is_valid": True, "errors": []}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for unclosed tags
            if soup.find_all(True):
                # Basic validation passed
                pass
            else:
                result["errors"].append("No valid HTML content found")
                result["is_valid"] = False
                
        except Exception as e:
            result["errors"].append(f"HTML parsing error: {str(e)}")
            result["is_valid"] = False
        
        return result
    
    def _validate_css(self, css_content: str) -> Dict[str, Any]:
        """Validate CSS content"""
        
        result = {"is_valid": True, "errors": []}
        
        # Basic CSS validation
        if not css_content.strip():
            result["errors"].append("Empty CSS content")
            result["is_valid"] = False
            return result
        
        # Check for basic CSS syntax
        if not re.search(r'[^{}]+{[^}]+}', css_content):
            result["errors"].append("Invalid CSS syntax")
            result["is_valid"] = False
        
        return result
    
    def _validate_references(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that references and links are still intact"""
        
        result = {"warnings": []}
        
        original_html = original_template.get("html_content", "")
        modified_html = modified_template.get("html_content", "")
        
        # Check for broken image references
        original_images = re.findall(r'src=["\']([^"\']+)["\']', original_html)
        modified_images = re.findall(r'src=["\']([^"\']+)["\']', modified_html)
        
        for img in original_images:
            if img not in modified_images:
                result["warnings"].append(f"Image reference removed: {img}")
        
        # Check for broken link references
        original_links = re.findall(r'href=["\']([^"\']+)["\']', original_html)
        modified_links = re.findall(r'href=["\']([^"\']+)["\']', modified_html)
        
        for link in original_links:
            if link not in modified_links:
                result["warnings"].append(f"Link reference removed: {link}")
        
        return result
    
    def _generate_changes_summary(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> List[str]:
        """Generate a summary of changes made"""
        
        summary = []
        
        # Compare HTML content
        original_html = original_template.get("html_content", "")
        modified_html = modified_template.get("html_content", "")
        
        if original_html != modified_html:
            summary.append("HTML content modified")
        
        # Compare CSS content
        original_css = original_template.get("css_content", "")
        modified_css = modified_template.get("css_content", "")
        
        if original_css != modified_css:
            summary.append("CSS content modified")
        
        # Count modification history
        modification_history = modified_template.get("modification_history", [])
        if modification_history:
            summary.append(f"Applied {len(modification_history)} modification(s)")
        
        return summary
    
    def generate_preview(self, template: Dict[str, Any]) -> str:
        """Generate a preview of the modified template"""
        
        html_content = template.get("html_content", "")
        css_content = template.get("css_content", "")
        
        # Create a complete HTML document for preview
        preview_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Template Preview</title>
    <style>
        {css_content}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
        """
        
        return preview_html
    
    def create_backup(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Create a backup of the template before modifications"""
        
        backup = {
            "original_template": template.copy(),
            "backup_timestamp": "2024-01-01T00:00:00Z",  # This should be actual timestamp
            "backup_reason": "Pre-modification backup"
        }
        
        return backup 