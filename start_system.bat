@echo off
echo 🚀 UI Mockup Generation System Startup
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "backend\.env" (
    echo ❌ .env file not found in backend directory
    echo Please create backend\.env with your CLAUDE_API_KEY
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo ❌ Virtual environment not found
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Start main backend server
echo 🐍 Starting main backend server...
start "Main Backend Server" cmd /k "cd backend && venv\Scripts\activate && python main.py"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM AutoGen API server removed - no longer needed

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend server
echo ⚛️ Starting frontend development server...
start "Frontend Server" cmd /k "cd frontend && npm start"

REM Wait a moment
timeout /t 5 /nobreak >nul

echo.
echo 🎉 All services started successfully!
echo.
echo 📱 Services running:
echo    • Main Backend: http://localhost:8000
REM AutoGen API removed - no longer needed
echo    • Frontend:     http://localhost:3000
echo.

REM Open browsers
echo 🌐 Opening browsers...
start http://localhost:8000/docs
start http://localhost:8001/docs
start http://localhost:3000

echo.
echo ✅ Browsers opened successfully!
echo.
echo 🔄 Close this window when you're done
echo.
pause 