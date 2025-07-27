from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import base64
from io import BytesIO

from agents.orchestrator import AutoGenOrchestrator

load_dotenv()

# Create AutoGen API router
autogen_app = FastAPI(title="AutoGen Multi-Agent API", description="API for UI Mockup Generation using AutoGen")

# Add CORS middleware
autogen_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = AutoGenOrchestrator()

# Request/Response models
class ProjectStartRequest(BaseModel):
    project_name: str
    user_prompt: str
    logo_image: Optional[str] = None  # Base64 encoded image

class TemplateConfirmationRequest(BaseModel):
    template_id: Optional[str] = None

class ModificationRequest(BaseModel):
    user_feedback: str

class ProjectStatusResponse(BaseModel):
    project_name: str
    phase: str
    selected_template: str
    total_modifications: int
    validation_status: str

# API Endpoints

@autogen_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AutoGen Multi-Agent System",
        "agents": [
            "User Proxy Agent",
            "Requirement Understanding Agent",
            "UI Recommender Agent", 
            "UI Modification Agent",
            "UI Editing Agent",
            "Report Generation Agent"
        ]
    }

@autogen_app.post("/project/start")
async def start_project(request: ProjectStartRequest):
    """Start a new UI mockup generation project"""
    
    try:
        # Add conversation entry
        orchestrator.add_conversation_entry("user", f"Started project: {request.project_name}")
        orchestrator.add_conversation_entry("user", f"Requirements: {request.user_prompt}")
        
        # Start the project
        result = orchestrator.start_project(
            project_name=request.project_name,
            user_prompt=request.user_prompt,
            logo_image=request.logo_image
        )
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting project: {str(e)}")

@autogen_app.post("/project/confirm-template")
async def confirm_template_selection(request: TemplateConfirmationRequest):
    """Confirm template selection and proceed to Phase 2"""
    
    try:
        # Add conversation entry
        orchestrator.add_conversation_entry("user", f"Confirmed template selection: {request.template_id or 'default'}")
        
        # Confirm template selection
        result = orchestrator.confirm_template_selection(request.template_id)
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming template: {str(e)}")

@autogen_app.get("/project/suggestions")
async def get_additional_pages_suggestions():
    """Get suggestions for additional pages"""
    
    try:
        result = orchestrator.get_additional_pages_suggestions()
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@autogen_app.post("/project/modify")
async def process_modification_request(request: ModificationRequest):
    """Process user modification request"""
    
    try:
        # Add conversation entry
        orchestrator.add_conversation_entry("user", f"Modification request: {request.user_feedback}")
        
        # Process modification
        result = orchestrator.process_modification_request(request.user_feedback)
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing modification: {str(e)}")

@autogen_app.post("/project/finalize")
async def finalize_project():
    """Finalize the project and generate report"""
    
    try:
        # Add conversation entry
        orchestrator.add_conversation_entry("user", "Requested project finalization")
        
        # Finalize project
        result = orchestrator.finalize_project()
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finalizing project: {str(e)}")

@autogen_app.get("/project/status")
async def get_project_status():
    """Get current project status"""
    
    try:
        return orchestrator.get_project_status()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting project status: {str(e)}")

@autogen_app.get("/project/conversation")
async def get_conversation_history():
    """Get conversation history"""
    
    try:
        return {
            "conversation": orchestrator.get_conversation_history()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

@autogen_app.post("/project/reset")
async def reset_project():
    """Reset the project to initial state"""
    
    try:
        result = orchestrator.reset_project()
        
        # Add system response to conversation
        orchestrator.add_conversation_entry("system", result["message"], result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting project: {str(e)}")

@autogen_app.get("/project/export")
async def export_project_data():
    """Export complete project data"""
    
    try:
        return orchestrator.export_project_data()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting project data: {str(e)}")

@autogen_app.get("/templates/categories")
async def get_template_categories():
    """Get available template categories"""
    
    try:
        return {
            "categories": ["landing", "login", "signup", "profile", "dashboard", "about", "contact", "pricing"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template categories: {str(e)}")

@autogen_app.get("/templates/{category}")
async def get_templates_by_category(category: str):
    """Get templates by category"""
    
    try:
        from agents.ui_recommender_agent import UIRecommenderAgent
        
        recommender = UIRecommenderAgent()
        templates = recommender.get_templates_by_category(category)
        
        return {
            "category": category,
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")

@autogen_app.get("/templates/{category}/{template_id}")
async def get_template_details(category: str, template_id: str):
    """Get detailed information about a specific template"""
    
    try:
        from agents.ui_recommender_agent import UIRecommenderAgent
        
        recommender = UIRecommenderAgent()
        template_details = recommender.get_template_details(template_id)
        
        if not template_details:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template details: {str(e)}")

# File upload endpoint for logos
@autogen_app.post("/upload/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload a logo image for analysis"""
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        content = await file.read()
        
        # Convert to base64
        base64_image = base64.b64encode(content).decode('utf-8')
        
        # Determine image type
        image_type = file.content_type.split('/')[-1]
        data_url = f"data:image/{image_type};base64,{base64_image}"
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "base64_data": data_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading logo: {str(e)}")

# WebSocket endpoint for real-time communication (optional)
@autogen_app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time communication"""
    
    try:
        await websocket.accept()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message (implement as needed)
            response = {
                "type": "message",
                "content": f"Received: {data}",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            # Send response back to client
            await websocket.send_text(str(response))
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(autogen_app, host="0.0.0.0", port=8001) 