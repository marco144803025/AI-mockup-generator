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

# Import the lean flow orchestrator with focused agents
from agents.lean_flow_orchestrator import LeanFlowOrchestrator

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

# Initialize the lean flow orchestrator
orchestrator = LeanFlowOrchestrator()

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
    return {"message": "Enhanced AI UI Workflow API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    """Main chat endpoint using the lean flow orchestrator with focused agents"""
    try:
        # Process the message through the flow orchestrator
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
                validation_results=result.get("validation_results", [])
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
        return orchestrator.reset_session()
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/categories")
def get_template_categories():
    """Get available template categories"""
    try:
        # First, try to get categories from database with a timeout
        import asyncio
        import concurrent.futures
        
        def fetch_categories_from_db():
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
                    'Login': 'login',
                    'Profile': 'profile',
                    'Landing': 'landing',
                    'Portfolio': 'portfolio'
                }
                
                for category in all_categories:
                    normalized = category_mapping.get(category, category.lower())
                    if normalized not in normalized_categories:
                        normalized_categories.append(normalized)
                
                return normalized_categories
            except Exception as e:
                logger.error(f"Database error fetching categories: {e}")
                return []
        
        # Try to fetch from database with 3-second timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(fetch_categories_from_db)
            try:
                normalized_categories = future.result(timeout=3.0)
            except concurrent.futures.TimeoutError:
                logger.warning("Database query timed out, using default categories")
                normalized_categories = []
        
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
    """Get category-specific constraints for prompt engineering using MongoDB tools"""
    try:
        # Use the MongoDB tools to get templates by category
        from tools.mongodb_tools import MongoDBTools
        mongodb_tools = MongoDBTools()
        
        result = mongodb_tools.get_templates_by_category(category, limit=50)  # Get more templates for better analysis
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Error fetching templates for category: {category}")
        
        templates = result.get("templates", [])
        
        if not templates:
            raise HTTPException(status_code=404, detail=f"No templates found for category: {category}")
        
        # Extract unique tags from all templates in this category
        all_tags = []
        for template in templates:
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
            "templates_count": len(templates),
            "category_tags": unique_tags,
            "styles": styles,
            "themes": themes,
            "features": features,
            "layouts": layouts,
            "templates": [
                {
                    "name": template.get('name', 'Unknown'),
                    "tags": template.get('tags', [])
                } for template in templates
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category constraints: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching category constraints: {str(e)}")

@app.get("/api/templates")
def get_templates(category: Optional[str] = None, limit: int = 10):
    """Get templates with optional category filter using MongoDB tools"""
    try:
        # Use the MongoDB tools to get templates
        from tools.mongodb_tools import MongoDBTools
        mongodb_tools = MongoDBTools()
        
        if category:
            # Get templates by category
            result = mongodb_tools.get_templates_by_category(category, limit)
        else:
            # Get all templates by fetching from all available categories
            categories_result = mongodb_tools.get_available_categories()
            if categories_result.get("success"):
                all_templates = []
                for cat in categories_result.get("categories", []):
                    cat_result = mongodb_tools.get_templates_by_category(cat, limit // len(categories_result.get("categories", [1])))
                    if cat_result.get("success"):
                        all_templates.extend(cat_result.get("templates", []))
                result = {"success": True, "templates": all_templates}
            else:
                # Fallback to a default category if categories can't be fetched
                result = mongodb_tools.get_templates_by_category("landing", limit)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Error fetching templates: {result.get('error', 'Unknown error')}")
        
        templates = result.get("templates", [])
        
        # Convert the template format to match the expected API response
        formatted_templates = []
        for template in templates:
            formatted_template = {
                "_id": template.get("template_id", ""),
                "name": template.get("name", "Unknown"),
                "category": template.get("category", category or "unknown"),
                "tags": template.get("tags", []),
                "metadata": {
                    "category": template.get("category", category or "unknown"),
                    "description": template.get("description", ""),
                    "figma_url": template.get("figma_url", "")
                }
            }
            formatted_templates.append(formatted_template)
        
        return {
            "templates": formatted_templates,
            "count": len(formatted_templates),
            "category": category
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@app.get("/api/debug/session/{session_id}")
def get_session_debug_info(session_id: str):
    """Get detailed session debug information"""
    try:
        logger.info(f"Debug: Requesting session info for session_id: {session_id}")
        logger.info(f"Debug: Current orchestrator session_id: {orchestrator.session_id}")
        
        # Check if this is the current session
        if session_id == orchestrator.session_id:
            session_status = orchestrator.get_session_status()
            conversation_history = orchestrator.session_state.get("conversation_history", [])
            current_plan = orchestrator.session_state.get("current_plan", [])
            
            debug_response = {
                "session_id": session_id,
                "session_status": session_status,
                "session_state": orchestrator.session_state,
                "conversation_history": conversation_history,
                "current_plan": current_plan,
                "debug_info": {
                    "total_messages": len(conversation_history),
                    "current_phase": orchestrator.session_state.get("current_phase", "unknown"),
                    "plan_steps": len(current_plan),
                    "current_plan_step": orchestrator.session_state.get("plan_step", 0),
                    "project_state": orchestrator.session_state.get("project_state", {})
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Debug: Returning session info with {len(conversation_history)} messages and {len(current_plan)} plan steps")
            return debug_response
        else:
            logger.warning(f"Debug: Session ID mismatch. Requested: {session_id}, Current: {orchestrator.session_id}")
            return {
                "session_id": session_id,
                "error": "Session not found or not current session",
                "current_session_id": orchestrator.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting session debug info: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "session_id": session_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/debug/test")
def test_debug_endpoint():
    """Simple test endpoint to check if debug endpoints are working"""
    logger.info("Debug: Test endpoint called")
    return {
        "status": "debug_endpoints_working",
        "message": "Debug endpoints are accessible",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_session_id": orchestrator.session_id,
        "orchestrator_initialized": orchestrator is not None,
        "session_state_keys": list(orchestrator.session_state.keys()) if orchestrator else []
    }

@app.get("/api/debug/logs")
def get_recent_logs(limit: int = 50):
    """Get recent application logs"""
    try:
        logger.info(f"Debug: Logs endpoint called with limit: {limit}")
        return {
            "message": "Logs are written to console and agent_debug.log file",
            "log_file": "agent_debug.log",
            "console_logging": "Enabled with DEBUG level",
            "note": "Run the backend with --log-level debug for more detailed logs",
            "current_log_level": "DEBUG",
            "orchestrator_status": "Initialized" if orchestrator else "Not initialized"
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug/test-agent")
async def test_agent_pipeline(request: ChatMessage):
    """Test the agent pipeline with detailed output"""
    try:
        logger.info(f"Debug: Testing agent pipeline with message: {request.message[:100]}...")
        
        # Test the orchestrator with a simple message
        result = await orchestrator.process_user_message(
            request.message, 
            request.context
        )
        
        logger.info(f"Debug: Agent pipeline test completed successfully")
        
        return {
            "success": True,
            "test_result": result,
            "orchestrator_session_id": orchestrator.session_id,
            "debug_info": {
                "message_processed": request.message,
                "session_state": orchestrator.session_state,
                "conversation_history_length": len(orchestrator.session_state.get("conversation_history", [])),
                "current_phase": orchestrator.session_state.get("current_phase", "unknown")
            }
        }
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "error_traceback": str(e),
                "orchestrator_session_id": orchestrator.session_id
            }
        }

@app.get("/api/debug/reasoning/{session_id}")
async def get_reasoning_chain(session_id: str):
    """Get the complete reasoning chain for a session"""
    try:
        logger.info(f"Debug: Requesting reasoning chain for session_id: {session_id}")
        
        # Check if this is the current session
        if session_id == orchestrator.session_id:
            conversation_history = orchestrator.session_state.get("conversation_history", [])
            current_plan = orchestrator.session_state.get("current_plan", [])
            
            logger.info(f"Debug: Returning reasoning chain with {len(conversation_history)} steps")
            
            return {
                "session_id": session_id,
                "reasoning_chain": conversation_history,
                "agent_thinking": {
                    "current_plan": current_plan,
                    "plan_step": orchestrator.session_state.get("plan_step", 0),
                    "total_plan_steps": len(current_plan)
                },
                "total_reasoning_steps": len(conversation_history),
                "agents_involved": ["lean_flow_orchestrator", "requirements_analysis", "template_recommendation", "question_generation", "user_proxy"],
                "current_phase": orchestrator.session_state.get("current_phase", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning(f"Debug: Session ID mismatch for reasoning chain. Requested: {session_id}, Current: {orchestrator.session_id}")
            return {
                "session_id": session_id,
                "error": "Session not found or not current session",
                "current_session_id": orchestrator.session_id,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting reasoning chain: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "session_id": session_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/debug/cot-summary/{session_id}")
async def get_cot_summary(session_id: str):
    """Get a summary of chain-of-thought reasoning for a session"""
    try:
        # Check if this is the current session
        if session_id == orchestrator.session_id:
            conversation_history = orchestrator.session_state.get("conversation_history", [])
            current_plan = orchestrator.session_state.get("current_plan", [])
            
            # Analyze conversation history
            user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
            assistant_messages = [msg for msg in conversation_history if msg.get("role") == "assistant"]
            
            # Count step types
            step_types = {}
            for step in current_plan:
                step_type = step.get("action", "unknown")
                step_types[step_type] = step_types.get(step_type, 0) + 1
            
            return {
                "session_id": session_id,
                "summary": {
                    "total_steps": len(conversation_history),
                    "user_messages": len(user_messages),
                    "assistant_messages": len(assistant_messages),
                    "agents_used": ["lean_flow_orchestrator", "requirements_analysis", "template_recommendation", "question_generation", "user_proxy"],
                    "layer_activity": {
                        "conversation_history_length": len(conversation_history),
                        "current_plan_length": len(current_plan),
                        "current_phase": orchestrator.session_state.get("current_phase", "unknown")
                    },
                    "step_types": step_types,
                    "first_step": conversation_history[0] if conversation_history else None,
                    "last_step": conversation_history[-1] if conversation_history else None
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "session_id": session_id,
                "error": "Session not found or not current session",
                "current_session_id": orchestrator.session_id,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting COT summary: {e}")
        return {
            "session_id": session_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/chat-with-cot")
async def chat_with_cot(chat_message: ChatMessage):
    """Enhanced chat endpoint that returns reasoning chain along with response"""
    try:
        # Process the message through the orchestrator
        result = await orchestrator.process_user_message(
            chat_message.message, 
            chat_message.context
        )
        
        # Get reasoning chain
        conversation_history = orchestrator.session_state.get("conversation_history", [])
        current_plan = orchestrator.session_state.get("current_plan", [])
        
        return {
            "response": result.get("response", "No response generated"),
            "session_id": result.get("session_id", orchestrator.session_id),
            "success": result.get("success", False),
            "metadata": result.get("metadata", {}),
            "validation_results": result.get("validation_results", []),
            "reasoning_chain": conversation_history,
            "current_plan": current_plan,
            "cot_enhanced": True,
            "debug_info": {
                "current_phase": orchestrator.session_state.get("current_phase", "unknown"),
                "total_conversation_steps": len(conversation_history),
                "plan_steps": len(current_plan)
            }
        }
    except Exception as e:
        logger.error(f"Error in chat-with-cot: {e}")
        return {
            "response": f"Error: {str(e)}",
            "session_id": orchestrator.session_id,
            "success": False,
            "metadata": {"error": str(e)},
            "validation_results": [],
            "reasoning_chain": [],
            "cot_enhanced": False
        }

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_db()
        db.command("ping")
        
        return {
            "status": "healthy",
            "database": "connected",
            "orchestrator": "ready",
            "session_id": orchestrator.session_id,
            "timestamp": datetime.now().isoformat()
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