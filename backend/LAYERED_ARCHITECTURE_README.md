# Layered AI Architecture

This document describes the new layered architecture implementation for the AI UI Workflow system.

## Architecture Overview

The system now uses a **7-layer architecture** that provides robust, scalable, and maintainable AI workflow management:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Layered Orchestrator                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Control   │ │ Intelligence│ │   Memory    │          │
│  │   Layer     │ │   Layer     │ │   Layer     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Tools     │ │ Validation  │ │  Feedback   │          │
│  │   Layer     │ │   Layer     │ │   Layer     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Recovery Layer                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 External Systems                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   MongoDB   │ │   Claude    │ │   Redis     │          │
│  │  Database   │ │     API     │ │   Cache     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. **Recovery Layer** (`recovery_layer.py`)
- **Purpose**: Error handling, retry logic, and backoff strategies
- **Features**:
  - Exponential backoff retry mechanisms
  - Circuit breaker patterns
  - Critical error handling with recovery actions
  - Multiple retry strategies (linear, exponential, fibonacci)

### 2. **Feedback Layer** (`feedback_layer.py`)
- **Purpose**: Human oversight and approval workflows
- **Features**:
  - Feedback request management
  - Approval/rejection workflows
  - Deadline management
  - Auto-approval for low-priority items
  - Feedback history tracking

### 3. **Intelligence Layer** (`intelligence_layer.py`)
- **Purpose**: LLM calling and response handling
- **Features**:
  - Multiple LLM provider support (Anthropic, OpenAI, Google)
  - Response format processing (text, JSON, structured)
  - System prompt management
  - Conversation context creation
  - Structured data extraction

### 4. **Memory Layer** (`memory_layer.py`)
- **Purpose**: Context persistence across interactions
- **Features**:
  - Redis and in-memory storage options
  - Session context management
  - Conversation history
  - Project state persistence
  - User preferences storage
  - TTL-based expiration

### 5. **Tools Layer** (`tools_layer.py`)
- **Purpose**: External system integration capabilities
- **Features**:
  - Database query tools
  - API call tools
  - File operation tools
  - Template generation tools
  - Image processing tools
  - Notification tools
  - Tool execution history and statistics

### 6. **Validation Layer** (`validation_layer.py`)
- **Purpose**: QA, structured data enforcement, schema validation
- **Features**:
  - JSON schema validation
  - Input validation (email, URL, etc.)
  - Template data validation
  - HTML/CSS validation
  - User input validation
  - Validation result tracking

### 7. **Control Layer** (`control_layer.py`)
- **Purpose**: Business logic for handling different user inputs
- **Features**:
  - Input classification (question, request, complaint, etc.)
  - Response type determination
  - Action execution planning
  - Conversation flow management
  - Business rule enforcement

## Workflow Process

### User Interaction Flow:

1. **Initial Load** → Frontend shows category selection
2. **Category Selection** → User chooses from available categories
3. **Multi-Agent Activation** → System switches to layered orchestrator
4. **Conversation** → All subsequent interactions use the multi-agent system

### Message Processing Flow:

1. **User Input** → Frontend sends message to appropriate endpoint
2. **Control Layer** → Classifies input type and extracts data
3. **Validation Layer** → Validates input format and content
4. **Memory Layer** → Stores conversation context
5. **Control Layer** → Generates initial response
6. **Intelligence Layer** → Enhances response with LLM (if needed)
7. **Tools Layer** → Executes required actions
8. **Memory Layer** → Updates session state
9. **Validation Layer** → Validates final response
10. **Response** → Returns enhanced response to frontend

### Error Handling:

- **Recovery Layer** → Handles all errors with retry logic
- **Circuit Breaker** → Prevents cascading failures
- **Graceful Degradation** → System continues working with reduced functionality
- **Error Logging** → Comprehensive error tracking and reporting

## Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your_claude_api_key"
export REDIS_URL="redis://localhost:6379"  # Optional
export MONGODB_URI="your_mongodb_connection_string"
```

### Running the System

```bash
# Start the backend
cd backend
python main.py

# Start the frontend (in another terminal)
cd frontend
npm start
```

### Testing

```bash
# Test the layered orchestrator
cd backend
python test_layered_orchestrator.py

# Test the API endpoints
curl http://localhost:8000/api/health
```

## API Endpoints

### New Endpoints:

- `POST /api/chat` - Main chat endpoint using layered orchestrator (multi-agent)
- `GET /api/session/status` - Get current session status
- `POST /api/session/reset` - Reset the current session
- `GET /api/health` - Health check with orchestrator status

### Legacy Endpoints:

- `POST /api/claude` - Direct Claude API calls (used for category selection)
- `GET /api/templates/categories` - Get available categories
- `GET /api/templates/category-constraints/{category}` - Get category constraints

## Configuration

### Environment Variables:

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
MONGODB_URI=your_mongodb_connection_string

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

### Layer Configuration:

Each layer can be configured independently:

```python
# Example: Configure recovery layer
orchestrator.recovery.max_retries = 5
orchestrator.recovery.base_delay = 2.0

