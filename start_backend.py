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
        print("Virtual environment not found. Please run setup first.")
        return False
    
    print("Starting FastAPI server...")
    
    try:
        # Activate virtual environment and start server
        if os.name == 'nt':  # Windows
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            python_path = os.path.join(venv_path, "bin", "python")
        
        # Start the server
        process = subprocess.Popen([
            python_path, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], cwd=backend_dir)
        
        print(f"Server started with PID: {process.pid}")
        print("Server running on http://localhost:8000")
        print("API documentation available at http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        
        # Wait for the process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if 'process' in locals():
            process.terminate()
        print("Server stopped")
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main()) 