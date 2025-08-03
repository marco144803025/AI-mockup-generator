#!/usr/bin/env python3
"""
Test script for logo upload functionality
"""

import requests
import base64
import json
import os

def test_logo_upload_endpoint():
    """Test the logo analysis endpoint"""
    
    # Test data
    test_data = {
        "message": "Apply this logo's design to my UI",
        "logo_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",  # 1x1 pixel PNG
        "logo_filename": "test_logo.png",
        "session_id": "test_session",
        "current_ui_codes": {
            "html_export": "<!DOCTYPE html><html><head><title>Test</title></head><body><div>Test</div></body></html>",
            "globals_css": "body { margin: 0; padding: 0; }",
            "style_css": ".test { color: black; }"
        }
    }
    
    try:
        # Test the endpoint
        response = requests.post(
            "http://localhost:8000/api/ui-editor/analyze-logo",
            json=test_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Logo Analysis: {data.get('logo_analysis')}")
            print(f"UI Modifications: {data.get('ui_modifications')}")
        else:
            print(f"Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the backend is running on port 8000.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Logo Upload Functionality...")
    test_logo_upload_endpoint() 