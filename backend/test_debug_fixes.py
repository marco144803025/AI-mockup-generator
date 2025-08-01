#!/usr/bin/env python3
"""
Test script to verify debug fixes work properly
"""

import asyncio
import requests
import json
from datetime import datetime

def test_debug_endpoints():
    """Test debug endpoints"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Debug Endpoints ===")
    
    # Test 1: Basic debug test endpoint
    print("\n1. Testing basic debug endpoint...")
    try:
        response = requests.get(f"{base_url}/api/debug/test")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug endpoint working: {data.get('status')}")
            print(f"   Orchestrator session ID: {data.get('orchestrator_session_id')}")
            print(f"   Orchestrator initialized: {data.get('orchestrator_initialized')}")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Debug endpoint error: {e}")
    
    # Test 2: Template categories
    print("\n2. Testing template categories...")
    try:
        response = requests.get(f"{base_url}/api/templates/categories")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Categories endpoint working: {data.get('categories')}")
            print(f"   Count: {data.get('count')}")
        else:
            print(f"❌ Categories endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Categories endpoint error: {e}")
    
    # Test 3: Templates for landing category
    print("\n3. Testing templates for landing category...")
    try:
        response = requests.get(f"{base_url}/api/templates?category=landing&limit=3")
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            print(f"✅ Templates endpoint working: Found {len(templates)} templates")
            for i, template in enumerate(templates[:2]):
                print(f"   Template {i+1}: {template.get('name', 'Unknown')}")
        else:
            print(f"❌ Templates endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Templates endpoint error: {e}")
    
    # Test 4: Test agent pipeline
    print("\n4. Testing agent pipeline...")
    try:
        test_message = {
            "message": "I want to build a landing UI mockup",
            "session_id": None,
            "context": {}
        }
        response = requests.post(f"{base_url}/api/debug/test-agent", json=test_message)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent pipeline test: {data.get('success')}")
            if data.get('success'):
                debug_info = data.get('debug_info', {})
                print(f"   Messages processed: {debug_info.get('conversation_history_length', 0)}")
                print(f"   Current phase: {debug_info.get('current_phase', 'unknown')}")
        else:
            print(f"❌ Agent pipeline test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent pipeline test error: {e}")

def test_chat_endpoint():
    """Test the main chat endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n=== Testing Chat Endpoint ===")
    
    try:
        chat_message = {
            "message": "I want to build a landing UI mockup",
            "session_id": None,
            "context": {}
        }
        
        print("Sending chat message...")
        response = requests.post(f"{base_url}/api/chat", json=chat_message)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat endpoint working: {data.get('success')}")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Session ID: {data.get('session_id')}")
            
            # Test debug session info
            session_id = data.get('session_id')
            if session_id:
                print(f"\nTesting debug session info for session: {session_id}")
                debug_response = requests.get(f"{base_url}/api/debug/session/{session_id}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    print(f"✅ Debug session info working")
                    debug_info = debug_data.get('debug_info', {})
                    print(f"   Total messages: {debug_info.get('total_messages', 0)}")
                    print(f"   Current phase: {debug_info.get('current_phase', 'unknown')}")
                else:
                    print(f"❌ Debug session info failed: {debug_response.status_code}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")

if __name__ == "__main__":
    print(f"Starting debug tests at {datetime.now()}")
    
    # Test debug endpoints
    test_debug_endpoints()
    
    # Test chat endpoint
    test_chat_endpoint()
    
    print(f"\nDebug tests completed at {datetime.now()}") 