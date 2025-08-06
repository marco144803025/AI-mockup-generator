#!/usr/bin/env python3
"""
Test script for the improved UI Editing Agent
Tests the enhanced HTML analysis and better error handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ui_editing_agent import UIEditingAgent
import json

def test_html_analysis_improvement():
    """Test the improved HTML structure analysis"""
    print("=== Testing Improved HTML Analysis ===")
    
    agent = UIEditingAgent()
    
    # Sample HTML with various text elements
    test_html = """
    <div class="header">
        <h1 class="logo-text">Our Product We Deliver</h1>
        <nav class="navigation">
            <a href="#" class="nav-link">Home</a>
            <a href="#" class="nav-link">About</a>
        </nav>
    </div>
    <div class="hero-section">
        <h2 class="hero-title">Welcome to Our Platform</h2>
        <p class="hero-description">We provide amazing solutions</p>
        <input type="text" placeholder="Enter your email" class="email-input" value="test@example.com">
        <button class="cta-button" title="Click to subscribe">Subscribe</button>
    </div>
    """
    
    analysis = agent._analyze_html_structure(test_html)
    
    print(f"Total elements found: {analysis['debug_info']['total_elements_found']}")
    print(f"Text elements found: {analysis['debug_info']['text_elements_found']}")
    print(f"Sample texts: {analysis['debug_info']['sample_texts'][:5]}")
    
    # Check if our target text is found
    target_text = "Our Product We Deliver"
    if target_text in analysis["elements_by_text"]:
        print(f"✓ Target text '{target_text}' found in analysis")
        element_info = analysis["elements_by_text"][target_text]
        print(f"  - Tag: {element_info['tag']}")
        print(f"  - Classes: {element_info['classes']}")
        print(f"  - ID: {element_info.get('id', 'none')}")
    else:
        print(f"✗ Target text '{target_text}' NOT found in analysis")
        print(f"Available texts: {list(analysis['elements_by_text'].keys())}")
    
    print()

def test_text_not_found_scenario():
    """Test the scenario where target text is not found"""
    print("=== Testing Text Not Found Scenario ===")
    
    agent = UIEditingAgent()
    
    # Create a template with different text than what we're looking for
    template = {
        "name": "Test Template",
        "category": "test",
        "html_export": """
        <div class="header">
            <h1 class="logo-text">Different Text Here</h1>
            <p class="description">Some other content</p>
        </div>
        """,
        "style_css": "body { margin: 0; }",
        "globals_css": "* { box-sizing: border-box; }"
    }
    
    # Try to modify text that doesn't exist
    user_request = "change the hero section quote from 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should return error indicating text not found")
    
    result = agent.process_modification_request(user_request, template)
    
    print(f"Result success: {result.get('success', False)}")
    if not result.get('success', False):
        print(f"Error: {result.get('error', 'No error message')}")
        if 'changes_summary' in result:
            print(f"Changes summary: {result['changes_summary']}")
        if 'suggestion' in result:
            print(f"Suggestion: {result['suggestion']}")
    else:
        print("Unexpected: Request succeeded when it should have failed")
    
    print()

def test_placeholder_detection():
    """Test that placeholder text is properly detected and rejected"""
    print("=== Testing Placeholder Detection ===")
    
    agent = UIEditingAgent()
    
    # Simulate a response with placeholder text (this shouldn't happen with our improved prompt)
    placeholder_response = """
    {
      "html_export": "/* Same as original HTML, no changes detected */",
      "globals_css": "/* Same as original global CSS, no changes detected */", 
      "style_css": "/* Same as original style CSS, no changes detected */",
      "changes_summary": [
        "No direct match found for 'Our Product We Deliver'"
      ]
    }
    """
    
    template = {
        "name": "Test Template",
        "category": "test",
        "html_export": "<div>Test content</div>",
        "style_css": "body { margin: 0; }",
        "globals_css": "* { box-sizing: border-box; }"
    }
    
    result = agent._parse_final_output_from_response(placeholder_response, template)
    
    print(f"Result success: {result.get('success', False)}")
    if not result.get('success', False):
        print(f"Error: {result.get('error', 'No error message')}")
        if 'suggestion' in result:
            print(f"Suggestion: {result['suggestion']}")
    else:
        print("Unexpected: Placeholder text was accepted")
    
    print()

def test_actual_text_modification():
    """Test actual text modification when text is found"""
    print("=== Testing Actual Text Modification ===")
    
    agent = UIEditingAgent()
    
    # Create a template with the text we want to modify
    template = {
        "name": "Test Template",
        "category": "test",
        "html_export": """
        <div class="header">
            <h1 class="logo-text">Our Product We Deliver</h1>
            <p class="description">Some other content</p>
        </div>
        """,
        "style_css": "body { margin: 0; }",
        "globals_css": "* { box-sizing: border-box; }"
    }
    
    # Try to modify text that exists
    user_request = "change the text 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should successfully modify the text")
    
    result = agent.process_modification_request(user_request, template)
    
    print(f"Result success: {result.get('success', False)}")
    if result.get('success', False):
        modified_template = result.get('modified_template', {})
        modified_html = modified_template.get('html_export', '')
        changes_summary = result.get('changes_summary', [])
        
        print(f"Changes summary: {changes_summary}")
        
        # Check if the modification was actually made
        if 'pioneer the future Starts from now' in modified_html:
            print("✓ Text was successfully modified")
        else:
            print("✗ Text was not modified as expected")
            print(f"Modified HTML: {modified_html[:200]}...")
    else:
        print(f"Error: {result.get('error', 'No error message')}")
    
    print()

if __name__ == "__main__":
    print("Testing Improved UI Editing Agent")
    print("=" * 50)
    
    test_html_analysis_improvement()
    test_text_not_found_scenario()
    test_placeholder_detection()
    test_actual_text_modification()
    
    print("All tests completed!") 