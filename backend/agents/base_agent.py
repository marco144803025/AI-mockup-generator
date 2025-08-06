import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from db import get_db
import json
import base64
from PIL import Image
import io
from datetime import datetime

class BaseAgent:
    # Base class for all agents with common functionality
    
    def __init__(self, name: str, system_message: str, model: str = "claude-3-5-haiku-20241022"):
        self.name = name
        self.model = model
        self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.db = get_db()
    
    def call_claude_with_cot(self, prompt: str, image: Optional[str] = None, system_prompt: Optional[str] = None, enable_cot: bool = True) -> str:
        """Call Claude API with chain-of-thought reasoning"""
        try:
            # Enhance prompt with CoT instructions if enabled
            if enable_cot:
                enhanced_prompt = self._add_cot_instructions(prompt)
            else:
                enhanced_prompt = prompt
            
            messages = []
            
            if system_prompt:
                messages.append({"role": "user", "content": system_prompt})
            
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
                        {"type": "text", "text": enhanced_prompt},
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
                messages.append({"role": "user", "content": enhanced_prompt})
            
            response = self.claude_client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=8000
            )
            
            # Debug: Log LLM response for all agents inheriting from BaseAgent
            agent_name = self.__class__.__name__
            print(f"DEBUG: {agent_name} LLM Response: {response.content[0].text[:500]}...")
            if len(response.content[0].text) > 500:
                print(f"DEBUG: Full {agent_name} Response: {response.content[0].text}")
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return f"Error: {str(e)}"
    
    def _add_cot_instructions(self, prompt: str) -> str:
        """Add chain-of-thought instructions to the prompt"""
        cot_instruction = """
IMPORTANT: Use Chain-of-Thought reasoning. Before providing your final answer, think through the problem step by step:

1. **ANALYZE**: What is the user asking for? What are the key requirements?
2. **CONSIDER**: What constraints and context should I keep in mind?
3. **REASON**: What are the logical steps to solve this problem?
4. **EVALUATE**: What are the pros and cons of different approaches?
5. **DECIDE**: What is the best solution based on my reasoning?
6. **EXPLAIN**: Provide clear reasoning for my decision.

Format your response as:
**THINKING:**
[Your step-by-step reasoning here]

**ANSWER:**
[Your final structured answer here]
"""
        
        return f"{prompt}\n\n{cot_instruction}"
    
    def call_claude(self, prompt: str, image: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Call Claude API with optional image input (legacy method)"""
        return self.call_claude_with_cot(prompt, image, system_prompt, enable_cot=False)
    
    def process_cot_response(self, response: str) -> Dict[str, str]:
        """Extract thinking and answer from CoT response"""
        thinking = ""
        answer = response
        
        # Try to extract thinking section
        if "**THINKING:**" in response and "**ANSWER:**" in response:
            parts = response.split("**THINKING:**")
            if len(parts) > 1:
                thinking_answer = parts[1].split("**ANSWER:**")
                if len(thinking_answer) > 1:
                    thinking = thinking_answer[0].strip()
                    answer = thinking_answer[1].strip()
        
        return {
            "thinking": thinking,
            "answer": answer,
            "full_response": response
        }
    
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
    
    def process_tool_results(self, tool_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process tool results and return final output - to be overridden by specific agents"""
        # Default implementation - return tool results as-is
        return tool_result.get("tool_results", [])
    
    def create_standardized_response(self, success: bool, data: Dict[str, Any], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a standardized response structure for all agents"""
        
        if metadata is None:
            metadata = {}
        
        return {
            "success": success,
            "data": {
                "primary_result": data.get("primary_result", data),
                "confidence_score": data.get("confidence_score", 0.0),
                "reasoning": data.get("reasoning", ""),
                "suggested_next_actions": data.get("suggested_next_actions", []),
                "requires_clarification": data.get("requires_clarification", False),
                "clarification_questions": data.get("clarification_questions", [])
            },
            "metadata": {
                "agent_name": self.name,
                "execution_time": metadata.get("execution_time", 0.0),
                "context_used": metadata.get("context_used", {}),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat())
            }
        }
    
    def validate_agent_output(self, output: Dict[str, Any]) -> bool:
        """Validate that agent output follows standardized structure"""
        
        required_keys = ["success", "data"]
        data_required_keys = ["primary_result"]
        
        # Check top-level structure
        if not all(key in output for key in required_keys):
            return False
        
        # Check data structure
        if not all(key in output["data"] for key in data_required_keys):
            return False
        
        return True
    
    def enhance_agent_output(self, output: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance agent output with additional context and validation"""
        
        # If output is not standardized, convert it
        if not self.validate_agent_output(output):
            # Assume it's a simple result, wrap it in standardized structure
            output = self.create_standardized_response(
                success=True,
                data={"primary_result": output},
                metadata={"context_used": context or {}}
            )
        
        # Add context information
        if context:
            output["metadata"]["context_used"] = context
        
        return output
        
        # Add context information
        if context:
            output["metadata"]["context_used"] = context
        
        return output