#!/usr/bin/env python3
"""
Test script to debug the template finding issue
"""

import requests
import json

def test_template_finding():
    """Test the template finding issue"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Template Finding Issue ===")
    
    # Test the chat endpoint with a landing page request
    chat_message = {
        "message": "I want to build a landing UI mockup",
        "session_id": None,
        "context": {}
    }
    
    print("Sending chat message...")
    response = requests.post(f"{base_url}/api/chat", json=chat_message)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Chat response received")
        print(f"   Success: {data.get('success')}")
        print(f"   Response: {data.get('response', '')}")
        print(f"   Session ID: {data.get('session_id')}")
        
        # Check if the response contains the error message
        if "I couldn't find any templates" in data.get('response', ''):
            print("❌ Template finding issue confirmed")
            
            # Get debug session info
            session_id = data.get('session_id')
            if session_id:
                print(f"\nGetting debug session info...")
                debug_response = requests.get(f"{base_url}/api/debug/session/{session_id}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    print(f"✅ Debug session info retrieved")
                    
                    # Check conversation history
                    conversation_history = debug_data.get('conversation_history', [])
                    print(f"   Conversation history length: {len(conversation_history)}")
                    
                    # Look for any error messages in the conversation
                    for i, msg in enumerate(conversation_history):
                        if 'error' in msg.get('content', '').lower() or 'failed' in msg.get('content', '').lower():
                            print(f"   Message {i}: {msg.get('content', '')[:200]}...")
                    
                    # Check session state
                    session_state = debug_data.get('session_state', {})
                    print(f"   Current phase: {session_state.get('current_phase', 'unknown')}")
                    print(f"   Plan steps: {len(session_state.get('current_plan', []))}")
                else:
                    print(f"❌ Failed to get debug session info: {debug_response.status_code}")
        else:
            print("✅ Template finding working correctly")
    else:
        print(f"❌ Chat endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_template_finding() 