from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import json

load_dotenv()

app = FastAPI(title="AI Mockup Backend", description="Backend for AI agent and prompt engineering")

# add new frontend URLs to allow CORS in the future
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# testing models for Claude API request/response, will change in the future
class ClaudeRequest(BaseModel):
    prompt: str
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class ClaudeResponse(BaseModel):
    response: str
    usage: Dict[str, Any]
    model: str

class PromptTestRequest(BaseModel):
    prompt: str
    test_cases: list[str] = []


CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY not found")

@app.get("/")
async def root():
    return {"message": "Model Server is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "claude_api_configured": bool(CLAUDE_API_KEY)}


# Main claude API calling function
@app.post("/api/claude", response_model=ClaudeResponse)
async def call_claude(request: ClaudeRequest):
    """
    Send a prompt to Claude API and return the response
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": []
        }
        
        # Add system prompt if provided
        if request.system_prompt:
            payload["messages"].append({
                "role": "user",
                "content": f"[System: {request.system_prompt}]\n\n{request.prompt}"
            })
        else:
            payload["messages"].append({
                "role": "user",
                "content": request.prompt
            })
        
        # Make the API call
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return ClaudeResponse(
            response=data["content"][0]["text"],
            usage=data.get("usage", {}),
            model=request.model
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/prompt-test")
async def test_prompt(request: PromptTestRequest):
    """
    Test a prompt with multiple test cases for prompt engineering
    """
    results = []
    
    for i, test_case in enumerate(request.test_cases):
        try:
            #test request
            test_request = ClaudeRequest(
                prompt=f"{request.prompt}\n\nTest case {i+1}: {test_case}",
                max_tokens=500,
                temperature=0.3
            )
            
            # Call Claude API
            response = await call_claude(test_request)
            
            results.append({
                "test_case": test_case,
                "response": response.response,
                "usage": response.usage,
                "success": True
            })
            
        except Exception as e:
            results.append({
                "test_case": test_case,
                "error": str(e),
                "success": False
            })
    
    return {
        "prompt": request.prompt,
        "test_results": results,
        "total_tests": len(request.test_cases),
        "successful_tests": len([r for r in results if r["success"]])
    }

# List of available models
@app.get("/api/models")
async def get_available_models():
    """
    Get list of available Claude models
    """
    return {
        "models": [
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful model for complex tasks"
            },
            {
                "id": "claude-3-sonnet-20240229", 
                "name": "Claude 3 Sonnet",
                "description": "Balanced model for most tasks"
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku", 
                "description": "Fastest model for simple tasks"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True) 