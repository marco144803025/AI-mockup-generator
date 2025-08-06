#!/usr/bin/env python3
"""
Test script for the clarification loop logic in the orchestrator
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.lean_flow_orchestrator import LeanFlowOrchestrator
from agents.ui_editing_agent import UIEditingAgent
from utils.file_manager import UICodeFileManager

async def test_clarification_loop():
    """Test the clarification loop logic"""
    print("🧪 Testing Clarification Loop Logic")
    print("=" * 50)
    
    # Create a test session
    session_id = "test_clarification_session"
    orchestrator = LeanFlowOrchestrator(session_id)
    
    # Set up a mock template for testing
    mock_template = {
        "template_id": "test_template_123",
        "name": "Test Template",
        "category": "test",
        "description": "A test template for clarification testing"
    }
    
    # Set up the session state
    orchestrator.session_state["selected_template"] = mock_template
    orchestrator.session_state["current_phase"] = "editing"
    
    # Create a mock UI state with multiple similar elements
    mock_ui_state = {
        "html_export": """
        <div class="header">
            <h1 class="logo-text">Our Product We Deliver</h1>
            <p class="description">Our Product We Deliver</p>
            <span class="subtitle">Our Product We Deliver</span>
            <div class="hero-section">
                <h2 class="hero-title">Our Product We Deliver</h2>
            </div>
        </div>
        """,
        "style_css": """
        .logo-text { color: black; }
        .description { color: gray; }
        .subtitle { color: darkgray; }
        .hero-title { color: navy; }
        """,
        "globals_css": "body { font-family: Arial, sans-serif; }"
    }
    
    # Mock the file manager to return our test UI state
    file_manager = UICodeFileManager()
    
    # Test 1: Simulate a modification request that needs clarification
    print("\n📝 Test 1: Modification request needing clarification")
    print("-" * 40)
    
    # Mock the UI editing agent to return clarification needed
    original_process_method = orchestrator.editing_agent.process_modification_request
    
    def mock_process_modification_request(user_feedback, current_template):
        return {
            "success": False,
            "clarification_needed": True,
            "clarification_options": [
                {
                    "text_content": "Our Product We Deliver",
                    "css_selector": ".logo-text",
                    "description": "Main logo text in header"
                },
                {
                    "text_content": "Our Product We Deliver", 
                    "css_selector": ".description",
                    "description": "Description text below logo"
                },
                {
                    "text_content": "Our Product We Deliver",
                    "css_selector": ".subtitle", 
                    "description": "Subtitle text"
                },
                {
                    "text_content": "Our Product We Deliver",
                    "css_selector": ".hero-title",
                    "description": "Hero section title"
                }
            ],
            "error": "Multiple elements found with text 'Our Product We Deliver'",
            "user_feedback": user_feedback,
            "original_template": current_template
        }
    
    orchestrator.editing_agent.process_modification_request = mock_process_modification_request
    
    # Test the modification request
    result = await orchestrator._handle_editing_modification_request(
        "change the color of 'Our Product We Deliver' to green",
        mock_template
    )
    
    print(f"✅ Result success: {result.get('success')}")
    print(f"✅ Intent: {result.get('intent')}")
    print(f"✅ Pending clarification: {result.get('pending_clarification')}")
    print(f"✅ Response: {result.get('response', '')[:200]}...")
    
    # Test 2: Simulate user response to clarification
    print("\n📝 Test 2: User response to clarification")
    print("-" * 40)
    
    # Mock the UI editing agent to return success after clarification
    def mock_process_modification_request_with_choice(user_feedback, current_template):
        if "targeting:" in user_feedback:
            return {
                "success": True,
                "modified_template": {
                    **current_template,
                    "style_css": current_template["style_css"] + "\n.logo-text { color: green; }"
                },
                "changes_summary": ["Changed logo text color to green"],
                "clarification_needed": False
            }
        else:
            return mock_process_modification_request(user_feedback, current_template)
    
    orchestrator.editing_agent.process_modification_request = mock_process_modification_request_with_choice
    
    # Test user response to clarification
    result = await orchestrator._handle_editing_clarification_user_response(
        "1",  # User chooses option 1
        mock_template
    )
    
    print(f"✅ Result success: {result.get('success')}")
    print(f"✅ Intent: {result.get('intent')}")
    print(f"✅ Response: {result.get('response', '')[:200]}...")
    
    # Test 3: Simulate invalid user choice
    print("\n📝 Test 3: Invalid user choice")
    print("-" * 40)
    
    # Reset the pending clarification
    orchestrator.session_state["pending_clarification"] = {
        "original_request": "change the color of 'Our Product We Deliver' to green",
        "clarification_options": [
            {
                "text_content": "Our Product We Deliver",
                "css_selector": ".logo-text",
                "description": "Main logo text in header"
            },
            {
                "text_content": "Our Product We Deliver", 
                "css_selector": ".description",
                "description": "Description text below logo"
            }
        ],
        "original_template": mock_ui_state,
        "timestamp": "2025-01-27T12:00:00Z"
    }
    
    # Test invalid choice
    result = await orchestrator._handle_editing_clarification_user_response(
        "invalid choice",  # Invalid choice
        mock_template
    )
    
    print(f"✅ Result success: {result.get('success')}")
    print(f"✅ Intent: {result.get('intent')}")
    print(f"✅ Pending clarification: {result.get('pending_clarification')}")
    print(f"✅ Response: {result.get('response', '')[:200]}...")
    
    # Test 4: Test the parsing of user choices
    print("\n📝 Test 4: User choice parsing")
    print("-" * 40)
    
    test_cases = [
        ("1", "Our Product We Deliver"),
        ("option 2", "Our Product We Deliver"), 
        ("Our Product We Deliver", "Our Product We Deliver"),
        (".logo-text", "Our Product We Deliver"),
        ("Main logo text in header", "Our Product We Deliver"),
        ("invalid", None)
    ]
    
    clarification_options = [
        {
            "text_content": "Our Product We Deliver",
            "css_selector": ".logo-text",
            "description": "Main logo text in header"
        },
        {
            "text_content": "Our Product We Deliver", 
            "css_selector": ".description",
            "description": "Description text below logo"
        }
    ]
    
    for user_input, expected in test_cases:
        result = orchestrator._parse_user_clarification_choice(user_input, clarification_options)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: '{user_input}' -> Expected: '{expected}', Got: '{result}'")
    
    # Restore original method
    orchestrator.editing_agent.process_modification_request = original_process_method
    
    print("\n🎉 Clarification loop testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_clarification_loop()) 