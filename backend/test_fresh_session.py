#!/usr/bin/env python3
"""
Test with a fresh session to check if the backend is running the correct code
"""

import requests
import json

def test_fresh_session():
    """Test with a fresh session"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Fresh Session ===")
    
    # First, reset the session
    print("1. Resetting session...")
    reset_response = requests.post(f"{base_url}/api/session/reset")
    if reset_response.status_code == 200:
        print("✅ Session reset successful")
    else:
        print(f"❌ Session reset failed: {reset_response.status_code}")
    
    # Test the chat endpoint with a profile page request
    chat_message = {
        "message": "I want to build a profile UI mockup",
        "session_id": None,
        "context": {}
    }
    
    print("\n2. Sending chat message...")
    response = requests.post(f"{base_url}/api/chat", json=chat_message)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Chat response received")
        print(f"   Success: {data.get('success')}")
        print(f"   Response: {data.get('response', '')}")
        print(f"   Session ID: {data.get('session_id')}")
        
        # Check if the response contains the error message
        if "I couldn't find any templates" in data.get('response', ''):
            print("❌ Template finding issue still exists")
            
            # Get debug session info
            session_id = data.get('session_id')
            if session_id:
                print(f"\n3. Getting debug session info...")
                debug_response = requests.get(f"{base_url}/api/debug/session/{session_id}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    print(f"✅ Debug session info retrieved")
                    
                    # Check conversation history
                    conversation_history = debug_data.get('conversation_history', [])
                    print(f"   Conversation history length: {len(conversation_history)}")
                    
                    # Print the last few messages
                    for i, msg in enumerate(conversation_history[-2:], len(conversation_history)-1):
                        print(f"\n   Message {i+1}:")
                        print(f"     Role: {msg.get('role', 'unknown')}")
                        print(f"     Content: {msg.get('content', '')[:200]}...")
                        print(f"     Timestamp: {msg.get('timestamp', 'unknown')}")
                else:
                    print(f"❌ Failed to get debug session info: {debug_response.status_code}")
        else:
            print("✅ Template finding working correctly")
    else:
        print(f"❌ Chat endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_fresh_session() 