# Example: Configure memory layer
orchestrator.memory.use_redis = True
orchestrator.memory.default_ttl = 3600
```

## Monitoring and Observability

### Session Status:

```python
status = orchestrator.get_session_status()
print(f"Session ID: {status['session_id']}")
print(f"Memory Stats: {status['memory_stats']}")
print(f"Validation Summary: {status['validation_summary']}")
print(f"Tool Statistics: {status['tool_statistics']}")
```

### Health Check:

```bash
curl http://localhost:8000/api/health
```

Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "orchestrator": "ready",
  "session_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Migration from Old System

### Frontend Changes:

- Updated `ChatScreen.js` to show category selection first
- Added multi-agent system activation after category selection
- Enhanced error handling
- Improved UI with new CSS styling

### Backend Changes:

- Implemented both direct Claude API and layered orchestrator
- Added comprehensive error handling
- Implemented session persistence
- Added validation and feedback mechanisms

### Backward Compatibility:

- Legacy `/api/claude` endpoint works for category selection
- Existing database structure unchanged
- Frontend can work with both old and new systems

## Development

### Adding New Tools:

```python
# In tools_layer.py
def my_custom_tool(self, param1: str, param2: int) -> Dict[str, Any]:
    """Custom tool implementation"""
    try:
        # Tool logic here
        return {"success": True, "result": "tool_output"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Register the tool
self.register_tool("my_custom_tool", self.my_custom_tool, {
    "type": ToolType.API_CALL,
    "description": "My custom tool",
    "parameters": {
        "param1": "string",
        "param2": "integer"
    }
})
```

### Adding New Validators:

```python
# In validation_layer.py
def validate_custom_field(self, value: str) -> ValidationResult:
    """Custom field validator"""
    if not value:
        return ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message="Field is required",
            field="custom_field"
        )
    return ValidationResult(
        is_valid=True,
        level=ValidationLevel.INFO,
        message="Field is valid"
    )

# Register the validator
self.register_validator("custom_field", validate_custom_field)
```

## Benefits

### 1. **Robustness**
- Comprehensive error handling with retry logic
- Circuit breaker patterns prevent cascading failures
- Graceful degradation when components fail

### 2. **Scalability**
- Modular design allows independent scaling
- Redis caching for performance
- Async processing for better throughput

### 3. **Maintainability**
- Clear separation of concerns
- Easy to add new features
- Comprehensive logging and monitoring

### 4. **Observability**
- Detailed session tracking
- Performance metrics
- Error reporting and debugging

### 5. **Flexibility**
- Easy to swap components
- Configurable behavior
- Plugin architecture for tools

## Future Enhancements

### Planned Features:

1. **Advanced Analytics**
   - User behavior tracking
   - Performance optimization
   - A/B testing capabilities

2. **Enhanced Tools**
   - Image generation tools
   - Code generation tools
   - Integration with external APIs

3. **Advanced Validation**
   - Machine learning-based validation
   - Real-time feedback
   - Quality scoring

4. **Distributed Processing**
   - Multi-node deployment
   - Load balancing
   - High availability

## Contributing

When contributing to the layered architecture:

1. **Follow the layer separation** - Keep concerns separated
2. **Add comprehensive tests** - Each layer should have unit tests
3. **Update documentation** - Keep this README current
4. **Use type hints** - All functions should have proper typing
5. **Add logging** - Include appropriate log messages
6. **Handle errors gracefully** - Use the recovery layer patterns

## Troubleshooting

### Common Issues:

1. **Redis Connection Failed**
   - Check Redis server is running
   - Verify REDIS_URL environment variable
   - System falls back to in-memory storage

2. **LLM API Errors**
   - Check ANTHROPIC_API_KEY is set
   - Verify API key has sufficient credits
   - Check network connectivity

3. **Database Connection Issues**
   - Verify MONGODB_URI is correct
   - Check MongoDB server is running
   - Ensure network connectivity

4. **Validation Errors**
   - Check input format matches expected schema
   - Review validation rules in validation layer
   - Check for required fields

### Debug Mode:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed session information
status = orchestrator.get_session_status()
print(json.dumps(status, indent=2))
```

---

This layered architecture provides a solid foundation for building robust, scalable AI applications with proper error handling, monitoring, and maintainability. 