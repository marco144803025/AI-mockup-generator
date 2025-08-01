#!/usr/bin/env python3
"""
Simple script to start the backend server
"""

import os
import sys
import subprocess
import time

def main():
    print(" Starting UI Mockup Generator Backend...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if not os.path.exists(backend_dir):
        print(f" Backend directory not found: {backend_dir}")
        return 1
    
    os.chdir(backend_dir)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check if virtual environment exists
    venv_path = os.path.join(backend_dir, "venv_new")
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found. Please run setup first.")
        return 1
    
    # Activate virtual environment and start server
    try:
        print("🔧 Starting FastAPI server...")
        
        # Use uvicorn to start the server
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ]
        
        print(f"📡 Server will be available at: http://localhost:8000")
        print(f"🏥 Health check: http://localhost:8000/api/health")
        print(f"📋 Categories: http://localhost:8000/api/templates/categories")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 