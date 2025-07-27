import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from db import get_db
import json
import base64
from PIL import Image
import io

class SimpleBaseAgent:
    """Simplified base class for all agents without AutoGen dependency"""
    
    def __init__(self, name: str, system_message: str, model: str = "claude-3-5-sonnet-20241022"):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.claude_client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.db = get_db()
    
    def call_claude(self, prompt: str, image: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Call Claude API with optional image input"""
        try:
            messages = []
            
            # Use agent's system message if no specific one provided
            if system_prompt:
                messages.append({"role": "user", "content": system_prompt})
            elif self.system_message:
                messages.append({"role": "user", "content": self.system_message})
            
            if image:
                # Handle base64 image
                if image.startswith('data:image'):
                    # Remove data URL prefix
                    image_data = image.split(',')[1]
                else:
                    image_data = image
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": prompt})
            
            response = self.claude_client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=4000
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return f"Error: {str(e)}"
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get UI templates by category from database"""
        try:
            templates = list(self.db.templates.find({"category": category}))
            return templates
        except Exception as e:
            print(f"Error fetching templates: {e}")
            return []
    
    def save_template(self, template_data: Dict[str, Any]) -> str:
        """Save a new template to database"""
        try:
            from datetime import datetime
            template_data["created_at"] = datetime.utcnow()
            template_data["updated_at"] = datetime.utcnow()
            result = self.db.templates.insert_one(template_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving template: {e}")
            return None
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing template"""
        try:
            from datetime import datetime
            updates["updated_at"] = datetime.utcnow()
            result = self.db.templates.update_one(
                {"_id": template_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating template: {e}")
            return False 