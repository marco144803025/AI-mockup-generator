# UI Mockup Tool Generator

A multi-agent AI system for generating and editing UI mockups with intelligent requirements analysis and template recommendations.

## Quick Start

### 1. Environment Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. External Dependencies

#### MongoDB Database
```bash
# Install MongoDB (if not already installed)
# Windows: Download from https://www.mongodb.com/try/download/community
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb

# Start MongoDB service
# Windows: MongoDB runs as a service
# macOS: brew services start mongodb-community
# Ubuntu: sudo systemctl start mongodb

# Create database and collections
mongosh
use ui_templates
db.createCollection("templates")
db.createCollection("categories")
```

#### Chrome Browser (for screenshots)
```bash
# Install Google Chrome (required for Html2Image screenshots)
# Windows: Download from https://www.google.com/chrome/
# macOS: brew install --cask google-chrome
# Ubuntu: wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
```

#### Redis (optional, for caching)
```bash
# Install Redis (optional dependency)
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
```

### 3. Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Required
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional (with defaults)
MONGODB_URI=mongodb://localhost:27017/
MONGO_DB_NAME=ui_templates
```

### 4. Database Setup

#### Import Sample Templates
```bash
# Navigate to backend directory
cd backend

# Run the upload script to populate database
python upload.py
```

#### Alternative: Manual Database Setup
```bash
# Connect to MongoDB
mongosh

# Use the database
use ui_templates

# Create sample template
db.templates.insertOne({
  "name": "Sample Landing Page",
  "category": "landing",
  "description": "A sample landing page template",
  "tags": ["landing", "modern", "responsive"],
  "html_export": "<div>Sample HTML</div>",
  "style_css": "body { margin: 0; }",
  "global_css": "/* Global styles */"
})
```

### 5. Directory Structure Setup

The project requires these directories to exist:

```bash
# Create required directories
mkdir -p temp_ui_files
mkdir -p temp_previews
mkdir -p temp_logos
mkdir -p reports
mkdir -p temp_previews/default
```

### 6. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 7. Start Frontend

```bash
cd frontend
npm install
npm start
```

### 8. Open Project

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── agents/             # AI agents
│   ├── tools/              # Utility tools
│   ├── utils/              # Helper utilities
│   ├── services/           # Screenshot service
│   └── main.py             # Main API server
├── frontend/                # React frontend
└── evaluation/              # Testing and evaluation
```

## Features

- **Requirements Analysis**: AI-powered requirements gathering
- **Template Recommendations**: Smart template suggestions
- **UI Editing**: Real-time UI modifications
- **Report Generation**: Comprehensive project reports
- **Multi-Agent Workflow**: Coordinated AI agent system
- **Screenshot Generation**: Html2Image-based UI previews

## Dependencies

- **Backend**: FastAPI, Claude API, MongoDB, Redis, Html2Image, Playwright
- **Frontend**: React, Tailwind CSS
- **AI**: Anthropic Claude, Multi-agent orchestration
- **Database**: MongoDB with sample templates
- **Screenshots**: Chrome browser, Html2Image library

## Common Issues & Solutions

### Screenshot Service Fails
- Ensure Chrome browser is installed
- Check if `temp_previews` directory exists
- Verify Html2Image installation: `pip install html2image`

### MongoDB Connection Error
- Ensure MongoDB service is running
- Check connection string in `.env` file
- Verify database and collections exist

### Missing Dependencies
- Run `pip install -r requirements.txt`
- Install system dependencies (Chrome, MongoDB)
- Check Python version compatibility (3.8+)

### Port Conflicts
- Change ports in `uvicorn` and `npm start` commands
- Update frontend API calls to match backend port
