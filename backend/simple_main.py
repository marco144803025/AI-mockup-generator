from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import json
import anthropic

load_dotenv()

app = FastAPI(title="AI Mockup Backend", description="Backend for AI agent and prompt engineering")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ClaudeRequest(BaseModel):
    prompt: Optional[str] = None
    image: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class ClaudeResponse(BaseModel):
    response: str
    usage: Dict[str, Any]
    model: str

class PromptTestRequest(BaseModel):
    prompt: str
    test_cases: List[str] = []

# Check for API key
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not CLAUDE_API_KEY:
    print("Warning: CLAUDE_API_KEY not found in environment variables")

@app.get("/")
async def root():
    return {"message": "AI Mockup Backend is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "claude_api_configured": bool(CLAUDE_API_KEY),
        "service": "AI Mockup Backend"
    }

@app.post("/api/claude", response_model=ClaudeResponse)
async def call_claude(request: ClaudeRequest):
    """Send a prompt to Claude API and return the response"""
    
    if not CLAUDE_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API key not configured")
    
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        
        messages = []
        
        if request.system_prompt:
            messages.append({"role": "user", "content": request.system_prompt})
        
        if request.image:
            # Handle image input
            if request.image.startswith('data:image'):
                image_data = request.image.split(',')[1]
            else:
                image_data = request.image
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": request.prompt or ""},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": request.prompt or ""})
        
        response = client.messages.create(
            model=request.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return ClaudeResponse(
            response=response.content[0].text,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
            model=request.model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Claude API: {str(e)}")

@app.post("/api/prompt-test")
async def test_prompt(request: PromptTestRequest):
    """Test a prompt with multiple test cases"""
    
    if not CLAUDE_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API key not configured")
    
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        results = []
        
        for i, test_case in enumerate(request.test_cases):
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[
                        {"role": "user", "content": f"Test case {i+1}: {test_case}\n\nPrompt: {request.prompt}"}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                
                results.append({
                    "test_case": test_case,
                    "response": response.content[0].text,
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "test_case": test_case,
                    "response": f"Error: {str(e)}",
                    "status": "error"
                })
        
        return {
            "prompt": request.prompt,
            "test_cases": request.test_cases,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing prompt: {str(e)}")

@app.get("/api/models")
async def get_available_models():
    """Get available Claude models"""
    return {
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ],
        "default_model": "claude-3-5-sonnet-20241022"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 