#!/usr/bin/env python3
"""
System Startup Script
Starts all services for the UI Mockup Generation System
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("UI Mockup Generation System Startup")
    print("=" * 50)
    print("Starting all services...")
    print()

def check_python_version():
    """Check if Python 3.8+ is installed"""
    try:
        if sys.version_info < (3, 8):
            print("Python 3.8+ required")
            return False
        return True
    except Exception as e:
        print(f"Error checking Python version: {e}")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_path = os.path.join(BACKEND_DIR, ".env")
    if not os.path.exists(env_path):
        print(".env file not found in backend directory")
        return False
    return True

def check_virtual_env():
    """Check if virtual environment exists"""
    venv_path = os.path.join(BACKEND_DIR, "venv_new")
    if not os.path.exists(venv_path):
        print("Virtual environment not found")
        return False
    return True

def check_prerequisites():
    """Check all prerequisites"""
    print("Checking prerequisites...")
    
    if not check_python_version():
        return False
    
    if not check_env_file():
        return False
    
    if not check_virtual_env():
        return False
    
    print("Prerequisites check passed")
    return True

def start_backend_server():
    """Start the main backend server"""
    print("Starting main backend server...")
    
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Activate virtual environment and start server
        if os.name == 'nt':  # Windows
            cmd = ["venv\\Scripts\\python.exe", "main.py"]
        else:  # Unix/Linux/macOS
            cmd = ["./venv/bin/python", "main.py"]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("Main backend server started on http://localhost:8000")
            return True
        else:
            print("Failed to start main backend server")
            print(f"Error: {e}")
            return False
            
    except Exception as e:
        print(f"Error starting main backend server: {e}")
        return False

# AutoGen server function removed - no longer needed

def start_frontend():
    """Start the frontend React development server"""
    try:
        print("Starting frontend server...")
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for the server to start
        time.sleep(5)
        
        if process.poll() is None:
            print("Frontend server started on http://localhost:3000")
            return True
        else:
            print("Failed to start frontend server")
            return False
            
    except Exception as e:
        print(f"Error starting frontend server: {e}")
        return False

def open_browsers():
    """Open browsers to the running services"""
    print("Opening browsers...")
    
    # Wait a bit for all servers to be ready
    time.sleep(2)
    
    try:
        # Open main backend API docs
        webbrowser.open("http://localhost:8000/docs")
        print("Opened main API documentation")
        
        # AutoGen API docs removed - no longer needed
        
        # Open frontend
        webbrowser.open("http://localhost:3000")
        print("Opened frontend application")
        
    except Exception as e:
        print(f"Could not open browsers automatically: {e}")

def main():
    """Main startup function"""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPrerequisites not met. Please fix the issues above.")
        return

    print("\nStarting services...")
    
    # Start backend server
    backend_started = start_backend_server()
    if not backend_started:
        print("Backend failed to start")
        return
    
    # Start frontend server
    frontend_started = start_frontend()
    if not frontend_started:
        print("Frontend failed to start")
        return
    
    # Wait a bit for all services to be ready
    print("\nWaiting for services to be ready...")
    time.sleep(10)
    
    # Open browsers
    open_browsers()
    
    print("\nAll services started successfully!")
    print("\nServices running:")
    print("- Backend API: http://localhost:8000")
    print("- Frontend: http://localhost:3000")
    print("- API Docs: http://localhost:8000/docs")
    
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        # Cleanup would go here if needed
        print("Services stopped")

if __name__ == "__main__":
    main() 