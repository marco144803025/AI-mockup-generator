"""
Tools Layer - External system integration capabilities
"""

import logging
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from dataclasses import dataclass
from enum import Enum
import requests
import os

T = TypeVar('T')

class ToolType(Enum):
    """Types of tools available"""
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    TEMPLATE_GENERATION = "template_generation"
    IMAGE_PROCESSING = "image_processing"
    VALIDATION = "validation"
    NOTIFICATION = "notification"

@dataclass
class ToolCall:
    """Represents a tool call"""
    id: str
    tool_name: str
    tool_type: ToolType
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class ToolsLayer:
    """Handles external system integration and tool execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registered_tools: Dict[str, Callable] = {}
        self.tool_call_history: List[ToolCall] = []
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Register default tools
        self._register_default_tools()
    
    def register_tool(self, name: str, func: Callable, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register a new tool"""
        try:
            self.registered_tools[name] = func
            self.tool_metadata[name] = metadata or {}
            self.logger.info(f"Registered tool: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register tool {name}: {e}")
            return False
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolCall:
        """Execute a registered tool"""
        import time
        
        tool_call = ToolCall(
            id=f"tool_{int(time.time())}_{tool_name}",
            tool_name=tool_name,
            tool_type=self.tool_metadata.get(tool_name, {}).get("type", ToolType.API_CALL),
            parameters=parameters
        )
        
        if tool_name not in self.registered_tools:
            tool_call.error = f"Tool '{tool_name}' not found"
            self.tool_call_history.append(tool_call)
            return tool_call
        
        start_time = time.time()
        
        try:
            func = self.registered_tools[tool_name]
            
            # Execute the tool
            if asyncio.iscoroutinefunction(func):
                result = asyncio.run(func(**parameters))
            else:
                result = func(**parameters)
            
            tool_call.result = result
            tool_call.execution_time = time.time() - start_time
            
            self.logger.info(f"Tool {tool_name} executed successfully in {tool_call.execution_time:.2f}s")
            
        except Exception as e:
            tool_call.error = str(e)
            tool_call.execution_time = time.time() - start_time
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
        
        self.tool_call_history.append(tool_call)
        return tool_call
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with metadata"""
        tools = []
        for name, func in self.registered_tools.items():
            metadata = self.tool_metadata.get(name, {})
            tools.append({
                "name": name,
                "type": metadata.get("type", ToolType.API_CALL).value,
                "description": metadata.get("description", ""),
                "parameters": metadata.get("parameters", {}),
                "examples": metadata.get("examples", [])
            })
        return tools
    
    def _register_default_tools(self):
        """Register default tools"""
        
        # Database query tool
        self.register_tool(
            "query_database",
            self._query_database_tool,
            {
                "type": ToolType.DATABASE_QUERY,
                "description": "Query the template database",
                "parameters": {
                    "query_type": "string (find, distinct, count)",
                    "collection": "string (templates, categories, etc.)",
                    "filters": "dict (optional query filters)",
                    "limit": "int (optional result limit)"
                },
                "examples": [
                    {"query_type": "find", "collection": "templates", "filters": {"category": "login"}},
                    {"query_type": "distinct", "collection": "templates", "filters": {"field": "category"}}
                ]
            }
        )
        
        # Template generation tool
        self.register_tool(
            "generate_template",
            self._generate_template_tool,
            {
                "type": ToolType.TEMPLATE_GENERATION,
                "description": "Generate HTML/CSS template",
                "parameters": {
                    "template_type": "string (login, signup, profile, etc.)",
                    "style_preferences": "dict (color scheme, layout, etc.)",
                    "features": "list (required features)"
                },
                "examples": [
                    {"template_type": "login", "style_preferences": {"theme": "dark"}, "features": ["social_login"]}
                ]
            }
        )
        
        # Image processing tool
        self.register_tool(
            "process_image",
            self._process_image_tool,
            {
                "type": ToolType.IMAGE_PROCESSING,
                "description": "Process and analyze images",
                "parameters": {
                    "image_data": "string (base64 encoded image)",
                    "operation": "string (analyze, resize, convert)",
                    "options": "dict (processing options)"
                },
                "examples": [
                    {"image_data": "base64...", "operation": "analyze", "options": {"extract_colors": True}}
                ]
            }
        )
        
        # API call tool
        self.register_tool(
            "make_api_call",
            self._make_api_call_tool,
            {
                "type": ToolType.API_CALL,
                "description": "Make external API calls",
                "parameters": {
                    "url": "string (API endpoint)",
                    "method": "string (GET, POST, PUT, DELETE)",
                    "headers": "dict (optional headers)",
                    "data": "dict (optional request data)"
                },
                "examples": [
                    {"url": "https://api.example.com/data", "method": "GET", "headers": {"Authorization": "Bearer token"}}
                ]
            }
        )
        
        # File operation tool
        self.register_tool(
            "file_operation",
            self._file_operation_tool,
            {
                "type": ToolType.FILE_OPERATION,
                "description": "Perform file operations",
                "parameters": {
                    "operation": "string (read, write, delete, list)",
                    "file_path": "string (file path)",
                    "content": "string (for write operations)"
                },
                "examples": [
                    {"operation": "read", "file_path": "/templates/login.html"},
                    {"operation": "write", "file_path": "/output/template.html", "content": "<html>...</html>"}
                ]
            }
        )
        
        # Notification tool
        self.register_tool(
            "send_notification",
            self._send_notification_tool,
            {
                "type": ToolType.NOTIFICATION,
                "description": "Send notifications to users",
                "parameters": {
                    "notification_type": "string (email, push, in_app)",
                    "recipient": "string (user identifier)",
                    "message": "string (notification message)",
                    "data": "dict (additional notification data)"
                },
                "examples": [
                    {"notification_type": "in_app", "recipient": "user123", "message": "Template ready for review"}
                ]
            }
        )
    
    # Default tool implementations
    def _query_database_tool(self, query_type: str, collection: str, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Query the database"""
        try:
            from db import get_db
            db = get_db()
            
            if query_type == "find":
                cursor = db[collection].find(filters or {})
                if limit:
                    cursor = cursor.limit(limit)
                results = list(cursor)
                return {"success": True, "results": results, "count": len(results)}
            
            elif query_type == "distinct":
                field = filters.get("field") if filters else None
                if not field:
                    return {"success": False, "error": "Field parameter required for distinct query"}
                
                results = db[collection].distinct(field)
                return {"success": True, "results": results, "count": len(results)}
            
            elif query_type == "count":
                count = db[collection].count_documents(filters or {})
                return {"success": True, "count": count}
            
            else:
                return {"success": False, "error": f"Unknown query type: {query_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_template_tool(self, template_type: str, style_preferences: Dict[str, Any], features: List[str]) -> Dict[str, Any]:
        """Generate a template"""
        try:
            # This would integrate with your template generation logic
            template_data = {
                "type": template_type,
                "html": f"<html><body><h1>{template_type.title()} Template</h1></body></html>",
                "css": f"body {{ background-color: {style_preferences.get('theme', 'light')}; }}",
                "features": features,
                "generated_at": "2024-01-01T00:00:00Z"
            }
            
            return {"success": True, "template": template_data}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _process_image_tool(self, image_data: str, operation: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process images"""
        try:
            # This would integrate with image processing libraries
            if operation == "analyze":
                # Analyze image for colors, content, etc.
                analysis = {
                    "colors": ["#000000", "#ffffff"],
                    "content_type": "logo",
                    "dimensions": {"width": 200, "height": 200}
                }
                return {"success": True, "analysis": analysis}
            
            elif operation == "resize":
                # Resize image
                return {"success": True, "resized_image": "base64_resized_image_data"}
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _make_api_call_tool(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make external API calls"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                timeout=30
            )
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _file_operation_tool(self, operation: str, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Perform file operations"""
        try:
            if operation == "read":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return {"success": True, "content": f.read()}
            
            elif operation == "write":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content or "")
                return {"success": True, "message": f"File written to {file_path}"}
            
            elif operation == "delete":
                import os
                os.remove(file_path)
                return {"success": True, "message": f"File deleted: {file_path}"}
            
            elif operation == "list":
                import os
                files = os.listdir(file_path)
                return {"success": True, "files": files}
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_notification_tool(self, notification_type: str, recipient: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send notifications"""
        try:
            # This would integrate with your notification system
            notification = {
                "type": notification_type,
                "recipient": recipient,
                "message": message,
                "data": data or {},
                "sent_at": "2024-01-01T00:00:00Z"
            }
            
            return {"success": True, "notification": notification}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tool_call_history(self, tool_name: Optional[str] = None) -> List[ToolCall]:
        """Get tool call history"""
        if tool_name:
            return [call for call in self.tool_call_history if call.tool_name == tool_name]
        return self.tool_call_history
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        stats = {}
        for tool_name in self.registered_tools.keys():
            calls = [call for call in self.tool_call_history if call.tool_name == tool_name]
            successful_calls = [call for call in calls if not call.error]
            
            stats[tool_name] = {
                "total_calls": len(calls),
                "successful_calls": len(successful_calls),
                "success_rate": len(successful_calls) / len(calls) if calls else 0,
                "average_execution_time": sum(call.execution_time or 0 for call in calls) / len(calls) if calls else 0
            }
        
        return stats 