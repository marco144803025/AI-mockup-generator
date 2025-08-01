"""
UI Preview Tools - Functions for generating and displaying UI template previews
"""

import logging
import base64
import json
from typing import Dict, List, Any, Optional
from db import get_db
from bson import ObjectId

class UIPreviewTools:
    """UI Preview tool functions that can be called by agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = get_db()
    
    def generate_ui_preview(self, template_id: str) -> Dict[str, Any]:
        """Generate a complete UI preview from template code"""
        try:
            # Get template from database
            template = self.db.templates.find_one({"_id": ObjectId(template_id)})
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template with ID '{template_id}' not found",
                    "agent_response": f"I couldn't find the template you're referring to. Please check the template ID and try again."
                }
            
            # Extract code files
            html_code = template.get("html_export", "")
            global_css = template.get("global_css", "")
            style_css = template.get("style_css", "")
            
            if not html_code:
                return {
                    "success": False,
                    "error": "Template HTML code not found",
                    "agent_response": "This template doesn't have the required HTML code for preview generation."
                }
            
            # Combine CSS files
            combined_css = f"{global_css}\n{style_css}".strip()
            
            # Create complete HTML document
            complete_html = self._create_complete_html(html_code, combined_css)
            
            # Generate preview data
            preview_data = {
                "template_id": str(template["_id"]),
                "template_name": template.get("name", "Unknown Template"),
                "category": template.get("category", "unknown"),
                "html_code": html_code,
                "css_code": combined_css,
                "complete_html": complete_html,
                "preview_url": self._generate_preview_url(complete_html),
                "code_summary": self._generate_code_summary(html_code, combined_css)
            }
            
            return {
                "success": True,
                "preview_data": preview_data,
                "template_info": {
                    "name": template.get("name", "Unknown"),
                    "category": template.get("category", "unknown"),
                    "description": template.get("metadata", {}).get("description", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating UI preview: {e}")
            return {
                "success": False,
                "error": f"Preview generation failed: {str(e)}",
                "agent_response": "I encountered an error while generating the UI preview. Please try again."
            }
    
    def _create_complete_html(self, html_code: str, css_code: str) -> str:
        """Create a complete HTML document with embedded CSS"""
        # If html_code already has DOCTYPE, use it as is
        if html_code.strip().startswith("<!DOCTYPE"):
            # Insert CSS into existing HTML
            if "<head>" in html_code:
                # Insert CSS into head section
                css_insert = f'<style>\n{css_code}\n</style>'
                head_end = html_code.find("</head>")
                if head_end != -1:
                    return html_code[:head_end] + css_insert + html_code[head_end:]
                else:
                    # No head section, insert at beginning
                    return f'<head>\n{css_insert}\n</head>\n{html_code}'
            else:
                # No head section, wrap with head
                return f'<!DOCTYPE html>\n<html>\n<head>\n<style>\n{css_code}\n</style>\n</head>\n<body>\n{html_code}\n</body>\n</html>'
        else:
            # Create complete HTML document
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Template Preview</title>
    <style>
{css_code}
    </style>
</head>
<body>
{html_code}
</body>
</html>"""
    
    def _generate_preview_url(self, html_content: str) -> str:
        """Generate a data URL for the HTML preview"""
        try:
            # Encode HTML content as base64
            html_bytes = html_content.encode('utf-8')
            html_b64 = base64.b64encode(html_bytes).decode('utf-8')
            return f"data:text/html;base64,{html_b64}"
        except Exception as e:
            self.logger.error(f"Error generating preview URL: {e}")
            return ""
    
    def _generate_code_summary(self, html_code: str, css_code: str) -> Dict[str, Any]:
        """Generate a summary of the code structure"""
        try:
            # Analyze HTML structure
            html_lines = html_code.split('\n')
            html_elements = []
            for line in html_lines:
                line = line.strip()
                if line.startswith('<') and not line.startswith('<!--'):
                    # Extract element name
                    element = line.split()[0].lstrip('<').split('>')[0].split('/')[0]
                    if element and element not in ['!DOCTYPE', 'html', 'head', 'body', 'style']:
                        html_elements.append(element)
            
            # Analyze CSS
            css_lines = css_code.split('\n')
            css_classes = []
            for line in css_lines:
                line = line.strip()
                if line.startswith('.'):
                    class_name = line.split('{')[0].strip()
                    css_classes.append(class_name)
            
            return {
                "html_elements": list(set(html_elements))[:10],  # Top 10 unique elements
                "css_classes": list(set(css_classes))[:10],      # Top 10 unique classes
                "html_lines": len(html_lines),
                "css_lines": len(css_lines),
                "total_size": len(html_code) + len(css_code)
            }
        except Exception as e:
            self.logger.error(f"Error generating code summary: {e}")
            return {
                "html_elements": [],
                "css_classes": [],
                "html_lines": 0,
                "css_lines": 0,
                "total_size": 0
            }
    
    def get_template_code(self, template_id: str) -> Dict[str, Any]:
        """Get raw template code files"""
        try:
            template = self.db.templates.find_one({"_id": ObjectId(template_id)})
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template with ID '{template_id}' not found"
                }
            
            return {
                "success": True,
                "template_id": str(template["_id"]),
                "template_name": template.get("name", "Unknown"),
                "html_export": template.get("html_export", ""),
                "global_css": template.get("global_css", ""),
                "style_css": template.get("style_css", ""),
                "metadata": template.get("metadata", {})
            }
            
        except Exception as e:
            self.logger.error(f"Error getting template code: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve template code: {str(e)}"
            }
    
    def validate_template_code(self, template_id: str) -> Dict[str, Any]:
        """Validate that template has all required code files"""
        try:
            template = self.db.templates.find_one({"_id": ObjectId(template_id)})
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template with ID '{template_id}' not found"
                }
            
            html_code = template.get("html_export", "")
            global_css = template.get("global_css", "")
            style_css = template.get("style_css", "")
            
            validation_results = {
                "has_html": bool(html_code.strip()),
                "has_global_css": bool(global_css.strip()),
                "has_style_css": bool(style_css.strip()),
                "html_length": len(html_code),
                "global_css_length": len(global_css),
                "style_css_length": len(style_css)
            }
            
            # Check if template is complete
            is_complete = validation_results["has_html"] and (validation_results["has_global_css"] or validation_results["has_style_css"])
            
            return {
                "success": True,
                "template_id": str(template["_id"]),
                "template_name": template.get("name", "Unknown"),
                "is_complete": is_complete,
                "validation_results": validation_results,
                "missing_files": [k for k, v in validation_results.items() if not v and k.startswith("has_")]
            }
            
        except Exception as e:
            self.logger.error(f"Error validating template code: {e}")
            return {
                "success": False,
                "error": f"Validation failed: {str(e)}"
            } 