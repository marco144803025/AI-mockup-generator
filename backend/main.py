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
    success: bool
    response: str
    session_id: Optional[str] = None
    phase: Optional[str] = None
    intent: Optional[str] = None
    selected_template: Optional[Dict[str, Any]] = None
    session_state: Optional[Dict[str, Any]] = None
    transition_ready: Optional[bool] = False
    transition_data: Optional[Dict[str, Any]] = None

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

class UIEditorChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_ui_codes: Optional[Dict[str, Any]] = None

class UIEditorChatResponse(BaseModel):
    success: bool
    response: str
    ui_modifications: Optional[Dict[str, Any]] = None
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

# Pydantic models for template-to-JSON transition
class TemplateToJsonRequest(BaseModel):
    template_id: str
    session_id: str
    category: Optional[str] = None

class TemplateToJsonResponse(BaseModel):
    success: bool
    message: str
    template_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Enhanced AI UI Workflow API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Main chat endpoint that coordinates the multi-agent workflow"""
    try:
        # Extract session ID from request
        session_id = request.session_id or "demo_session"
        
        # Create orchestrator with session ID
        from agents.lean_flow_orchestrator import LeanFlowOrchestrator
        orchestrator = LeanFlowOrchestrator(session_id=session_id)
        
        # Process the message through the orchestrator
        result = await orchestrator.process_user_message(
            message=request.message,
            context=request.context
        )
        
        return ChatResponse(
            success=result.get("success", True),
            response=result.get("response", "I understand your request. Let me process that for you."),
            session_id=result.get("session_id", session_id),
            phase=result.get("phase", "unknown"),
            intent=result.get("intent", "unknown"),
            selected_template=result.get("selected_template"),
            session_state=result.get("session_state"),
            transition_ready=result.get("transition_ready", False),
            transition_data=result.get("transition_data")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            success=False,
            response=f"I encountered an error: {str(e)}",
            session_id=request.session_id or "demo_session"
        )

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
async def get_session_status():
    """Get current session status and state"""
    try:
        from session_manager import session_manager
        
        # For demo purposes, use a default session ID
        # In production, you'd get the session ID from the request
        session_id = "demo_session"
        
        # Get session from global manager
        session_data = session_manager.get_session(session_id)
        
        if session_data:
            return {
                "success": True,
                "session_id": session_id,
                "session_state": session_data,
                "message": "Session status retrieved successfully"
            }
        else:
            # Return default session state if not found
            return {
                "success": True,
                "session_id": session_id,
                "session_state": {
                    "phase": "initial",
                    "selected_template": None,
                    "category": None,
                    "requirements": {}
                },
                "message": "Session not found, returning default state"
            }
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

# Remove debug endpoints - not needed for production
# @app.get("/api/debug/test")
# @app.get("/api/debug/logs") 
# @app.post("/api/debug/test-agent")
# @app.get("/api/debug/reasoning/{session_id}")
# @app.get("/api/debug/cot-summary/{session_id}")
# @app.post("/api/chat-with-cot")



@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/ui-codes/{template_id}")
async def get_ui_codes(template_id: str):
    """Get UI codes (HTML, CSS, JS) for a specific template"""
    try:
        from bson import ObjectId
        from tools.ui_preview_tools import UIPreviewTools
        
        # Handle special case for "default" template
        if template_id == "default":
            return await get_default_ui_codes()
        
        # Validate template_id format for MongoDB ObjectId
        try:
            ObjectId(template_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid template ID format")
        
        # Use the existing UI preview tools to get template data
        ui_tools = UIPreviewTools()
        result = ui_tools.get_template_code(template_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Template not found"))
        
        # Return structured UI codes matching MongoDB structure
        return {
            "success": True,
            "template_id": template_id,
            "template_name": result["template_info"]["name"],
            "ui_codes": {
                "html_export": result["code_data"]["html_export"],
                "globals_css": result["code_data"]["global_css"],
                "style_css": result["code_data"]["style_css"],
                "js": result["code_data"].get("js_code", ""),
                "complete_html": result["code_data"]["complete_html"]
            },
            "metadata": {
                "category": result["template_info"]["category"],
                "description": result["template_info"]["description"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching UI codes for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ui-codes/default")
async def get_default_ui_codes():
    """Get default UI codes for the editor (using login template)"""
    try:
        # Use the login template as default
        login_html = """<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta charset="utf-8" />
    <style>
