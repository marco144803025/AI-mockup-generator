#!/usr/bin/env python3
"""
Test script for the reset endpoint
"""

import requests
import json
import time

def test_reset_endpoint():
    """Test the reset endpoint"""
    session_id = "ac8a5fe7-87df-42b4-b6ea-a61b884b9353"
    url = f"http://localhost:8000/api/ui-codes/session/{session_id}/reset"
    
    print(f"Testing reset endpoint for session: {session_id}")
    print(f"URL: {url}")
    
    try:
        # Test the reset endpoint
        response = requests.post(url, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Reset successful!")
            print(f"Message: {data.get('message', 'No message')}")
            print(f"Screenshot available: {bool(data.get('screenshot_preview', ''))}")
        else:
            print(f"❌ Reset failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error testing reset endpoint: {e}")

def test_session_loading():
    """Test loading the session after reset"""
    session_id = "ac8a5fe7-87df-42b4-b6ea-a61b884b9353"
    url = f"http://localhost:8000/api/ui-codes/session/{session_id}"
    
    print(f"\nTesting session loading for: {session_id}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Session loaded successfully!")
            print(f"Template ID: {data.get('template_id', 'N/A')}")
            print(f"HTML content length: {len(data.get('ui_codes', {}).get('current_codes', {}).get('html_export', ''))}")
            print(f"Screenshot available: {bool(data.get('screenshot_preview', ''))}")
        else:
            print(f"❌ Failed to load session: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error loading session: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("Testing Reset Endpoint")
    print("=" * 60)
    
    # Test reset endpoint
    test_reset_endpoint()
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Test session loading
    test_session_loading()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main() 