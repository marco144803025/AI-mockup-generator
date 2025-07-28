"""
Intelligence Layer - LLM calling and response handling
"""

import logging
import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import anthropic
import os

class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class ResponseFormat(Enum):
    """Response format types"""
    TEXT = "text"
    JSON = "json"
    FUNCTION_CALL = "function_call"
    STRUCTURED = "structured"

@dataclass
class LLMRequest:
    """Represents an LLM request"""
    prompt: str
    system_prompt: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1000
    temperature: float = 0.7
    response_format: ResponseFormat = ResponseFormat.TEXT
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMResponse:
    """Represents an LLM response"""
    content: str
    usage: Dict[str, Any]
    model: str
    response_format: ResponseFormat
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class IntelligenceLayer:
    """Handles LLM calling and response processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.response_processors: Dict[ResponseFormat, Callable] = {
            ResponseFormat.TEXT: self._process_text_response,
            ResponseFormat.JSON: self._process_json_response,
            ResponseFormat.FUNCTION_CALL: self._process_function_call_response,
            ResponseFormat.STRUCTURED: self._process_structured_response
        }
        
    async def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Call the LLM with the given request"""
        try:
            self.logger.info(f"Calling LLM with model: {request.model}")
            
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "user", "content": f"[System: {request.system_prompt}]\n\n{request.prompt}"})
            else:
                messages.append({"role": "user", "content": request.prompt})
            
            # Call Claude API
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=messages
            )
            
            # Extract content
            if isinstance(response.content, list):
                content = " ".join([block.text for block in response.content if hasattr(block, 'text')])
            else:
                content = str(response.content)
            
            # Process response based on format
            processor = self.response_processors.get(request.response_format, self._process_text_response)
            processed_content = processor(content)
            
            return LLMResponse(
                content=processed_content,
                usage=dict(response.usage) if hasattr(response, 'usage') else {},
                model=request.model,
                response_format=request.response_format,
                tool_calls=getattr(response, 'tool_calls', None),
                metadata=request.metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            return LLMResponse(
                content="",
                usage={},
                model=request.model,
                response_format=request.response_format,
                error=str(e)
            )
    
    def _process_text_response(self, content: str) -> str:
        """Process text response"""
        return content.strip()
    
    def _process_json_response(self, content: str) -> Dict[str, Any]:
        """Process JSON response"""
        try:
            # Try to extract JSON from response
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Failed to parse JSON response", "raw_content": content}
    
    def _process_function_call_response(self, content: str) -> Dict[str, Any]:
        """Process function call response"""
        # This would be handled by the tools layer
        return {"content": content, "function_calls": []}
    
    def _process_structured_response(self, content: str) -> Dict[str, Any]:
        """Process structured response (markdown, etc.)"""
        # Parse structured content like markdown tables, lists, etc.
        structured_data = {
            "content": content,
            "sections": self._extract_sections(content),
            "lists": self._extract_lists(content),
            "tables": self._extract_tables(content)
        }
        return structured_data
    
    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections from markdown content"""
        sections = []
        lines = content.split('\n')
        current_section = {"title": "", "content": ""}
        
        for line in lines:
            if line.startswith('#'):
                if current_section["title"]:
                    sections.append(current_section)
                current_section = {"title": line.strip('# '), "content": ""}
            else:
                current_section["content"] += line + '\n'
        
        if current_section["title"]:
            sections.append(current_section)
        
        return sections
    
    def _extract_lists(self, content: str) -> List[List[str]]:
        """Extract lists from content"""
        lists = []
        lines = content.split('\n')
        current_list = []
        
        for line in lines:
            if line.strip().startswith(('-', '*', '1.', '2.', '3.')):
                current_list.append(line.strip())
            elif current_list and line.strip():
                current_list.append(line.strip())
            elif current_list:
                lists.append(current_list)
                current_list = []
        
        if current_list:
            lists.append(current_list)
        
        return lists
    
    def _extract_tables(self, content: str) -> List[List[List[str]]]:
        """Extract tables from markdown content"""
        tables = []
        lines = content.split('\n')
        current_table = []
        in_table = False
        
        for line in lines:
            if '|' in line:
                if not in_table:
                    in_table = True
                row = [cell.strip() for cell in line.split('|')[1:-1]]
                current_table.append(row)
            elif in_table:
                tables.append(current_table)
                current_table = []
                in_table = False
        
        if current_table:
            tables.append(current_table)
        
        return tables
    
    def create_system_prompt(self, role: str, constraints: Dict[str, Any], examples: Optional[List[str]] = None) -> str:
        """Create a system prompt with role, constraints, and examples"""
        prompt = f"You are a {role}.\n\n"
        
        if constraints:
            prompt += "CONSTRAINTS:\n"
            for key, value in constraints.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        if examples:
            prompt += "EXAMPLES:\n"
            for i, example in enumerate(examples, 1):
                prompt += f"{i}. {example}\n"
            prompt += "\n"
        
        prompt += "Please respond according to your role and the given constraints."
        return prompt
    
    def validate_response(self, response: LLMResponse, expected_format: ResponseFormat) -> bool:
        """Validate LLM response format and content"""
        if response.error:
            return False
        
        if response.response_format != expected_format:
            return False
        
        if expected_format == ResponseFormat.JSON:
            try:
                json.loads(response.content)
                return True
            except json.JSONDecodeError:
                return False
        
        return True
    
    def extract_structured_data(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from LLM response based on schema"""
        try:
            # Try to parse as JSON first
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            # Validate against schema
            validated_data = {}
            for key, expected_type in schema.items():
                if key in data:
                    if isinstance(data[key], expected_type):
                        validated_data[key] = data[key]
                    else:
                        self.logger.warning(f"Type mismatch for {key}: expected {expected_type}, got {type(data[key])}")
                        validated_data[key] = None
                else:
                    validated_data[key] = None
            
            return validated_data
            
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Failed to extract structured data: {e}")
            return {key: None for key in schema.keys()}
    
    def create_conversation_context(self, messages: List[Dict[str, str]], max_tokens: int = 4000) -> str:
        """Create conversation context from message history"""
        context = ""
        token_count = 0
        
        # Start from most recent messages and work backwards
        for message in reversed(messages):
            message_text = f"{message['role']}: {message['content']}\n"
            estimated_tokens = len(message_text.split()) * 1.3  # Rough estimation
            
            if token_count + estimated_tokens > max_tokens:
                break
            
            context = message_text + context
            token_count += estimated_tokens
        
        return context.strip() 