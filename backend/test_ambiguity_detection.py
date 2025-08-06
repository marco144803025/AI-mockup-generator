#!/usr/bin/env python3
"""
Test script for ambiguity detection in the new Planner-Executor architecture
Tests the clarification system when multiple similar elements are found
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ui_editing_agent import UIEditingAgent
import json

def test_multiple_similar_elements():
    """Test ambiguity detection with multiple elements containing similar text"""
    print("=== Testing Ambiguity Detection with Multiple Similar Elements ===")
    
    agent = UIEditingAgent()
    
    # Create a template with multiple elements containing the same text
    template = {
        "name": "Test Template",
        "category": "test",
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
        "style_css": "body { margin: 0; }",
        "globals_css": "* { box-sizing: border-box; }"
    }
    
    # Test with ambiguous request
    user_request = "change 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should detect ambiguity and request clarification")
    
    result = agent.process_modification_request(user_request, template)
    
    print(f"Workflow success: {result.get('success', False)}")
    if not result.get('success', False):
        if result.get('clarification_needed', False):
            print("✓ Ambiguity detected correctly")
            clarification_options = result.get('clarification_options', [])
            print(f"Clarification options: {clarification_options}")
        else:
            print(f"Error: {result.get('error', 'No error message')}")
    else:
        print("Unexpected: Request succeeded when it should have detected ambiguity")
    
    print()

def test_specific_element_targeting():
    """Test that specific targeting works when ambiguity is resolved"""
    print("=== Testing Specific Element Targeting ===")
    
    agent = UIEditingAgent()
    
    # Create a template with multiple elements but target a specific one
    template = {
        "name": "Test Template",
        "category": "test",
        "html_export": """
        <div class="header">
            <h1 class="logo-text">Our Product We Deliver</h1>
            <p class="description">Our Product We Deliver</p>
            <span class="subtitle">Our Product We Deliver</span>
        </div>
        """,
        "style_css": "body { margin: 0; }",
        "globals_css": "* { box-sizing: border-box; }"
    }
    
    # Test with specific targeting
    user_request = "change the logo text 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should successfully target the logo text specifically")
    
    result = agent.process_modification_request(user_request, template)
    
    print(f"Workflow success: {result.get('success', False)}")
    if result.get('success', False):
        modified_template = result.get('modified_template', {})
        changes_summary = result.get('changes_summary', [])
        
        print(f"Changes summary: {changes_summary}")
        
        # Check if the modification was actually made
        modified_html = modified_template.get('html_export', '')
        if 'pioneer the future Starts from now' in modified_html:
            print("✓ Text was successfully modified")
            # Check if only the logo text was changed (not the description or subtitle)
            if modified_html.count('pioneer the future Starts from now') == 1:
                print("✓ Only the target element was modified")
            else:
                print("✗ Multiple elements were modified when only one should have been")
        else:
            print("✗ Text was not modified as expected")
    else:
        print(f"Error: {result.get('error', 'No error message')}")
    
    print()

def test_beautifulsoup_analysis_with_multiple_elements():
    """Test BeautifulSoup analysis with multiple similar elements"""
    print("=== Testing BeautifulSoup Analysis with Multiple Elements ===")
    
    agent = UIEditingAgent()
    
    # HTML with multiple similar elements
    test_html = """
    <div class="header">
        <h1 class="logo-text">Our Product We Deliver</h1>
        <p class="description">Our Product We Deliver</p>
        <span class="subtitle">Our Product We Deliver</span>
        <div class="hero-section">
            <h2 class="hero-title">Our Product We Deliver</h2>
        </div>
    </div>
    """
    
    analysis = agent._analyze_html_structure_with_beautifulsoup(test_html)
    
    print(f"Total elements found: {analysis['debug_info']['total_elements_found']}")
    print(f"Text elements found: {analysis['debug_info']['text_elements_found']}")
    
    # Check how many times our target text appears
    target_text = "Our Product We Deliver"
    matching_elements = []
    
    for text, info in analysis["elements_by_text"].items():
        if target_text in text:
            matching_elements.append({
                "text": text,
                "tag": info['tag'],
                "classes": info['classes'],
                "parent_context": info.get('parent_context', 'none')
            })
    
    print(f"Found {len(matching_elements)} elements containing '{target_text}':")
    for i, element in enumerate(matching_elements):
        print(f"  {i+1}. {element['tag']}.{'.'.join(element['classes'])} - '{element['text']}'")
        print(f"     Parent context: {element['parent_context']}")
    
    print()

if __name__ == "__main__":
    print("Testing Ambiguity Detection in New Architecture")
    print("=" * 60)
    
    test_beautifulsoup_analysis_with_multiple_elements()
    test_multiple_similar_elements()
    test_specific_element_targeting()
    
    print("All ambiguity detection tests completed!") 