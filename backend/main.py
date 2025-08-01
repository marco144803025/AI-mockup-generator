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
    """Get default UI codes for the editor (placeholder content)"""
    try:
        # Return a simple default template
        default_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Editor</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        .title {
            font-size: 2em;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">Welcome!</h1>
        <p class="subtitle">This is your UI editor. Start customizing your template!</p>
        <button class="button" id="demo-button">Click Me!</button>
    </div>
    
    <script>
        document.getElementById('demo-button').addEventListener('click', function() {
            this.style.background = '#ff4444';
            this.textContent = 'Button Clicked!';
        });
    </script>
</body>
</html>"""
        
        return {
            "success": True,
            "template_id": "default",
            "template_name": "Default Template",
            "ui_codes": {
                "html_export": default_html,
                "globals_css": "",
                "style_css": "",
                "js": "",
                "complete_html": default_html
            },
            "metadata": {
                "category": "default",
                "description": "Default template for the UI editor"
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
        session_files = list(temp_dir.glob(f"ui_codes_*_{session_id}.json"))
        
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
            "ui_codes": data["current_codes"],
            "metadata": {
                "last_modified": data["last_updated"],
                "file_path": str(latest_file),
                "history_count": len(data.get("history", []))
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 