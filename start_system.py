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
    print("🚀 UI Mockup Generation System Startup")
    print("=" * 50)
    print("Starting all services...")
    print()

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("📋 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if .env file exists
    env_file = Path("backend/.env")
    if not env_file.exists():
        print("❌ .env file not found in backend directory")
        print("Please create backend/.env with your CLAUDE_API_KEY")
        return False
    
    # Check if virtual environment exists
    venv_path = Path("backend/venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        print("Please run: cd backend && python -m venv venv")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def start_backend_server():
    """Start the main backend server"""
    print("🐍 Starting main backend server...")
    
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
            print("✅ Main backend server started on http://localhost:8000")
            return process
        else:
            print("❌ Failed to start main backend server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting main backend server: {e}")
        return None

def start_autogen_server():
    """Start the AutoGen API server"""
    print("🤖 Starting AutoGen API server...")
    
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Activate virtual environment and start server
        if os.name == 'nt':  # Windows
            cmd = ["venv\\Scripts\\python.exe", "autogen_api.py"]
        else:  # Unix/Linux/macOS
            cmd = ["./venv/bin/python", "autogen_api.py"]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ AutoGen API server started on http://localhost:8001")
            return process
        else:
            print("❌ Failed to start AutoGen API server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting AutoGen API server: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    print("⚛️ Starting frontend development server...")
    
    try:
        # Change to frontend directory
        os.chdir("frontend")
        
        # Check if node_modules exists
        if not Path("node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], check=True)
        
        # Start development server
        process = subprocess.Popen(["npm", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Frontend server started on http://localhost:3000")
            return process
        else:
            print("❌ Failed to start frontend server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting frontend server: {e}")
        return None

def open_browsers():
    """Open browsers to the running services"""
    print("🌐 Opening browsers...")
    
    # Wait a bit for all servers to be ready
    time.sleep(2)
    
    try:
        # Open main backend API docs
        webbrowser.open("http://localhost:8000/docs")
        print("✅ Opened main API documentation")
        
        # Open AutoGen API docs
        webbrowser.open("http://localhost:8001/docs")
        print("✅ Opened AutoGen API documentation")
        
        # Open frontend
        webbrowser.open("http://localhost:3000")
        print("✅ Opened frontend application")
        
    except Exception as e:
        print(f"⚠️ Could not open browsers automatically: {e}")

def main():
    """Main startup function"""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return
    
    print()
    
    # Store original directory
    original_dir = os.getcwd()
    
    try:
        # Start all services
        processes = []
        
        # Start main backend server
        backend_process = start_backend_server()
        if backend_process:
            processes.append(("Main Backend", backend_process))
        
        # Start AutoGen API server
        autogen_process = start_autogen_server()
        if autogen_process:
            processes.append(("AutoGen API", autogen_process))
        
        # Start frontend server
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("Frontend", frontend_process))
        
        # Check if all services started successfully
        if len(processes) == 3:
            print("\n🎉 All services started successfully!")
            print("\n📱 Services running:")
            print("   • Main Backend: http://localhost:8000")
            print("   • AutoGen API:  http://localhost:8001")
            print("   • Frontend:     http://localhost:3000")
            
            # Open browsers
            open_browsers()
            
            print("\n🔄 Press Ctrl+C to stop all services")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping all services...")
                
        else:
            print(f"\n❌ Only {len(processes)}/3 services started successfully")
            print("Please check the error messages above")
    
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted")
    
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main() 