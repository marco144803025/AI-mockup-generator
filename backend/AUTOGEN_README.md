# AutoGen Multi-Agent System for UI Mockup Generation

This implementation provides a sophisticated multi-agent system using Microsoft's AutoGen framework to automate UI mockup generation through conversational AI agents.

## 🏗️ System Architecture

### **6 Specialized Agents:**

1. **User Proxy Agent** - Handles user interactions and workflow coordination
2. **Requirement Understanding Agent** - Analyzes user prompts and logos to extract structured requirements
3. **UI Recommender Agent** - Finds suitable UI templates based on requirements
4. **UI Modification Agent** - Understands modification requests and generates implementation plans
5. **UI Editing Agent** - Applies modifications to HTML/CSS templates
6. **Report Generation Agent** - Creates comprehensive PDF reports documenting the process

### **3-Phase Workflow:**

#### **Phase 1: Requirements Analysis & Template Selection**
- User provides requirements and optional logo
- Agents analyze requirements and extract UI specifications
- System recommends suitable templates with reasoning
- User confirms template selection

#### **Phase 2: Template Modification & User Feedback**
- Selected template becomes "master style" for the site
- User provides modification requests
- Agents analyze, plan, and apply modifications
- Real-time preview generation and validation
- Iterative feedback loop until satisfaction

#### **Phase 3: Finalization & Report Generation**
- Comprehensive validation of final template
- PDF report generation with detailed reasoning
- Project data export and summary

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

### **2. Set Environment Variables**
Create a `.env` file with your Claude API key:
```
CLAUDE_API_KEY=your_claude_api_key_here
```

### **3. Test the System**
```bash
python test_autogen.py
```

### **4. Start the AutoGen API Server**
```bash
python autogen_api.py
```

The API will be available at `http://localhost:8001` with interactive documentation at `http://localhost:8001/docs`

## 📁 Project Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py              # Base class for all agents
│   ├── user_proxy_agent.py        # User interaction agent
│   ├── requirement_understanding_agent.py  # Requirements analysis
│   ├── ui_recommender_agent.py    # Template recommendation
│   ├── ui_modification_agent.py   # Modification understanding
│   ├── ui_editing_agent.py        # Template editing
│   ├── report_generation_agent.py # Report generation
│   └── orchestrator.py            # Main coordinator
├── autogen_api.py                 # FastAPI endpoints
├── test_autogen.py               # Test script
├── requirements.txt              # Dependencies
└── AUTOGEN_README.md            # This file
```

## 🔧 API Endpoints

### **Project Management**
- `POST /project/start` - Start new UI project
- `POST /project/confirm-template` - Confirm template selection
- `POST /project/modify` - Process modification requests
- `POST /project/finalize` - Finalize project and generate report
- `GET /project/status` - Get current project status
- `GET /project/conversation` - Get conversation history
- `POST /project/reset` - Reset project to initial state

### **Template Management**
- `GET /templates/categories` - Get available categories
- `GET /templates/{category}` - Get templates by category
- `GET /templates/{category}/{template_id}` - Get template details

### **File Upload**
- `POST /upload/logo` - Upload logo for analysis

### **Real-time Communication**
- `WebSocket /ws` - Real-time communication (optional)

## 💬 Usage Examples

### **Starting a Project**
```python
import requests

# Start a new project
response = requests.post("http://localhost:8001/project/start", json={
    "project_name": "My Tech Startup Landing Page",
    "user_prompt": "I want a modern landing page for a tech startup with a clean design, hero section, and contact form",
    "logo_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."  # Optional
})

