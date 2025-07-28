#!/usr/bin/env python3
"""
Test script for the Layered Orchestrator
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from layered_orchestrator import LayeredOrchestrator

async def test_layered_orchestrator():
    """Test the layered orchestrator functionality"""
    
    print("🧪 Testing Layered Orchestrator...")
    
    # Initialize orchestrator
    orchestrator = LayeredOrchestrator()
    print(f"✅ Orchestrator initialized with session ID: {orchestrator.session_id}")
    
    # Test 1: Basic message processing
    print("\n📝 Test 1: Basic message processing")
    result = await orchestrator.process_user_message("Hello, I want to create a login page")
    print(f"Response: {result['response']}")
    print(f"Success: {result['success']}")
    print(f"Input Type: {result['metadata']['input_type']}")
    
    # Test 2: Category selection
    print("\n📝 Test 2: Category selection")
    result = await orchestrator.process_user_message("I want to build a landing page")
    print(f"Response: {result['response']}")
    print(f"Selected Category: {orchestrator.session_state['selected_category']}")
    
    # Test 3: Requirements gathering
    print("\n📝 Test 3: Requirements gathering")
    result = await orchestrator.process_user_message("I want it to be modern and responsive")
    print(f"Response: {result['response']}")
    
    # Test 4: Session status
    print("\n📝 Test 4: Session status")
    status = orchestrator.get_session_status()
    print(f"Session State: {status['session_state']['current_phase']}")
    print(f"Memory Stats: {status['memory_stats']['storage_type']}")
    print(f"Validation Summary: {status['validation_summary']['total_validations']} validations")
    
    # Test 5: Reset session
    print("\n📝 Test 5: Reset session")
    reset_result = orchestrator.reset_session()
    print(f"Reset Success: {reset_result['success']}")
    print(f"New Session ID: {reset_result['new_session_id']}")
    
    # Test 6: Error handling
    print("\n📝 Test 6: Error handling")
    result = await orchestrator.process_user_message("")  # Empty message
    print(f"Error Handling: {not result['success']}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_layered_orchestrator()) 