# 🚀 Complete Startup Guide - UI Mockup Generation System

This guide will walk you through starting the entire system, including both backend servers and the frontend application.

## 📊 System Architecture Overview

Before starting the system, you may want to review the system architecture diagrams located in the `diagrams/` directory:

- **[System Architecture Diagram](diagrams/system_architecture_diagram.html)** - High-level system architecture showing all components and their interactions
- **[Multi-Agent Workflow Diagram](diagrams/multi_agent_workflow_diagram.html)** - Detailed workflow showing how the 6 AI agents collaborate  
- **[Data Flow Diagram](diagrams/data_flow_diagram.html)** - Comprehensive data transformation and flow throughout the system

These diagrams provide professional, academic-grade visualizations of the system architecture and can be opened directly in any web browser.

## 📋 Prerequisites

Before starting, make sure you have:

- ✅ **Python 3.8+** installed
- ✅ **Node.js 16+** installed  
- ✅ **MongoDB** running (local or cloud)
- ✅ **Claude API Key** from Anthropic
- ✅ **Git** (for version control)

## 🔧 Step 1: Environment Setup

### **1.1 Clone/Setup Project**
```bash
# Navigate to your project directory
cd /n:/msc_project/upload

# Verify you're in the right directory
ls
# Should show: backend/, frontend/, UIpages/, README.md, etc.
```

### **1.2 Set Up Environment Variables**
Create a `.env` file in the `backend` directory:

```bash
cd backend
touch .env
```

Add your Claude API key to the `.env` file:
```env
CLAUDE_API_KEY=your_claude_api_key_here
MONGODB_URI=mongodb://localhost:27017/ui_mockup_db
```

**To get a Claude API key:**
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up/Login
3. Create a new API key
4. Copy the key to your `.env` file

## 🐍 Step 2: Backend Setup

### **2.1 Install Python Dependencies**
```bash
# Make sure you're in the backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **2.2 Test AutoGen System**
```bash
# Test the AutoGen multi-agent system
python test_autogen.py
```

You should see output like:
```
🚀 Starting AutoGen Multi-Agent System Tests
==================================================
🧪 Testing AutoGen Multi-Agent System...
1. Testing imports...
✅ Orchestrator imported successfully
2. Testing orchestrator initialization...
✅ Orchestrator initialized successfully
...
🎉 All tests passed! Your AutoGen system is ready to use.
```

### **2.3 Start the Main Backend Server**
```bash
# Start the main FastAPI server (Claude API integration)
python main.py
```

You should see:
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Main Backend Server**: `http://localhost:8000`
**API Documentation**: `http://localhost:8000/docs`

### **2.4 Start the AutoGen API Server**
Open a **new terminal window** and run:

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # macOS/Linux

# Start AutoGen API server
python autogen_api.py
```

You should see:
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

**AutoGen API Server**: `http://localhost:8001`
**AutoGen API Documentation**: `http://localhost:8001/docs`

## ⚛️ Step 3: Frontend Setup

### **3.1 Install Frontend Dependencies**
Open a **new terminal window**:

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### **3.2 Start Frontend Development Server**
```bash
# Start the React development server
npm start
```

You should see:
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.
```

**Frontend Application**: `http://localhost:3000`

## 🌐 Step 4: Verify Everything is Running

### **4.1 Check All Services**
You should now have **3 services** running:

1. **Main Backend Server**: `http://localhost:8000`
2. **AutoGen API Server**: `http://localhost:8001`  
3. **Frontend Application**: `http://localhost:3000`

### **4.2 Test API Endpoints**
Visit these URLs in your browser to verify everything works:

- **Main API Health**: `http://localhost:8000/health`
- **AutoGen API Health**: `http://localhost:8001/health`
- **Main API Docs**: `http://localhost:8000/docs`
- **AutoGen API Docs**: `http://localhost:8001/docs`

### **4.3 Test Frontend**
Visit `http://localhost:3000` and you should see your React application.

## 🎯 Step 5: Using the System

### **5.1 Basic Workflow**
1. **Frontend**: Go to `http://localhost:3000`
2. **Start Project**: Use the UI to create a new UI mockup project
3. **AutoGen Agents**: The system will use the 6 AI agents to:
   - Understand your requirements
   - Recommend suitable templates
   - Apply modifications based on your feedback
   - Generate comprehensive reports

### **5.2 API Testing**
You can test the AutoGen API directly:

```bash
# Test starting a project
curl -X POST "http://localhost:8001/project/start" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Test Project",
    "user_prompt": "I want a modern landing page for a tech startup"
  }'
```

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **Issue 1: Port Already in Use**
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill the process or use different ports
```

#### **Issue 2: Module Not Found**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### **Issue 3: Claude API Key Error**
```bash
# Check your .env file
cat .env

# Make sure the key is correct and has no extra spaces
CLAUDE_API_KEY=your_actual_key_here
```

#### **Issue 4: MongoDB Connection Error**
```bash
# Start MongoDB (if running locally)
mongod

# Or check your MongoDB URI in .env
MONGODB_URI=mongodb://localhost:27017/ui_mockup_db
```

#### **Issue 5: Frontend Can't Connect to Backend**
Check that:
- Both backend servers are running
- CORS is properly configured
- Frontend is using correct API URLs

## 📱 Quick Start Commands

Here's a quick reference for starting everything:

### **Terminal 1 - Main Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
python main.py
```

### **Terminal 2 - AutoGen API:**
```bash
cd backend
venv\Scripts\activate  # Windows
python autogen_api.py
```

### **Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```

## 🎉 Success Indicators

You'll know everything is working when:

✅ **Main Backend**: `http://localhost:8000/health` returns `{"status": "healthy"}`  
✅ **AutoGen API**: `http://localhost:8001/health` returns agent list  
✅ **Frontend**: `http://localhost:3000` loads your React app  
✅ **API Docs**: Both `/docs` endpoints show interactive documentation  

## 🚀 Next Steps

Once everything is running:

1. **Explore the API Documentation** at both `/docs` endpoints
2. **Test the AutoGen system** with a simple project
3. **Integrate with your frontend** using the provided API endpoints
4. **Customize the agents** for your specific needs
5. **Add your own templates** to the database

## 📞 Getting Help

If you encounter issues:

1. **Check the logs** in each terminal window
2. **Verify all services** are running on correct ports
3. **Test individual components** using the test scripts
4. **Check the API documentation** for endpoint details
5. **Review the conversation history** for debugging

---

**🎉 Congratulations!** You now have a fully functional AI-powered UI mockup generation system running with conversational agents, intelligent template matching, and comprehensive reporting capabilities! 