/* Global CSS Variables and Reset Styles */
:root {
  --glass1-fill-carey: rgba(255, 255, 255, 0.1);
  --muted: #666666;
  --action-sec: #007bff;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Noto Sans", Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #ffffff;
}

/* Reset form elements */
input, button, textarea, select {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

/* Ensure proper rendering */
html {
  -webkit-text-size-adjust: 100%;
  -ms-text-size-adjust: 100%;
}

.login {
  background-color: #0e0e0e;
  display: flex;
  flex-direction: row;
  justify-content: center;
  width: 100%;
}

.login .overlap-wrapper {
  background-color: #0e0e0e;
  overflow: hidden;
  width: 1440px;
  height: 1024px;
}

.login .overlap {
  position: relative;
  top: 81px;
  left: 60px;
  width: 1408px;
  height: 937px;
}

.login .overlap-group {
  position: absolute;
  top: 0;
  left: 0;
  width: 1408px;
  height: 937px;
}

.login .text-wrapper {
  position: absolute;
  top: 299px;
  left: 0;
  font-family: "Noto Sans", Helvetica;
  font-weight: 600;
  color: #ffffff;
  font-size: 96px;
  letter-spacing: 0;
  line-height: normal;
}

.login .frame {
  display: inline-flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 24px;
  position: absolute;
  top: 427px;
  left: 18px;
  border: 4px solid;
  border-color: #ffffff;
}

.login .div {
  position: relative;
  width: fit-content;
  font-family: "Noto Sans", Helvetica;
  font-weight: 400;
  color: #ffffff;
  font-size: 32px;
  letter-spacing: 0;
  line-height: normal;
}

.login .ellipse {
  position: absolute;
  width: 302px;
  height: 302px;
  top: 0;
  left: 689px;
  border-radius: 151px;
  background: linear-gradient(
    180deg,
    rgba(83, 0, 97, 1) 0%,
    rgba(13, 10, 48, 1) 100%
  );
}

.login .ellipse-2 {
  position: absolute;
  width: 220px;
  height: 220px;
  top: 678px;
  left: 1149px;
  border-radius: 110px;
  transform: rotate(-28.50deg);
  background: linear-gradient(
    180deg,
    rgba(48, 0, 97, 1) 0%,
    rgba(10, 16, 48, 1) 100%
  );
}

.login .frame-wrapper {
  position: absolute;
  width: 482px;
  height: 798px;
  top: 32px;
  left: 839px;
  border-radius: 20px;
  overflow: hidden;
  border: none;
  box-shadow: -8px 4px 5px #0000003d;
  backdrop-filter: blur(26.5px) brightness(100%);
  -webkit-backdrop-filter: blur(26.5px) brightness(100%);
  background: linear-gradient(
      294deg,
      rgba(191, 191, 191, 0.06) 0%,
      rgba(0, 0, 0, 0) 100%
    ), linear-gradient(0deg, rgba(0, 0, 0, 0.14) 0%, rgba(0, 0, 0, 0.14) 100%);
  background-color: var(--glass1-fill-carey);
}

.login .frame-wrapper::before {
  content: "";
  position: absolute;
  inset: 0;
  padding: 1px;
  border-radius: 20px;
  background: linear-gradient(
    318deg,
    rgba(255, 255, 255, 0.6) 0%,
    rgba(0, 0, 0, 0) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  z-index: 1;
  pointer-events: none;
}

.login .frame-2 {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 101px;
  position: relative;
  top: 97px;
  left: 40px;
}

.login .frame-3 {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 47px;
  position: relative;
  flex: 0 0 auto;
}

.login .upper-section {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  position: relative;
  flex: 0 0 auto;
}

.login .login-text {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  flex: 0 0 auto;
}

.login .text-wrapper-2 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 600;
  color: #ffffff;
  font-size: 36px;
  letter-spacing: 0;
  line-height: normal;
}

.login .text-wrapper-3 {
  position: relative;
  width: fit-content;
  font-family: "Noto Sans", Helvetica;
  font-weight: 500;
  color: #ffffff;
  font-size: 16px;
  letter-spacing: 0;
  line-height: normal;
}

.login .credentials {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 25px;
  position: relative;
  flex: 0 0 auto;
}

.login .username {
  display: flex;
  width: 400px;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  position: relative;
  flex: 0 0 auto;
  border-radius: 12px;
  border: 1px solid;
  border-color: #ffffff;
}

.login .text-wrapper-4 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 400;
  color: #ffffff;
  font-size: 20px;
  letter-spacing: 0;
  line-height: normal;
}

