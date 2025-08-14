"""
Tool Utility - Shared utility for tool calling that agents can use
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .mongodb_tools import MongoDBTools
from .ui_preview_tools import UIPreviewTools
from .tool_definitions import get_tools_for_agent, get_agent_tool_names

class ToolUtility:
    """Shared utility for tool calling that agents can use"""
    
    def __init__(self, agent_name: str):
        self.logger = logging.getLogger(__name__)
        self.agent_name = agent_name
        self.mongodb_tools = MongoDBTools()
        self.ui_preview_tools = UIPreviewTools()
        
        # Get tools for this specific agent
        self.tools = get_tools_for_agent(agent_name)
        self.tool_names = get_agent_tool_names(agent_name)
        
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tool schemas for this agent"""
        return self.tools
    
    def get_tool_names(self) -> List[str]:
        """Get the list of tool names for this agent"""
        return self.tool_names
    
    def call_function(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function by name with arguments"""
        try:
            if name == "get_templates_by_category":
                category = args.get("category")
                limit = args.get("limit", 10)
                return self.mongodb_tools.get_templates_by_category(category, limit)
            
            elif name == "get_template_metadata":
                template_id = args.get("template_id")
                return self.mongodb_tools.get_template_metadata(template_id)
            
            elif name == "search_templates_by_tags":
                tags = args.get("tags", [])
                category = args.get("category")
                limit = args.get("limit", 10)
                return self.mongodb_tools.search_templates_by_tags(tags, category, limit)
            
            elif name == "get_available_categories":
                return self.mongodb_tools.get_available_categories()
            
            # UI Preview Tools
            elif name == "generate_ui_preview":
                template_id = args.get("template_id")
                return self.ui_preview_tools.generate_ui_preview(template_id)
            
            elif name == "get_template_code":
                template_id = args.get("template_id")
                return self.ui_preview_tools.get_template_code(template_id)
            
            elif name == "validate_template_code":
                template_id = args.get("template_id")
                return self.ui_preview_tools.validate_template_code(template_id)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {name}",
                    "agent_response": f"I don't know how to execute the function '{name}'. Please check the available tools."
                }
                
        except Exception as e:
            self.logger.error(f"Error executing function {name}: {e}")
            return {
                "success": False,
                "error": f"Function execution failed: {str(e)}",
                "agent_response": "I encountered an error while executing the requested function. Please try again."
            }
    
    def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of tool calls and return results"""
        results = []
        
        for tool_call in tool_calls:
            try:
                # Handle both function_call and custom tool formats
                if tool_call.get("type") == "function_call":
                    name = tool_call.get("name")
                    args = json.loads(tool_call.get("arguments", "{}"))
                elif tool_call.get("type") == "custom":
                    name = tool_call.get("name")
                    args = json.loads(tool_call.get("input", "{}"))
                else:
                    # Try to extract name and args from any format
                    name = tool_call.get("name")
                    args = json.loads(tool_call.get("input", tool_call.get("arguments", "{}")))
                
                if name:
                    # Execute the function
                    result = self.call_function(name, args)
                    
                    # Add tool call metadata
                    result["tool_call_id"] = tool_call.get("id", tool_call.get("call_id"))
                    result["tool_name"] = name
                    
                    results.append(result)
                else:
                    results.append({
                        "success": False,
                        "error": "No tool name found in tool call",
                        "agent_response": "I couldn't identify which tool to call."
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing tool call: {e}")
                results.append({
                    "success": False,
                    "error": f"Tool call processing failed: {str(e)}",
                    "agent_response": "I encountered an error while processing the tool call. Please try again."
                })
        
        return results
    
    def format_tool_results_for_agent(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results into a readable string for the agent"""
        if not tool_results:
            return "No tool results to process."
        
        formatted_results = []
        
        for result in tool_results:
            tool_name = result.get("tool_name", "unknown")
            success = result.get("success", False)
            
            if success:
                if tool_name == "get_templates_by_category":
                    category = result.get("category", "unknown")
                    count = result.get("count", 0)
                    templates = result.get("templates", [])
                    
                    formatted_results.append(f"Found {count} templates for category '{category}':")
                    for template in templates[:3]:  # Show first 3 templates
                        formatted_results.append(f"- {template.get('name', 'Unknown')} (ID: {template.get('template_id', 'N/A')})")
                        formatted_results.append(f"  Tags: {', '.join(template.get('tags', []))}")
                        formatted_results.append(f"  Description: {template.get('description', 'No description')}")
                    if count > 3:
                        formatted_results.append(f"... and {count - 3} more templates")
                
                elif tool_name == "get_template_metadata":
                    template = result.get("template", {})
                    formatted_results.append(f"Template: {template.get('name', 'Unknown')}")
                    formatted_results.append(f"Category: {template.get('category', 'unknown')}")
                    formatted_results.append(f"Tags: {', '.join(template.get('tags', []))}")
                    formatted_results.append(f"Description: {template.get('description', 'No description')}")
                
                elif tool_name == "search_templates_by_tags":
                    tags = result.get("tags", [])
                    count = result.get("count", 0)
                    templates = result.get("templates", [])
                    
                    formatted_results.append(f"Found {count} templates with tags {tags}:")
                    for template in templates[:3]:
                        formatted_results.append(f"- {template.get('name', 'Unknown')} (ID: {template.get('template_id', 'N/A')})")
                
                elif tool_name == "get_available_categories":
                    categories = result.get("categories", [])
                    count = result.get("count", 0)
                    formatted_results.append(f"Available categories ({count}): {', '.join(categories)}")
            
            else:
                error = result.get("error", "Unknown error")
                agent_response = result.get("agent_response", "An error occurred")
                formatted_results.append(f"Tool '{tool_name}' failed: {error}")
                formatted_results.append(f"Agent response: {agent_response}")
        
        return "\n".join(formatted_results)
    
    def get_tool_summary(self) -> str:
        """Get a summary of available tools for this agent"""
        if not self.tool_names:
            return "No tools available for this agent."
        
        summary = f"Available tools for {self.agent_name}:\n"
        for tool_name in self.tool_names:
            summary += f"- {tool_name}\n"
        
        return summary 