print(response.json())
```

### **Confirming Template Selection**
```python
# Confirm the recommended template
response = requests.post("http://localhost:8001/project/confirm-template", json={
    "template_id": "template_id_here"  # Optional, uses default if not provided
})
```

### **Requesting Modifications**
```python
# Request modifications
response = requests.post("http://localhost:8001/project/modify", json={
    "user_feedback": "Make the color scheme more vibrant and add a testimonials section"
})
```

### **Finalizing Project**
```python
# Finalize and generate report
response = requests.post("http://localhost:8001/project/finalize")
```

## 🎯 Key Features

### **Intelligent Template Matching**
- Multi-factor scoring system (category, style, components, brand personality)
- Fuzzy matching for similar tags and requirements
- Alternative recommendations with reasoning

### **Natural Language Processing**
- Converts vague user requests into structured modification plans
- Understands context and intent behind feedback
- Generates detailed reasoning for all decisions

### **Real-time Validation**
- HTML/CSS syntax validation
- Reference integrity checking
- Accessibility and responsive design validation

### **Comprehensive Reporting**
- Detailed PDF reports with decision reasoning
- Modification history and impact analysis
- Technical specifications and validation results

### **Conversation Memory**
- Maintains context throughout the project lifecycle
- Detailed conversation history for audit trails
- Exportable project data for analysis

## 🔍 Agent Capabilities

### **User Proxy Agent**
- ✅ Conversational interface management
- ✅ Workflow coordination between phases
- ✅ User confirmation handling
- ✅ Clear explanation of agent decisions

### **Requirement Understanding Agent**
- ✅ Natural language requirement analysis
- ✅ Logo and brand element analysis
- ✅ UI specification extraction
- ✅ Template search criteria generation

### **UI Recommender Agent**
- ✅ Database template matching
- ✅ Multi-factor scoring algorithm
- ✅ Alternative recommendation generation
- ✅ Detailed reasoning for selections

### **UI Modification Agent**
- ✅ Natural language modification analysis
- ✅ Element selector identification
- ✅ Modification plan generation
- ✅ Priority-based change ordering

### **UI Editing Agent**
- ✅ HTML/CSS modification application
- ✅ Code validation and error checking
- ✅ Preview generation
- ✅ Backup and version management

### **Report Generation Agent**
- ✅ Comprehensive PDF report creation
- ✅ Decision reasoning documentation
- ✅ Technical specification inclusion
- ✅ Professional formatting and styling

## 🛠️ Configuration

### **Environment Variables**
```bash
CLAUDE_API_KEY=your_claude_api_key
MONGODB_URI=your_mongodb_connection_string  # Optional
```

### **Agent Configuration**
Each agent can be configured with different models and parameters in their respective classes:
```python
# Example: Change model for specific agent
class CustomUserProxyAgent(UserProxyAgent):
    def __init__(self):
        super().__init__()
        self.model = "claude-3-5-haiku-20241022"  # Different model
```

## 🧪 Testing

### **Run All Tests**
```bash
python test_autogen.py
```

### **Test Individual Components**
```python
# Test specific agent
from agents.user_proxy_agent import UserProxyAgent
agent = UserProxyAgent()
result = agent.understand_requirements("I want a modern landing page")
print(result)
```

## 📊 Performance Considerations

### **Optimization Tips**
1. **Caching**: Template recommendations are cached for faster responses
2. **Async Processing**: Long-running operations are handled asynchronously
3. **Memory Management**: Conversation history is managed efficiently
4. **Error Handling**: Comprehensive error handling with graceful fallbacks

### **Scalability**
- Modular agent architecture allows easy scaling
- Database integration for template storage
- API-first design for frontend integration
- WebSocket support for real-time updates

## 🔒 Security & Privacy

### **Data Protection**
- No sensitive data stored in conversation history
- Secure API key management
- Input validation and sanitization
- CORS configuration for frontend security

### **Access Control**
- API rate limiting (can be implemented)
- Authentication middleware ready
- Audit trail for all operations

## 🚀 Integration with Frontend

### **React Integration Example**
```javascript
// Start project
const startProject = async (projectName, userPrompt, logoImage) => {
  const response = await fetch('http://localhost:8001/project/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_name: projectName, user_prompt: userPrompt, logo_image: logoImage })
  });
  return response.json();
};

// Process modifications
const requestModification = async (feedback) => {
  const response = await fetch('http://localhost:8001/project/modify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_feedback: feedback })
  });
  return response.json();
};
```

## 🎯 Future Enhancements

### **Planned Features**
1. **Multi-language Support** - Internationalization for agents
2. **Advanced Analytics** - Usage patterns and optimization insights
3. **Custom Agent Training** - Domain-specific agent fine-tuning
4. **Real-time Collaboration** - Multi-user project collaboration
5. **Advanced Preview** - Interactive preview with live editing
6. **Integration APIs** - Third-party design tool integrations

### **Extensibility**
The modular architecture makes it easy to:
- Add new agents for specific tasks
- Integrate with different AI models
- Extend template databases
- Add new validation rules
- Implement custom reporting formats

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

### **Code Standards**
- Follow PEP 8 for Python code
- Add docstrings for all functions
- Include type hints
- Write comprehensive tests
- Update documentation

## 📞 Support

For questions, issues, or contributions:
1. Check the test script for common issues
2. Review the API documentation at `/docs`
3. Examine the conversation history for debugging
4. Check the validation results for error details

---

**🎉 Congratulations!** You now have a fully functional AutoGen multi-agent system for UI mockup generation. The system provides intelligent, conversational AI agents that can understand requirements, recommend templates, apply modifications, and generate comprehensive reports - all while maintaining explainability and user control throughout the process. 