.login .password-rem {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  position: relative;
  flex: 0 0 auto;
}

.login .password {
  display: flex;
  width: 400px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  position: relative;
  flex: 0 0 auto;
  border-radius: 12px;
  border: 1px solid;
  border-color: #ffffff;
}

.login .vector-wrapper {
  position: relative;
  width: 18px;
  height: 18px;
}

.login .vector {
  width: 15px;
  height: 7px;
  top: 7px;
  position: absolute;
  left: 2px;
}

.login .remember {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  position: relative;
  flex: 0 0 auto;
}

.login .img {
  width: 14px;
  height: 14px;
  top: 2px;
  position: absolute;
  left: 2px;
}

.login .text-wrapper-5 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 500;
  color: #ffffff;
  font-size: 16px;
  letter-spacing: 0;
  line-height: normal;
}

.login .login-bt-fp {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  position: relative;
  flex: 0 0 auto;
}

.login .div-wrapper {
  display: flex;
  width: 400px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 10px;
  position: relative;
  flex: 0 0 auto;
  border-radius: 12px;
  background: linear-gradient(
    119deg,
    rgba(98, 142, 255, 1) 0%,
    rgba(135, 64, 205, 1) 53%,
    rgba(88, 4, 117, 1) 100%
  );
}

.login .text-wrapper-6 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 600;
  color: #ffffff;
  font-size: 20px;
  letter-spacing: 0;
  line-height: normal;
}

.login .other-logins {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  position: relative;
  flex: 0 0 auto;
}

.login .or {
  display: inline-flex;
  align-items: center;
  gap: 20px;
  position: relative;
  flex: 0 0 auto;
}

.login .line {
  position: relative;
  width: 170px;
  height: 2px;
}

.login .text-wrapper-7 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 500;
  color: #4c4c4c;
  font-size: 16px;
  letter-spacing: 0;
  line-height: normal;
}

.login .frame-4 {
  position: relative;
  flex: 0 0 auto;
}

.login .frame-5 {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
  flex: 0 0 auto;
}

.login .customer-care {
  display: flex;
  width: 400px;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px;
  position: relative;
  flex: 0 0 auto;
  border-radius: 6px;
  background: linear-gradient(
    180deg,
    rgba(98, 98, 98, 0) 0%,
    rgba(98, 98, 98, 0.07) 100%
  );
}

.login .frame-6 {
  display: inline-flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
}

.login .text-wrapper-8 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Noto Sans", Helvetica;
  font-weight: 400;
  color: #ffffff;
  font-size: 16px;
  letter-spacing: 0;
  line-height: normal;
}

.login .line-2 {
  position: absolute;
  width: 561px;
  height: 2px;
  top: 467px;
  left: 270px;
}
    </style>
  </head>
  <body>
    <div class="login">
      <div class="overlap-wrapper">
        <div class="overlap">
          <div class="overlap-group">
            <div class="text-wrapper">Welcome back!</div>
            <div class="frame">
              <div class="div">Enter your Credentials to access your account</div>
            </div>
            <div class="ellipse"></div>
            <div class="ellipse-2"></div>
          </div>
          <div class="frame-wrapper">
            <div class="frame-2">
              <div class="frame-3">
                <div class="upper-section">
                  <div class="login-text">
                    <div class="text-wrapper-2">Login</div>
                    <div class="text-wrapper-3">Enter your credentials to access your account</div>
                  </div>
                </div>
                <div class="credentials">
                  <div class="username">
                    <div class="text-wrapper-4">Username</div>
                  </div>
                  <div class="password-rem">
                    <div class="password">
                      <div class="text-wrapper-4">Password</div>
                      <div class="vector-wrapper">
                        <div class="vector"></div>
                      </div>
                    </div>
                    <div class="remember">
                      <div class="img"></div>
                      <div class="text-wrapper-5">Remember me</div>
                    </div>
                  </div>
                </div>
                <div class="login-bt-fp">
                  <div class="div-wrapper">
                    <div class="text-wrapper-6">Login</div>
                  </div>
                </div>
                <div class="other-logins">
                  <div class="or">
                    <div class="line"></div>
                    <div class="text-wrapper-7">or</div>
                    <div class="line"></div>
                  </div>
                  <div class="frame-4">
                    <div class="frame-5">
                      <div class="customer-care">
                        <div class="frame-6">
                          <div class="text-wrapper-8">Sign in with Google</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="line-2"></div>
      </div>
    </div>
  </body>
