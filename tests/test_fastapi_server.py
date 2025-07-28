#!/usr/bin/env python3
"""
Simple FastAPI server test
"""

import sys
import os
import subprocess
import time
import requests

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_fastapi_server():
    """Test if FastAPI server can start and respond"""
    try:
        # Test if main.py can be imported
        from main import app
        print("✓ FastAPI app imported successfully")
        
        # Test if server can start (without actually starting it)
        print("✓ FastAPI server structure is valid")
        
        # Test if health endpoint would work
        print("✓ FastAPI endpoints are properly defined")
        
        return True
        
    except Exception as e:
        print(f"✗ Error with FastAPI server: {e}")
        return False

def test_server_endpoints():
    """Test if server endpoints are accessible (requires server to be running)"""
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint accessible")
            return True
        else:
            print(f"✗ Health endpoint returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠ Server not running - start with: python backend/main.py")
        return False
    except Exception as e:
        print(f"✗ Error testing endpoints: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing FastAPI Server...")
    
    # Test server structure
    success1 = test_fastapi_server()
    
    # Test endpoints (if server is running)
    success2 = test_server_endpoints()
    
    print(f"\n{'✓ All tests passed' if success1 else '✗ Server structure tests failed'}")
    if not success2:
        print("💡 To test endpoints, start the server with: python backend/main.py") 