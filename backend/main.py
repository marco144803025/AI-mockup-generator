from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import json
import anthropic
from db import get_db
from datetime import datetime

# Import the new layered orchestrator
from layered_orchestrator import LayeredOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the layered orchestrator
orchestrator = LayeredOrchestrator()

# Claude API configuration
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not CLAUDE_API_KEY:
    print("Warning: ANTHROPIC_API_KEY not found. LLM features will be limited.")
    CLAUDE_API_KEY = "placeholder_key"

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    metadata: Optional[Dict[str, Any]] = None
    validation_results: Optional[List[Dict[str, Any]]] = None

class ClaudeRequest(BaseModel):
    prompt: Optional[str] = None
    image: Optional[str] = None
    model: str = "claude-3-5-haiku-20241022"
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class ClaudeResponse(BaseModel):
    response: str
    usage: Dict[str, Any]
    model: str

@app.get("/")
def read_root():
    return {"message": "Layered AI UI Workflow API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    """Main chat endpoint using the layered orchestrator"""
    try:
        # Process the message through the layered orchestrator
        result = await orchestrator.process_user_message(
            chat_message.message, 
            chat_message.context
        )
        
        if result["success"]:
            return ChatResponse(
                response=result["response"],
                session_id=result["session_id"],
                success=True,
                metadata=result.get("metadata"),
                validation_results=result.get("validation_results")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claude", response_model=ClaudeResponse)
async def call_claude(request: ClaudeRequest):
    """Legacy Claude API endpoint for direct LLM calls"""
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        
        # Handle image input
        if request.image:
            media_type = "image/png"
            base64_data = request.image
            if request.image.startswith("data:image/"):
                media_type = request.image.split(";")[0].split(":")[1]
                base64_data = request.image.split(",")[1]
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
                            }
                        },
                        {
                            "type": "text",
                            "text": request.prompt or "Describe this image."
                        }
                    ]
                }
            ]
        else:
            # Prepare text messages
            if request.system_prompt:
                user_content = f"[System: {request.system_prompt}]\n\n{request.prompt}"
            else:
                user_content = request.prompt
            
            messages = [{"role": "user", "content": user_content}]
        
        # Call Claude API
        message = client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=messages
        )
        
        # Extract response content
        if isinstance(message.content, list):
            response_text = " ".join([block.text for block in message.content if hasattr(block, 'text')])
        else:
            response_text = str(message.content)
        
        # Extract usage information
        usage = getattr(message, 'usage', {})
        if not isinstance(usage, dict):
            usage = dict(usage)
        
        return ClaudeResponse(
            response=response_text,
            usage=usage,
            model=request.model
        )
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")

@app.get("/api/session/status")
def get_session_status():
    """Get current session status"""
    try:
        return orchestrator.get_session_status()
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/reset")
def reset_session():
    """Reset the current session"""
    try:
        result = orchestrator.reset_session()
        return result
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/categories")
def get_template_categories():
    """Get available template categories"""
    try:
        db = get_db()
        # Get categories from direct category field
        direct_categories = db.templates.distinct("category")
        
        # Get categories from metadata.category field
        metadata_categories = db.templates.distinct("metadata.category")
        
        # Combine and deduplicate categories
        all_categories = list(set(direct_categories + metadata_categories))
        
        # Remove None/empty values
        all_categories = [cat for cat in all_categories if cat]
        
        # Normalize categories to lowercase for consistency
        normalized_categories = []
        category_mapping = {
            'About': 'about',
            'sign-up': 'signup',
            'Sign-up': 'signup',
            'Signup': 'signup',
            'Login': 'login',
            'Profile': 'profile',
            'Landing': 'landing',
            'Portfolio': 'portfolio'
        }
        
        for category in all_categories:
            normalized = category_mapping.get(category, category.lower())
            if normalized not in normalized_categories:
                normalized_categories.append(normalized)
        
        # If no categories found in database, provide default categories
        if not normalized_categories:
            logger.info("No categories found in database, providing defaults")
            normalized_categories = ['landing', 'login', 'signup', 'profile', 'about', 'portfolio']
        
        return {
            "categories": normalized_categories,
            "count": len(normalized_categories)
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        # Return default categories on error
        return {
            "categories": ['landing', 'login', 'signup', 'profile', 'about', 'portfolio'],
            "count": 6
        }

@app.get("/api/templates/category-constraints/{category}")
def get_category_constraints(category: str):
    """Get category-specific constraints for prompt engineering"""
    try:
        db = get_db()
        
        # Normalize the input category
        category_mapping = {
            'About': 'about',
            'sign-up': 'signup',
            'Sign-up': 'signup',
            'Signup': 'signup',
            'Login': 'login',
            'Profile': 'profile',
            'Landing': 'landing',
            'Portfolio': 'portfolio'
        }
        
        # Find templates in this category (check both direct and metadata fields)
        # Also check for variations of the category name
        possible_categories = [category]
        for original, normalized in category_mapping.items():
            if normalized == category:
                possible_categories.append(original)
            elif original == category:
                possible_categories.append(normalized)
        
        category_templates = list(db.templates.find({
            "$or": [
                {"category": {"$in": possible_categories}},
                {"metadata.category": {"$in": possible_categories}}
            ]
        }))
        
        if not category_templates:
            raise HTTPException(status_code=404, detail=f"No templates found for category: {category}")
        
        # Extract unique tags from all templates in this category
        all_tags = []
        for template in category_templates:
            tags = template.get('tags', [])
            if isinstance(tags, list):
                all_tags.extend(tags)
        
        unique_tags = list(set(all_tags))
        
        # Categorize tags
        styles = []
        themes = []
        features = []
        layouts = []
        
        for tag in unique_tags:
            tag_lower = tag.lower()
            if any(style in tag_lower for style in ['modern', 'minimal', 'clean', 'professional', 'colorful']):
                styles.append(tag)
            elif any(theme in tag_lower for theme in ['dark', 'light', 'theme']):
                themes.append(tag)
            elif any(feature in tag_lower for feature in ['responsive', 'interactive', 'user-friendly', 'form', 'gallery']):
                features.append(tag)
            elif any(layout in tag_lower for layout in ['card', 'grid', 'flexbox', 'hero']):
                layouts.append(tag)
            else:
                # Default to features if not categorized
                features.append(tag)
        
        return {
            "category": category,
            "templates_count": len(category_templates),
            "category_tags": unique_tags,
            "styles": styles,
            "themes": themes,
            "features": features,
            "layouts": layouts,
            "templates": [
                {
                    "name": template.get('name', 'Unknown'),
                    "tags": template.get('tags', [])
                } for template in category_templates
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category constraints: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching category constraints: {str(e)}")

@app.get("/api/templates")
def get_templates(category: Optional[str] = None, limit: int = 10):
    """Get templates with optional category filter"""
    try:
        db = get_db()
        
        # Build query
        query = {}
        if category:
            # Normalize the input category and check for variations
            category_mapping = {
                'About': 'about',
                'sign-up': 'signup',
                'Sign-up': 'signup',
                'Signup': 'signup',
                'Login': 'login',
                'Profile': 'profile',
                'Landing': 'landing',
                'Portfolio': 'portfolio'
            }
            
            possible_categories = [category]
            for original, normalized in category_mapping.items():
                if normalized == category:
                    possible_categories.append(original)
                elif original == category:
                    possible_categories.append(normalized)
            
            query["$or"] = [
                {"category": {"$in": possible_categories}},
                {"metadata.category": {"$in": possible_categories}}
            ]
        
        # Execute query
        templates = list(db.templates.find(query).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for template in templates:
            if '_id' in template:
                template['_id'] = str(template['_id'])
        
        return {
            "templates": templates,
            "count": len(templates),
            "category": category
        }
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@app.get("/api/debug/session/{session_id}")
def get_session_debug_info(session_id: str):
    """Get detailed debug information for a session"""
    try:
        logger.info(f"Debug endpoint called for session: {session_id}")
        
        # Get session state from memory
        session_state = orchestrator.memory.retrieve_project_state(session_id)
        logger.info(f"Retrieved session state: {session_state is not None}")
        
        conversation_context = orchestrator.memory.retrieve_conversation_context(session_id)
        logger.info(f"Retrieved conversation context: {conversation_context is not None}")
        
        # Get conversation history from control layer
        conversation_history = orchestrator.control.conversation_history
        logger.info(f"Conversation history length: {len(conversation_history)}")
        
        # Get validation summary
        validation_summary = orchestrator.validation.get_validation_summary()
        logger.info(f"Validation summary retrieved")
        
        # Get tool statistics
        tool_stats = orchestrator.tools.get_tool_statistics()
        logger.info(f"Tool statistics retrieved")
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        response_data = {
            "session_id": session_id,
            "session_state": convert_datetime(session_state),
            "conversation_context": convert_datetime(conversation_context),
            "conversation_history": convert_datetime(conversation_history),
            "validation_summary": convert_datetime(validation_summary),
            "tool_statistics": convert_datetime(tool_stats),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Debug response prepared successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting debug info: {e}")
        return {
            "error": str(e),
            "session_id": session_id,
            "message": "Failed to retrieve debug information"
        }

@app.get("/api/debug/test")
def test_debug_endpoint():
    """Simple test endpoint to check if debug endpoints are working"""
    return {
        "status": "debug_endpoints_working",
        "message": "Debug endpoints are accessible",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_session_id": orchestrator.session_id
    }

@app.get("/api/debug/logs")
def get_recent_logs(limit: int = 50):
    """Get recent application logs"""
    try:
        # This would require setting up a log handler that stores logs in memory
        # For now, return a message about where to find logs
        return {
            "message": "Logs are written to console and agent_debug.log file",
            "log_file": "agent_debug.log",
            "console_logging": "Enabled with DEBUG level",
            "note": "Run the backend with --log-level debug for more detailed logs"
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug/test-agent")
async def test_agent_pipeline(request: ChatMessage):
    """Test the agent pipeline with detailed output"""
    try:
        # Process the message and capture detailed information
        result = await orchestrator.process_user_message(request.message, request.context)
        
        # Get additional debug information
        session_state = orchestrator.memory.retrieve_project_state(result["session_id"])
        conversation_history = orchestrator.control.conversation_history[-5:]  # Last 5 entries
        
        return {
            "success": True,
            "result": result,
            "debug_info": {
                "session_state": session_state,
                "recent_conversation_history": conversation_history,
                "validation_summary": orchestrator.validation.get_validation_summary(),
                "tool_statistics": orchestrator.tools.get_tool_statistics()
            }
        }
    except Exception as e:
        logger.error(f"Error in test agent pipeline: {e}")
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "error_traceback": str(e)
            }
        }

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_db()
        db.command("ping")
        
        # Test orchestrator
        status = orchestrator.get_session_status()
        
        return {
            "status": "healthy",
            "database": "connected",
            "orchestrator": "ready",
            "session_id": status.get("session_id"),
            "timestamp": status.get("session_state", {}).get("created_at")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 