</html>"""
        
        login_css = """.log-in {
  background-color: #ffffff;
  display: flex;
  flex-direction: row;
  justify-content: center;
  width: 100%;
}

.log-in .div {
  background-color: #ffffff;
  width: 1536px;
  height: 1042px;
  position: relative;
}

.log-in .overlap {
  position: absolute;
  width: 404px;
  height: 583px;
  top: 230px;
  left: 175px;
}

.log-in .frame {
  display: inline-flex;
  height: 583px;
  align-items: flex-start;
  gap: 10px;
  position: absolute;
  top: 0;
  left: 0;
}

.log-in .group {
  position: relative;
  width: 408px;
  height: 583px;
  margin-right: -4.00px;
}

.log-in .div-wrapper {
  display: inline-flex;
  height: 53px;
  align-items: flex-start;
  gap: 10px;
  position: absolute;
  top: 0;
  left: 0;
}

.log-in .text-wrapper {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 32px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .p {
  position: absolute;
  width: 372px;
  top: 53px;
  left: 0;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 16px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .frame-2 {
  display: flex;
  flex-direction: column;
  width: 404px;
  height: 59px;
  align-items: flex-start;
  position: absolute;
  top: 139px;
  left: 0;
}

.log-in .name {
  display: inline-flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
  border: none;
  background: none;
  margin-top: -1.00px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 14px;
  letter-spacing: 0;
  line-height: normal;
  padding: 0;
}

.log-in .frame-wrapper {
  display: flex;
  width: 404px;
  height: 32px;
  align-items: center;
  gap: 10px;
  padding: 10px 0px 10px 10px;
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid;
  border-color: #d9d9d9;
}

.log-in .name-wrapper {
  display: inline-flex;
  align-items: flex-start;
  justify-content: center;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
  margin-top: -1.00px;
  margin-bottom: -1.50px;
  border: none;
  background: none;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0;
  line-height: normal;
  padding: 0;
}

.log-in .overlap-group {
  position: absolute;
  width: 404px;
  height: 59px;
  top: 218px;
  left: 0;
}

.log-in .frame-3 {
  height: 59px;
  display: flex;
  flex-direction: column;
  width: 404px;
  align-items: flex-start;
  position: absolute;
  top: 0;
  left: 0;
}

.log-in .frame-4 {
  display: inline-flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
}

.log-in .name-2 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 14px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .frame-5 {
  display: inline-flex;
  align-items: flex-start;
  justify-content: center;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
  margin-top: -1.50px;
  margin-bottom: -1.50px;
}

.log-in .text-wrapper-2 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .text-wrapper-3 {
  position: absolute;
  width: 83px;
  top: 0;
  left: 317px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: var(--action-sec);
  font-size: 10px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .group-2 {
  position: absolute;
  width: 121px;
  height: 15px;
  top: 296px;
  left: 0;
}

.log-in .text-wrapper-4 {
  position: absolute;
  width: 104px;
  top: 0;
  left: 15px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 9px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .rectangle {
  position: absolute;
  width: 9px;
  height: 10px;
  top: 2px;
  left: 0;
  border-radius: 2px;
  border: 1px solid;
  border-color: #000000;
}

.log-in .don-t-have-an-wrapper {
  position: absolute;
  width: 231px;
  height: 23px;
  top: 560px;
  left: 93px;
}

.log-in .don-t-have-an {
  position: absolute;
  width: 229px;
  top: 0;
  left: 0;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: transparent;
  font-size: 14px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .span {
  color: #000000;
}

.log-in .text-wrapper-5 {
  color: #0f3cde;
}

.log-in .overlap-group-wrapper {
  position: absolute;
  width: 404px;
  height: 35px;
  top: 332px;
  left: 0;
}

.log-in .overlap-group-2 {
  position: relative;
  height: 32px;
}

.log-in .frame-6 {
  display: flex;
  flex-direction: column;
  width: 404px;
  align-items: flex-start;
  position: absolute;
  top: 0;
  left: 0;
}

.log-in .frame-7 {
  display: flex;
  width: 404px;
  height: 32px;
  align-items: center;
  gap: 10px;
  padding: 10px 0px 10px 10px;
  position: relative;
  background-color: #3a5b22;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid;
}

.log-in .text-wrapper-6 {
  position: absolute;
  top: 5px;
  left: 185px;
  font-family: "Poppins", Helvetica;
  font-weight: 700;
  color: #ffffff;
  font-size: 13px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .frame-8 {
  display: inline-flex;
  align-items: center;
  gap: 23px;
  position: absolute;
  top: 505px;
  left: 0;
}

.log-in .frame-9 {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 4px 20px;
  position: relative;
  flex: 0 0 auto;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid;
  border-color: #d9d9d9;
}

.log-in .frame-10 {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
}

.log-in .div-2 {
  position: relative;
  width: 24px;
  height: 24px;
}

.log-in .overlap-group-3 {
  position: relative;
  width: 20px;
  height: 20px;
  top: 2px;
  left: 2px;
  background-image: url(https://c.animaapp.com/mdjj5tlqNNqw9w/img/vector.svg);
  background-size: 100% 100%;
}

.log-in .vector {
  position: absolute;
  width: 16px;
  height: 8px;
  top: 0;
  left: 1px;
}

.log-in .overlap-2 {
  position: absolute;
  width: 19px;
  height: 12px;
  top: 8px;
  left: 1px;
}

.log-in .img {
  position: absolute;
  width: 16px;
  height: 8px;
  top: 4px;
  left: 0;
}

.log-in .vector-2 {
  position: absolute;
  width: 10px;
  height: 9px;
  top: 0;
  left: 9px;
}

.log-in .text-wrapper-7 {
  position: relative;
  width: fit-content;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 12px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .frame-11 {
  display: flex;
  flex-direction: column;
  width: 190px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 20px;
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid;
  border-color: #d9d9d9;
}

.log-in .frame-12 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  position: relative;
  flex: 0 0 auto;
}

.log-in .vector-3 {
  position: absolute;
  width: 20px;
  height: 23px;
  top: 0;
  left: 3px;
}

.log-in .overlap-wrapper {
  position: absolute;
  width: 400px;
  height: 14px;
  top: 402px;
  left: 0;
}

.log-in .overlap-3 {
  position: relative;
  height: 14px;
}

.log-in .line {
  position: absolute;
  width: 400px;
  height: 2px;
  top: 7px;
  left: 0;
}

.log-in .frame-13 {
  display: flex;
  width: 20px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0px 3px;
  position: absolute;
  top: 0;
  left: 191px;
  background-color: #ffffff;
}

.log-in .text-wrapper-8 {
  position: relative;
  width: fit-content;
  margin-top: -1.00px;
  font-family: "Poppins", Helvetica;
  font-weight: 500;
  color: #000000;
  font-size: 9px;
  letter-spacing: 0;
  line-height: normal;
}

.log-in .chris-lee {
  position: absolute;
  width: 782px;
  height: 1042px;
  top: 0;
  left: 754px;
  object-fit: cover;
}"""
        
        # Create complete HTML with embedded CSS
        complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Template</title>
    <style>
{login_css}
    </style>
</head>
<body>
{login_html}
</body>
</html>"""
        
        # Extract global CSS from the embedded HTML
        import re
        globals_css_match = re.search(r'<style>\s*(/\* Global CSS Variables and Reset Styles \*/\s*.*?)\s*</style>', login_html, re.DOTALL)
        globals_css = globals_css_match.group(1) if globals_css_match else ""
        
        return {
            "success": True,
            "template_id": "default",
            "template_name": "Login Template",
            "ui_codes": {
                "html_export": login_html,
                "globals_css": globals_css,
                "style_css": login_css,
                "js": "",
                "complete_html": complete_html
            },
            "metadata": {
                "category": "login",
                "description": "A clean and modern sign-in page for user authentication"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching default UI codes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class UICodeModification(BaseModel):
    template_id: str
    modification_type: str  # 'css_change', 'html_change', 'js_change', 'complete_change'
    changes: Dict[str, Any]
    session_id: Optional[str] = None

class UICodeModificationResponse(BaseModel):
    success: bool
    message: str
    updated_codes: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None

@app.post("/api/ui-codes/modify", response_model=UICodeModificationResponse)
async def modify_ui_codes(modification: UICodeModification):
    """Modify UI codes and store in temporary JSON files"""
    try:
        import json
        import os
        from pathlib import Path
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp_ui_files")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate unique filename based on template_id and session_id
        session_id = modification.session_id or "default"
        filename = f"ui_codes_{modification.template_id}_{session_id}.json"
        file_path = temp_dir / filename
        
        # Get current UI codes (either from existing file or default)
        current_data = {}
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                # Extract current codes from the flat structure
                current_codes = current_data.get("current_codes", {})
                history = current_data.get("history", [])
        else:
            # Initialize with default codes if no existing file
            if modification.template_id == "default":
                default_response = await get_default_ui_codes()
                current_codes = default_response["ui_codes"]
            else:
                # Fetch from MongoDB
                ui_tools = UIPreviewTools()
                result = ui_tools.get_template_code(modification.template_id)
                if result["success"]:
                    current_codes = result["code_data"]
                else:
                    raise HTTPException(status_code=404, detail="Template not found")
            history = []
        
        # Apply modifications based on type
        updated_codes = current_codes.copy()
        modification_description = ""
        
        if modification.modification_type == "css_change":
            # Modify CSS properties
            for selector, properties in modification.changes.items():
                if "style_css" not in updated_codes:
                    updated_codes["style_css"] = ""
                
                # Simple CSS modification - append new styles
                new_css = f"\n{selector} {{\n"
                for prop, value in properties.items():
                    new_css += f"    {prop}: {value};\n"
                new_css += "}\n"
                updated_codes["style_css"] += new_css
                
                # Create modification description
                props_list = [f"{prop} to {value}" for prop, value in properties.items()]
                modification_description = f"Changed {selector} styles: set {', '.join(props_list)}"
                
        elif modification.modification_type == "html_change":
            # Modify HTML content
            if "html_export" in modification.changes:
                updated_codes["html_export"] = modification.changes["html_export"]
                modification_description = "Updated HTML content"
                
        elif modification.modification_type == "js_change":
            # Modify JavaScript
            if "js" in modification.changes:
                updated_codes["js"] = modification.changes["js"]
                modification_description = "Updated JavaScript code"
                
        elif modification.modification_type == "complete_change":
            # Complete replacement of codes
            updated_codes.update(modification.changes)
            modification_description = "Complete code replacement"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid modification type")
        
        # Rebuild complete HTML
        updated_codes["complete_html"] = _rebuild_complete_html(
            updated_codes.get("html_export", ""),
            updated_codes.get("globals_css", "") + updated_codes.get("style_css", ""),
            updated_codes.get("js", "")
        )
        
        # Add to history
        history.append({
            "timestamp": datetime.now().isoformat(),
            "modification": modification_description
        })
        
        # Save to JSON file with clean, flat structure
        save_data = {
            "template_id": modification.template_id,
            "session_id": session_id,
            "last_updated": datetime.now().isoformat(),
            "current_codes": updated_codes,
            "history": history
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return UICodeModificationResponse(
            success=True,
            message="UI codes modified successfully",
            updated_codes=updated_codes,
            file_path=str(file_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying UI codes: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def _rebuild_complete_html(html_code: str, css_code: str, js_code: str) -> str:
    """Rebuild complete HTML document with embedded CSS and JS"""
    # If html_code already has DOCTYPE, use it as is
    if html_code.strip().startswith("<!DOCTYPE"):
        # Insert CSS into head section
        css_insert = f'<style>\n{css_code}\n</style>' if css_code else ''
        head_end = html_code.find("</head>")
        if head_end != -1:
            html_with_css = html_code[:head_end] + css_insert + html_code[head_end:]
        else:
            # No head section, insert at beginning
            html_with_css = f'<head>\n{css_insert}\n</head>\n{html_code}'
    else:
        # Create complete HTML document
        html_with_css = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Editor</title>
    <style>
{css_code}
    </style>
</head>
<body>
{html_code}
    <script>
{js_code}
    </script>
</body>
</html>"""
    
    return html_with_css

@app.get("/api/ui-codes/session/{session_id}")
async def get_session_ui_codes(session_id: str):
    """Get UI codes for a specific session from temporary files"""
    try:
        import json
        from pathlib import Path
        
        temp_dir = Path("temp_ui_files")
        
        # Find the most recent file for this session
        session_files = list(temp_dir.glob(f"ui_codes_{session_id}.json"))
        
        if not session_files:
            # Return default if no session file exists
            return await get_default_ui_codes()
        
        # Get the most recent file
        latest_file = max(session_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "template_id": data["template_id"],
            "session_id": session_id,
            "ui_codes": {
                "html_export": data["current_codes"]["html_export"],
                "globals_css": data["current_codes"]["globals_css"],
                "style_css": data["current_codes"]["style_css"],
                "js": data["current_codes"]["js"],
                "complete_html": data["current_codes"]["complete_html"]
            },
            "metadata": {
                "last_modified": data["last_updated"],
                "file_path": str(latest_file),
                "history_count": len(data.get("history", [])),
                "template_info": data.get("template_info", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching session UI codes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/ui-editor/chat", response_model=UIEditorChatResponse)
async def ui_editor_chat(request: UIEditorChatRequest):
    """AI-powered chat endpoint for UI editor that can modify UI codes using enhanced orchestrator"""
    try:
        session_id = request.session_id or "default_session"
        
        # Get current UI codes if not provided
        current_ui_codes = request.current_ui_codes
        if not current_ui_codes:
            # Fetch current UI codes for the session
            try:
                session_response = await get_session_ui_codes(session_id)
                if session_response.get("success") and session_response.get("ui_codes"):
                    current_ui_codes = session_response["ui_codes"]["current_codes"]
                else:
                    # Fallback to default template
                    default_response = await get_default_ui_codes()
                    current_ui_codes = default_response["ui_codes"]
            except Exception as e:
                logger.error(f"Error fetching current UI codes: {e}")
                # Use default template as fallback
                default_response = await get_default_ui_codes()
                current_ui_codes = default_response["ui_codes"]
        
        # Use the enhanced orchestrator for Phase 2 editing
        from agents.lean_flow_orchestrator import LeanFlowOrchestrator
        orchestrator = LeanFlowOrchestrator()
        
        # Handle the editing phase request
        response = orchestrator.handle_editing_phase(
            user_message=request.message,
            current_ui_state=current_ui_codes,
            session_id=session_id
        )
        
        # Extract modifications and new UI codes if available
        modifications = response.get("modifications")
        new_ui_codes = response.get("metadata", {}).get("new_ui_codes")
        
        return UIEditorChatResponse(
            success=response["success"],
            response=response["response"],
            ui_modifications=modifications,
            session_id=session_id,
            metadata={
                "intent": response.get("metadata", {}).get("intent", "unknown"),
                "new_ui_codes": new_ui_codes,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error in UI editor chat: {e}")
        return UIEditorChatResponse(
            success=False,
            response=f"Sorry, I encountered an error: {str(e)}",
            session_id=request.session_id or "default_session"
        )

@app.post("/api/template-to-json", response_model=TemplateToJsonResponse)
async def template_to_json(request: TemplateToJsonRequest):
    """Convert selected template from MongoDB to JSON file for Phase 2 transition"""
    try:
        from bson import ObjectId
        from tools.ui_preview_tools import UIPreviewTools
        import json
        from pathlib import Path
        
        # Validate template_id format
        try:
            ObjectId(request.template_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid template ID format")
        
        # Get template data from MongoDB
        ui_tools = UIPreviewTools()
        template_result = ui_tools.get_template_code(request.template_id)
        
        if not template_result["success"]:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Extract template data from the correct structure
        template_name = template_result.get("template_name", "Unknown Template")
        html_export = template_result.get("html_export", "")
        global_css = template_result.get("global_css", "")
        style_css = template_result.get("style_css", "")
        metadata = template_result.get("metadata", {})
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp_ui_files")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate filename for the session
        filename = f"ui_codes_{request.template_id}_{request.session_id}.json"
        file_path = temp_dir / filename
        
        # Create JSON structure
        json_data = {
            "template_id": request.template_id,
            "session_id": request.session_id,
            "last_updated": datetime.now().isoformat(),
            "current_codes": {
                "html_export": html_export,
                "globals_css": global_css,
                "style_css": style_css,
                "js": "",  # No JS in current templates
                "complete_html": _rebuild_complete_html(html_export, global_css + style_css, "")
            },
            "history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "modification": f"Template '{template_name}' selected from Phase 1"
                }
            ],
            "template_info": {
                "name": template_name,
                "category": metadata.get("category", request.category or "unknown"),
                "description": metadata.get("description", ""),
                "tags": metadata.get("tags", [])
            }
        }
        
        # Save to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Template JSON created: {file_path}")
        
        return TemplateToJsonResponse(
            success=True,
            message=f"Template '{template_name}' converted to JSON successfully",
            template_data=json_data,
            file_path=str(file_path)
        )
        
    except Exception as e:
        logger.error(f"Error converting template to JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 