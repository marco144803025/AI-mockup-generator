#!/usr/bin/env python3
"""
Detailed debug test to see what's happening in the conversation history
"""

import requests
import json

def test_detailed_debug():
    """Test with detailed debug output"""
    base_url = "http://localhost:8000"
    
    print("=== Detailed Debug Test ===")
    
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
        
        # Get detailed debug session info
        session_id = data.get('session_id')
        if session_id:
            print(f"\nGetting detailed debug session info...")
            debug_response = requests.get(f"{base_url}/api/debug/session/{session_id}")
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print(f"✅ Debug session info retrieved")
                
                # Check conversation history
                conversation_history = debug_data.get('conversation_history', [])
                print(f"   Conversation history length: {len(conversation_history)}")
                
                # Print each message in the conversation
                for i, msg in enumerate(conversation_history):
                    print(f"\n   Message {i+1}:")
                    print(f"     Role: {msg.get('role', 'unknown')}")
                    print(f"     Content: {msg.get('content', '')[:200]}...")
                    print(f"     Timestamp: {msg.get('timestamp', 'unknown')}")
                
                # Check session state
                session_state = debug_data.get('session_state', {})
                print(f"\n   Session State:")
                print(f"     Current phase: {session_state.get('current_phase', 'unknown')}")
                print(f"     Plan steps: {len(session_state.get('current_plan', []))}")
                
                # Check current plan
                current_plan = session_state.get('current_plan', [])
                if current_plan:
                    print(f"\n   Current Plan:")
                    for i, step in enumerate(current_plan):
                        print(f"     Step {i+1}: {step.get('action', 'unknown')} by {step.get('agent', 'unknown')}")
                        print(f"       Description: {step.get('description', 'no description')}")
                
                # Check project state
                project_state = session_state.get('project_state', {})
                print(f"\n   Project State:")
                for phase, state in project_state.items():
                    print(f"     {phase}: {state}")
            else:
                print(f"❌ Failed to get debug session info: {debug_response.status_code}")
        else:
            print("❌ No session ID received")
    else:
        print(f"❌ Chat endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_detailed_debug() 