"""
Tool Definitions - Tool schemas and agent-specific assignments
"""

# Tool schemas following Anthropic's API format
MONGODB_TOOL_SCHEMAS = {
    "get_templates_by_category": {
        "type": "custom",
        "name": "get_templates_by_category",
        "description": "Get UI templates filtered by category with metadata and tags. Use this to find templates for a specific page type like landing, login, signup, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category of templates to fetch (e.g., 'landing', 'login', 'signup', 'profile')"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of templates to return (default: 10)"
                }
            },
            "required": ["category"],
            "additionalProperties": False
        }
    },
    
    "get_template_metadata": {
        "type": "custom",
        "name": "get_template_metadata",
        "description": "Get detailed metadata and tags for a specific template by its ID. Use this to analyze a specific template's design elements and features.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "The unique ID of the template to fetch metadata for"
                }
            },
            "required": ["template_id"],
            "additionalProperties": False
        }
    },
    
    "search_templates_by_tags": {
        "type": "custom",
        "name": "search_templates_by_tags",
        "description": "Search templates by design tags with optional category filter. Use this to find templates with specific design elements like 'modern', 'clean', 'responsive', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of design tags to search for (e.g., ['modern', 'clean', 'responsive'])"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g., 'landing', 'login')"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of templates to return (default: 10)"
                }
            },
            "required": ["tags"],
            "additionalProperties": False
        }
    },
    
    "get_available_categories": {
        "type": "custom",
        "name": "get_available_categories",
        "description": "Get all available template categories in the database. Use this to understand what page types are available.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
}

# UI Preview Tool Schemas
UI_PREVIEW_TOOL_SCHEMAS = {
    "generate_ui_preview": {
        "type": "custom",
        "name": "generate_ui_preview",
        "description": "Generate a complete UI preview from template code. This combines HTML, CSS files and creates a renderable preview with code analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "The unique ID of the template to generate preview for"
                }
            },
            "required": ["template_id"],
            "additionalProperties": False
        }
    },
    
    "get_template_code": {
        "type": "custom",
        "name": "get_template_code",
        "description": "Get raw template code files (HTML, CSS) from the database. Use this to access the actual code for analysis or modification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "The unique ID of the template to get code for"
                }
            },
            "required": ["template_id"],
            "additionalProperties": False
        }
    },
    
    "validate_template_code": {
        "type": "custom",
        "name": "validate_template_code",
        "description": "Validate that a template has all required code files (HTML, CSS) and is complete for preview generation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "The unique ID of the template to validate"
                }
            },
            "required": ["template_id"],
            "additionalProperties": False
        }
    }
}

# Agent-specific tool assignments
AGENT_TOOLS = {
    "ui_recommender_agent": [
        "get_templates_by_category",
        "search_templates_by_tags",
        "get_available_categories",
        "get_template_metadata",
        "generate_ui_preview",
        "validate_template_code"
    ],
    "requirements_analysis_agent": [
        "get_templates_by_category",
        "get_available_categories",
        "get_template_metadata"
    ],
    "template_recommendation_agent": [
        "get_templates_by_category",
        "search_templates_by_tags",
        "get_available_categories",
        "get_template_metadata"
    ],
    "question_generation_agent": [
        "get_templates_by_category",
        "get_available_categories"
    ],
    "ui_editing_agent": [
        # UI editing agent doesn't need database tools - it works with provided UI code
    ],
    "user_proxy_agent": [
        "get_available_categories",
        "get_templates_by_category"
    ],
    "report_generation_agent": [
        "get_template_metadata",
        "get_templates_by_category",
        "generate_ui_preview"
    ]
}

def get_tools_for_agent(agent_name: str) -> list:
    """Get the list of tool schemas for a specific agent"""
    if agent_name not in AGENT_TOOLS:
        return []
    
    tools = []
    for tool_name in AGENT_TOOLS[agent_name]:
        if tool_name in MONGODB_TOOL_SCHEMAS:
            tools.append(MONGODB_TOOL_SCHEMAS[tool_name])
        elif tool_name in UI_PREVIEW_TOOL_SCHEMAS:
            tools.append(UI_PREVIEW_TOOL_SCHEMAS[tool_name])
    
    return tools

def get_all_available_tools() -> dict:
    """Get all available tool schemas"""
    return MONGODB_TOOL_SCHEMAS.copy()

def get_agent_tool_names(agent_name: str) -> list:
    """Get the list of tool names (not schemas) for a specific agent"""
    return AGENT_TOOLS.get(agent_name, []) 