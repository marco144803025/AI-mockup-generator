# AI Mockup Backend

A Python backend for AI agent prototyping and prompt engineering using Claude's API.

## Features

- **FastAPI Server**: RESTful API for Claude integration
- **MCP Server**: Model Context Protocol server for AI agent tools (will be implemented in the future)
- **Prompt Engineering**: Tools for testing and iterating on prompts
- **Claude API Integration**: Direct access to Claude models

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate on Windows
venv\Scripts\activate

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Create a .env key to include your claude api key

```
## Usage

### Start the FastAPI Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Call Claude API
```bash
curl -X POST http://localhost:8000/api/claude \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello! Can you help me with prompt engineering?",
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "temperature": 0.7
  }'
```

#### Test Prompt with Multiple Cases
```bash
curl -X POST http://localhost:8000/api/prompt-test \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a creative story about a robot learning to paint",
    "test_cases": [
      "The robot discovers color theory",
      "The robot paints its first masterpiece"
    ]
  }'
```

#### Get Available Models
```bash
curl http://localhost:8000/api/models
```

### MCP Server

The MCP server provides tools for AI agent integration:

```bash
python mcp_server.py
```

#### Available MCP Tools

1. **call_claude**: Send prompts to Claude API
2. **test_prompt**: Test prompts with multiple test cases
3. **get_models**: Get available Claude models

## Prompt Engineering Workflow

### 1. Basic Prompt Testing

Use the `/api/prompt-test` endpoint to test your prompts with different scenarios:

```python
import requests

# Test a prompt with multiple cases
response = requests.post("http://localhost:8000/api/prompt-test", json={
    "prompt": "Explain quantum computing in simple terms",
    "test_cases": [
        "For a 10-year-old child",
        "For a high school student", 
        "For a college graduate"
    ]
})

print(response.json())
```

### 2. Iterative Prompt Development

1. Start with a basic prompt
2. Test with various scenarios
3. Analyze responses for consistency
4. Refine the prompt based on results
5. Repeat until satisfied

### 3. System Prompts

Use system prompts to set the AI's behavior:

```python
response = requests.post("http://localhost:8000/api/claude", json={
    "prompt": "Write a product description",
    "system_prompt": "You are a marketing expert. Write compelling, concise product descriptions that highlight benefits and features.",
    "temperature": 0.3
})
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI server
├── mcp_server.py        # MCP server implementation
├── requirements.txt     # Python dependencies
├── env_template.txt     # Environment variables template
└── README.md           # This file
```

### Adding New Tools

To add new tools to the MCP server:

1. Add the tool definition in `mcp_server.py` `_register_tools()` method
2. Implement the tool function
3. Add the handler in `handle_tool_call()` method

### Error Handling

The backend includes comprehensive error handling for:
- Invalid API keys
- Network errors
- Malformed requests
- Claude API errors

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your `.env` file contains a valid Claude API key
2. **Import Errors**: Ensure you've activated the virtual environment
3. **Port Already in Use**: Change the port in `.env` file or kill the existing process

### Debug Mode

Run the server in debug mode for more detailed error messages:

```bash
uvicorn main:app --reload --log-level debug
```

## Next Steps

1. **Frontend Integration**: Connect your React frontend to these APIs
2. **Advanced Prompt Engineering**: Add more sophisticated testing frameworks
3. **MCP Client**: Build an MCP client to use the server tools
4. **Custom Tools**: Add domain-specific tools for your use case

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI. 