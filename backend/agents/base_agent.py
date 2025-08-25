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
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Claude response, handling different content types"""
        if not response.content:
            return ""
        
        # Look for text content in any of the content blocks
        for content in response.content:
            # Handle text content
            if hasattr(content, 'text') and content.text:
                return content.text
        
        # If no text found, handle tool use blocks
        content = response.content[0]
        
        # Handle tool use blocks
        if hasattr(content, 'type') and content.type == 'tool_use':
            # Extract text from tool use block if available
            if hasattr(content, 'input') and content.input:
                return str(content.input)
            elif hasattr(content, 'name'):
                return f"Tool used: {content.name}"
            else:
                return "Tool used"
        
        # Handle other content types
        if hasattr(content, 'type'):
            return f"Content type: {content.type}"
        
        # Fallback
        return str(content)
    
    def call_claude_with_cot(self, prompt: str, image: Optional[str] = None, system_prompt: Optional[str] = None, enable_cot: bool = True, extract_json: bool = False) -> str:
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
                max_tokens=8000  # Set to safe limit for Claude Haiku
            )
            
            # Debug: Log LLM response for all agents inheriting from BaseAgent
            agent_name = self.__class__.__name__
            response_text = self._extract_response_text(response)
            print(f"DEBUG: {agent_name} LLM Response Length: {len(response_text)} chars")
            print(f"DEBUG: {agent_name} LLM Response Preview: {response_text[:200]}...")
            
            # Only log full response if it's very short (for debugging)
            if len(response_text) < 1000:
                print(f"DEBUG: {agent_name} Full Response: {response_text}")
            else:
                print(f"DEBUG: {agent_name} Response truncated for logging (too long)")
            
            # If JSON extraction is requested, parse the response
            if extract_json and enable_cot:
                extracted_json = self._extract_json_from_cot_response(response_text)
                if extracted_json:
                    return extracted_json
            
            return response_text
            
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
THINKING:
[Your step-by-step reasoning here]

ANSWER:
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
    
    def _extract_json_from_cot_response(self, response: str) -> Optional[str]:
        """Extract JSON content from COT response after 'ANSWER:' section"""
        try:
            # Look for the ANSWER section
            if "**ANSWER:**" in response:
                answer_start = response.find("**ANSWER:**") + len("**ANSWER:**")
                answer_content = response[answer_start:].strip()
                
                # Find JSON content within the answer
                if "{" in answer_content and "}" in answer_content:
                    # Find the first complete JSON object
                    brace_count = 0
                    json_start = -1
                    
                    for i, char in enumerate(answer_content):
                        if char == "{":
                            if brace_count == 0:
                                json_start = i
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0 and json_start >= 0:
                                # Found complete JSON object
                                json_content = answer_content[json_start:i+1]
                                return json_content.strip()
                
                # If no JSON found, return the entire answer content
                return answer_content
            
            # If no ANSWER section found, return the original response
            return None
            
        except Exception as e:
            # If parsing fails, return None
            return None
    
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

    def _clean_json_string_enhanced(self, json_str: str) -> str:
        """Clean JSON-ish strings to improve parse success without changing meaning."""
        try:
            # Strip markdown code fences
            json_str = json_str.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            # Remove trailing commas before } or ]
            import re
            json_str = re.sub(r',\s*(\}|\])', r'\1', json_str)
            # Ensure double quotes
            if "'" in json_str and '"' not in json_str:
                json_str = json_str.replace("'", '"')
            return json_str
        except Exception:
            return json_str

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Robust JSON extraction that handles prose, code fences, and partials.

        Strategies:
        - Prefer ```json fenced blocks
        - Balanced brace scan for first complete object/array
        - Fallback to widest { ... } or [ ... ] slice with cleanup
        """
        try:
            import json
            # 1) Code-fenced json block
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end > start:
                    candidate = text[start:end].strip()
                    candidate = self._clean_json_string_enhanced(candidate)
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
            # 2) Balanced braces/brackets scan
            for open_char, close_char in (("{", "}"), ("[", "]")):
                depth = 0
                start_idx = -1
                for i, ch in enumerate(text):
                    if ch == open_char:
                        if depth == 0:
                            start_idx = i
                        depth += 1
                    elif ch == close_char:
                        if depth > 0:
                            depth -= 1
                            if depth == 0 and start_idx >= 0:
                                candidate = text[start_idx:i+1]
                                candidate = self._clean_json_string_enhanced(candidate)
                                try:
                                    return json.loads(candidate)
                                except json.JSONDecodeError:
                                    continue
            # 3) Greedy slice between first { and last }
            if "{" in text and "}" in text:
                s = text.find("{")
                e = text.rfind("}") + 1
                candidate = self._clean_json_string_enhanced(text[s:e])
                try:
                    import json
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
            # 4) Greedy slice between first [ and last ]
            if "[" in text and "]" in text:
                s = text.find("[")
                e = text.rfind("]") + 1
                candidate = self._clean_json_string_enhanced(text[s:e])
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
            return None
        except Exception:
            return None
        
        # Add context information
        if context:
            output["metadata"]["context_used"] = context
        
        return output