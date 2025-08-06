#!/usr/bin/env python3
"""
Test script to verify enhanced prompt engineering prevents invalid CSS selectors
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.ui_editing_agent import UIEditingAgent

def test_enhanced_prompt_engineering():
    """Test that enhanced prompt engineering prevents invalid CSS selectors"""
    print("🧪 Testing Enhanced Prompt Engineering")
    print("=" * 50)
    
    # Create UI editing agent
    editing_agent = UIEditingAgent()
    
    # Test HTML with multiple elements that could be targeted
    test_html = """
    <div class="header">
        <nav class="navigation">
            <a href="#" class="nav-link">INFO</a>
            <a href="#" class="nav-link">WORK</a>
            <a href="#" class="nav-link">PHOTOS</a>
            <a href="#" class="nav-link text-wrapper-10">Connect</a>
            <a href="#" class="nav-link">ABOUT</a>
        </nav>
        <div class="hero-section">
            <h1 class="hero-title">Welcome to Our Site</h1>
            <p class="hero-description">This is a test description</p>
        </div>
    </div>
    """
    
    # Create a mock template
    mock_template = {
        "name": "Test Template",
        "category": "test",
        "html_export": test_html,
        "style_css": """
        .nav-link { color: black; }
        .text-wrapper-10 { font-weight: bold; }
        .hero-title { font-size: 2em; }
        """,
        "globals_css": "body { font-family: Arial, sans-serif; }"
    }
    
    # Test cases that previously generated invalid selectors
    test_cases = [
        {
            "request": "change the connect button at the top navigation bar to light red",
            "expected_valid": True,
            "description": "Should use .text-wrapper-10 or .nav-link.text-wrapper-10"
        },
        {
            "request": "change the hero title color to blue",
            "expected_valid": True,
            "description": "Should use .hero-title"
        },
        {
            "request": "change the description text to green",
            "expected_valid": True,
            "description": "Should use .hero-description"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print("-" * 40)
        print(f"Request: {test_case['request']}")
        
        try:
            result = editing_agent.process_modification_request(
                test_case['request'],
                mock_template
            )
            
            print(f"✅ Success: {result.get('success', False)}")
            
            if result.get('success'):
                changes = result.get('changes_summary', [])
                print(f"✅ Changes: {changes}")
                
                # Check if any invalid selectors were generated
                has_invalid_selectors = False
                for change in changes:
                    if any(invalid in change for invalid in [':contains(', ':has(', ':text(', ':first', ':last', ':eq(']):
                        has_invalid_selectors = True
                        print(f"❌ INVALID SELECTOR DETECTED: {change}")
                
                if not has_invalid_selectors:
                    print("✅ All selectors are valid CSS")
                else:
                    print("❌ Invalid selectors were generated despite enhanced prompts")
                    
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Error: {error}")
                
                # Check if the error is about invalid selectors (which is good)
                if 'jQuery' in error or 'invalid' in error.lower():
                    print("✅ Correctly caught invalid selector - this is good!")
                else:
                    print("❌ Unexpected error type")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n🎉 Enhanced prompt engineering testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_enhanced_prompt_engineering() 