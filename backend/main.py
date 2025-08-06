#!/usr/bin/env python3
"""
Clean FastAPI application with proper route ordering for screenshot service
"""

import asyncio
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import json
import anthropic
from pathlib import Path
from db import get_db
from datetime import datetime
from services.screenshot_service import get_screenshot_service

# Set Windows event loop policy for Playwright compatibility
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

# Pydantic models
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

class ScreenshotRequest(BaseModel):
    session_id: str
    html_content: str
    css_content: str

class LogoAnalysisRequest(BaseModel):
    message: str
    logo_image: str
    logo_filename: str
    session_id: str
    current_ui_codes: Optional[Dict[str, Any]] = None

# API Routes (must come before catch-all routes)

@app.get("/")
def read_root():
    return {"message": "UI Editor API is running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "UI Editor API is running"}

@app.get("/api/templates/categories")
async def get_template_categories():
    """Get all available template categories from the database"""
    try:
        from tools.mongodb_tools import MongoDBTools
        tools = MongoDBTools()
        result = tools.get_available_categories()
        
        if result["success"]:
            return {"success": True, "categories": result["categories"]}
        else:
            return {"success": False, "categories": [], "error": result.get("error", "Unknown error")}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"success": False, "categories": [], "error": str(e)}

@app.get("/api/templates/category-constraints/{category}")
async def get_category_constraints(category: str):
    """Get constraints and available options for a specific category"""
    try:
        from tools.mongodb_tools import MongoDBTools
        tools = MongoDBTools()
        result = tools.get_templates_by_category(category)
        
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Unknown error")}
        
        templates = result["templates"]
        
        # Extract unique tags, styles, and features from templates
        all_tags = set()
        all_styles = set()
        all_features = set()
        
        for template in templates:
            tags = template.get('tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                all_tags.update([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        # Categorize tags into styles and features
        style_keywords = ['modern', 'minimal', 'clean', 'bold', 'colorful', 'dark', 'light', 'sleek', 'elegant', 'professional', 'playful', 'soft', 'natural', 'futuristic']
        feature_keywords = ['responsive', 'mobile', 'desktop', 'tablet', 'interactive', 'animated', 'static', 'hero', 'navigation', 'footer', 'sidebar', 'form', 'button', 'image']
        
        for tag in all_tags:
            tag_lower = tag.lower()
            if any(style in tag_lower for style in style_keywords):
                all_styles.add(tag)
            elif any(feature in tag_lower for feature in feature_keywords):
                all_features.add(tag)
        
        return {
            "success": True,
            "templates_count": len(templates),
            "category_tags": list(all_tags),
            "styles": list(all_styles),
            "features": list(all_features)
        }
    except Exception as e:
        logger.error(f"Error fetching category constraints for {category}: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/chat")
async def chat_info():
    """Info endpoint for chat - POST method required"""
    return {
        "message": "This is the chat API endpoint. Use POST method with a JSON body containing your message.",
        "method": "POST",
        "endpoint": "/api/chat",
        "required_fields": ["message"],
        "optional_fields": ["session_id", "context"]
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Main chat endpoint that coordinates the multi-agent workflow"""
    try:
        # Extract session ID from request
        session_id = request.session_id or "demo_session"
        
        # Create orchestrator with session ID
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

@app.get("/api/ui-codes/default")
async def get_default_ui_codes():
    """Get default UI codes for new sessions with screenshot preview"""
    try:
        # Load the test template from the JSON file
        import json
        from pathlib import Path
        
        test_file_path = Path("temp_ui_files/ui_codes_test_session.json")
        
        if test_file_path.exists():
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            default_codes = {
                "current_codes": test_data["current_codes"],
                "template_info": test_data["template_info"]
            }
            logger.info("Loaded default template from test JSON file")
        else:
            # Fallback to hardcoded template if file doesn't exist
            logger.warning("Test JSON file not found, using fallback template")
            default_codes = {
                "current_codes": {
                    "html_export": """
                    <div class="container">
                        <header class="header">
                            <h1>Welcome to Our Platform</h1>
                            <p>This is a test template with screenshot preview</p>
                        </header>
                        <main class="main">
                            <div class="card">
                                <h2>Feature 1</h2>
                                <p>Amazing feature description goes here</p>
                                <button class="btn">Learn More</button>
                            </div>
                            <div class="card">
                                <h2>Feature 2</h2>
                                <p>Another amazing feature description</p>
                                <button class="btn">Get Started</button>
                            </div>
                        </main>
                    </div>
                    """,
                    "globals_css": """
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    """,
                    "style_css": """
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    
                    .header {
                        text-align: center;
                        color: white;
                        margin-bottom: 40px;
                    }
                    
                    .header h1 {
                        font-size: 3rem;
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    
                    .header p {
                        font-size: 1.2rem;
                        opacity: 0.9;
                    }
                    
                    .main {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 30px;
                    }
                    
                    .card {
                        background: white;
                        padding: 30px;
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        text-align: center;
                        transition: transform 0.3s ease;
                    }
                    
                    .card:hover {
                        transform: translateY(-5px);
                    }
                    
                    .card h2 {
                        color: #333;
                        margin-bottom: 15px;
                        font-size: 1.8rem;
                    }
                    
                    .card p {
                        color: #666;
                        margin-bottom: 20px;
                        line-height: 1.6;
                    }
                    
                    .btn {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
  border: none;
                        padding: 12px 30px;
                        border-radius: 25px;
                        font-size: 1rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .btn:hover {
                        transform: scale(1.05);
                        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                    }
                    """
                },
                "template_info": {
                    "name": "Test Template",
                    "category": "test"
                }
            }
        
        # Generate screenshot for default template
        try:
            screenshot_service = await get_screenshot_service()
            html_content = default_codes["current_codes"]["html_export"]
            css_content = default_codes["current_codes"]["globals_css"] + "\n" + default_codes["current_codes"]["style_css"]
            result = await screenshot_service.generate_screenshot(html_content, css_content, "default")
            screenshot_base64 = result["base64_image"] if result["success"] else ""
            logger.info(f"Screenshot generated for default template: success={result['success']}, length={len(screenshot_base64)}")
            if not result["success"]:
                logger.error(f"Screenshot generation failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error generating screenshot for default template: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            screenshot_base64 = ""
        
        return {
            "success": True,
            "template_id": "default",
            "ui_codes": default_codes,
            "screenshot_preview": screenshot_base64
        }
    except Exception as e:
        logger.error(f"Error fetching default UI codes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ui-codes/session/{session_id}")
async def get_session_ui_codes(session_id: str):
    """Get UI codes for a specific session using file manager"""
    try:
        from utils.file_manager import UICodeFileManager
        
        # Initialize file manager
        file_manager = UICodeFileManager()
        
        # Check if session exists in new file-based format
        if file_manager.session_exists(session_id):
            # Load session from file-based structure
            session_data = file_manager.load_session(session_id)
            if session_data:
                # Generate screenshot for session template
                try:
                    screenshot_service = await get_screenshot_service()
                    html_content = session_data["current_codes"]["html_export"]
                    css_content = session_data["current_codes"]["globals_css"] + "\n" + session_data["current_codes"]["style_css"]
                    result = await screenshot_service.generate_screenshot(html_content, css_content, session_id)
                    screenshot_base64 = result["base64_image"] if result["success"] else ""
                    logger.info(f"Screenshot generated for session {session_id}")
                except Exception as e:
                    logger.error(f"Error generating screenshot for session {session_id}: {e}")
                    screenshot_base64 = ""
                
                return {
                    "success": True,
                    "template_id": session_data["template_id"],
                    "session_id": session_id,
                    "ui_codes": {
                        "current_codes": {
                            "html_export": session_data["current_codes"]["html_export"],
                            "globals_css": session_data["current_codes"]["globals_css"],
                            "style_css": session_data["current_codes"]["style_css"]
                        },
                        "original_codes": session_data.get("original_codes", {}),
                        "template_info": session_data.get("template_info", {}),
                        "metadata": {
                            "last_modified": session_data["last_updated"],
                            "file_path": f"temp_ui_files/{session_id}/",
                            "history_count": len(session_data.get("history", [])),
                            "template_info": session_data.get("template_info", {})
                        }
                    },
                    "screenshot_preview": screenshot_base64
                }
        
        # Fallback: Check for old JSON format and migrate
        import json
        from pathlib import Path
        
        temp_dir = Path("temp_ui_files")
        session_files = list(temp_dir.glob(f"ui_codes_{session_id}.json"))
        
        if session_files:
            # Migrate from old JSON format to new file-based format
            latest_file = max(session_files, key=lambda x: x.stat().st_mtime)
            success = file_manager.migrate_from_json(session_id, str(latest_file))
            
            if success:
                # Retry loading the migrated session
                session_data = file_manager.load_session(session_id)
                if session_data:
                    # Generate screenshot for session template
                    try:
                        screenshot_service = await get_screenshot_service()
                        html_content = session_data["current_codes"]["html_export"]
                        css_content = session_data["current_codes"]["globals_css"] + "\n" + session_data["current_codes"]["style_css"]
                        result = await screenshot_service.generate_screenshot(html_content, css_content, session_id)
                        screenshot_base64 = result["base64_image"] if result["success"] else ""
                        logger.info(f"Screenshot generated for migrated session {session_id}")
                    except Exception as e:
                        logger.error(f"Error generating screenshot for migrated session {session_id}: {e}")
                        screenshot_base64 = ""
                    
                    return {
                        "success": True,
                        "template_id": session_data["template_id"],
                        "session_id": session_id,
                        "ui_codes": {
                            "current_codes": {
                                "html_export": session_data["current_codes"]["html_export"],
                                "globals_css": session_data["current_codes"]["globals_css"],
                                "style_css": session_data["current_codes"]["style_css"]
                            },
                            "original_codes": session_data.get("original_codes", {}),
                            "template_info": session_data.get("template_info", {}),
                            "metadata": {
                                "last_modified": session_data["last_updated"],
                                "file_path": f"temp_ui_files/{session_id}/",
                                "history_count": len(session_data.get("history", [])),
                                "template_info": session_data.get("template_info", {})
                            }
                        },
                        "screenshot_preview": screenshot_base64
                    }
        
        # Return default if no session file exists
        return await get_default_ui_codes()
        
    except Exception as e:
        logger.error(f"Error fetching session UI codes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/session/reset")
async def reset_session(session_id: str = None):
    """Reset session state and conversation history"""
    try:
        # Create orchestrator to handle session reset
        orchestrator = LeanFlowOrchestrator(session_id=session_id)
        result = orchestrator.reset_session()
        
        return {
            "success": True,
            "message": "Session reset successfully",
            "session_id": result.get("session_id", session_id)
        }
        
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

@app.post("/api/ui-codes/session/{session_id}/reset")
async def reset_session_to_original(session_id: str):
    """Reset UI codes for a specific session to their original state"""
    try:
        from utils.file_manager import UICodeFileManager
        
        # Initialize file manager
        file_manager = UICodeFileManager()
        
        # Check if session exists
        if not file_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Reset to original
        success = file_manager.reset_to_original(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset session to original state")
        
        # Generate new screenshot after reset
        try:
            screenshot_service = await get_screenshot_service()
            session_data = file_manager.load_session(session_id)
            if session_data:
                html_content = session_data["current_codes"]["html_export"]
                css_content = session_data["current_codes"]["globals_css"] + "\n" + session_data["current_codes"]["style_css"]
                result = await screenshot_service.generate_screenshot(html_content, css_content, session_id)
                screenshot_base64 = result["base64_image"] if result["success"] else ""
                logger.info(f"Screenshot regenerated after reset for session {session_id}")
            else:
                screenshot_base64 = ""
        except Exception as e:
            logger.error(f"Error generating screenshot after reset for session {session_id}: {e}")
            screenshot_base64 = ""
        
        return {
            "success": True,
            "message": "Session reset to original state successfully",
            "session_id": session_id,
            "screenshot_preview": screenshot_base64
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session {session_id} to original: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting session to original: {str(e)}")

@app.post("/api/ui-preview/generate-screenshot")
async def generate_ui_preview_screenshot(request: ScreenshotRequest):
    """Generate a screenshot preview of the UI template"""
    try:
        screenshot_service = await get_screenshot_service()
        # Access data from the request model
        result = await screenshot_service.generate_screenshot(
            request.html_content, 
            request.css_content, 
            request.session_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "screenshot_base64": result["base64_image"],
                "screenshot_path": result["screenshot_path"],
                "session_id": request.session_id
            }
        # 'else' is now correctly aligned with 'if'
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate screenshot: {result.get('error', 'Unknown error')}"
            )
    # 'except' is now correctly aligned with 'try'
    except Exception as e:
        logger.error(f"Error generating UI preview screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating screenshot: {str(e)}")

@app.post("/api/ui-editor/chat", response_model=UIEditorChatResponse)
async def ui_editor_chat(request: UIEditorChatRequest):
    """Handle UI Editor chat requests for modifying UI templates via agent system"""
    try:
        logger.info(f"UI Editor chat request for session: {request.session_id}")
        
        # Pass the request to the agent system (LeanFlowOrchestrator)
        session_id = request.session_id or "default"
        
        # Create orchestrator with session ID for UI editing context
        orchestrator = LeanFlowOrchestrator(session_id=session_id)
        
        # Process the UI modification request through the agent system
        result = await orchestrator.process_ui_edit_request(
            message=request.message,
            current_ui_codes=request.current_ui_codes,
            session_id=session_id
        )
        
        return UIEditorChatResponse(
            success=result.get("success", True),
            response=result.get("response", "Processing your UI modification request..."),
            ui_modifications=result.get("ui_modifications"),
            session_id=session_id,
            metadata=result.get("metadata", {"feature": "ui_editor_agent"})
        )
        
    except Exception as e:
        logger.error(f"Error in UI Editor chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing UI Editor request: {str(e)}")

@app.post("/api/ui-editor/analyze-logo")
async def analyze_logo(request: LogoAnalysisRequest):
    """Analyze uploaded logo and provide UI modification suggestions"""
    try:
        logger.info(f"Logo analysis request for session: {request.session_id}")
        
        # For now, return a placeholder response
        # TODO: Implement actual logo analysis logic
        response_message = f"I received your logo '{request.logo_filename}' with request: '{request.message}'. Logo analysis functionality is being implemented."
        
        return {
            "success": True,
            "response": response_message,
            "ui_modifications": None,
            "session_id": request.session_id,
            "metadata": {"feature": "logo_analysis", "status": "placeholder"}
        }
        
    except Exception as e:
        logger.error(f"Error in logo analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing logo: {str(e)}")

# Static file serving routes (must come after API routes)

@app.get("/templates/{template_name}/{file_name}")
async def serve_template_file(template_name: str, file_name: str):
    """Serve static files from UI templates directory"""
    try:
            
        # Construct the file path
        file_path = os.path.join("..", "UIpages", template_name, file_name)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_name} not found in template {template_name}")
        
        # Return the file
        return FileResponse(file_path)
        
    except Exception as e:
        logger.error(f"Error serving template file {file_name} from {template_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/css/{file_name}")
async def serve_css_file(file_name: str):
    """Serve CSS files that might be referenced in templates"""
    try:
        # Only allow CSS files for security
        if not file_name.endswith('.css'):
            raise HTTPException(status_code=404, detail="Only CSS files are allowed")
        
        # Look for the CSS file in UIpages subdirectories
        ui_pages_dir = os.path.join("..", "UIpages")
        if not os.path.exists(ui_pages_dir):
            raise HTTPException(status_code=404, detail="UIpages directory not found")
        
        # Search for the CSS file in subdirectories
        for root, dirs, files in os.walk(ui_pages_dir):
            if file_name in files:
                file_path = os.path.join(root, file_name)
                return FileResponse(file_path)
        
        # If not found, return 404
        raise HTTPException(status_code=404, detail=f"CSS file {file_name} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving CSS file {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 