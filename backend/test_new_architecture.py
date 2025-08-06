#!/usr/bin/env python3
"""
Test script for the new Planner-Executor architecture
Tests the BeautifulSoup analysis and multi-step modification process
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ui_editing_agent import UIEditingAgent
import json

def test_beautifulsoup_analysis():
    """Test the new BeautifulSoup-based HTML analysis"""
    print("=== Testing BeautifulSoup HTML Analysis ===")
    
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
    
    analysis = agent._analyze_html_structure_with_beautifulsoup(test_html)
    
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
        print(f"  - Parent context: {element_info.get('parent_context', 'none')}")
    else:
        print(f"✗ Target text '{target_text}' NOT found in analysis")
        print(f"Available texts: {list(analysis['elements_by_text'].keys())}")
    
    print()

def test_planner_agent():
    """Test the Planner Agent's ability to create modification plans"""
    print("=== Testing Planner Agent ===")
    
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
    
    # Analyze HTML
    html_analysis = agent._analyze_html_structure_with_beautifulsoup(template['html_export'])
    
    # Test planning
    user_request = "change the text 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should create a detailed modification plan")
    
    plan_result = agent.planner_agent.create_modification_plan(user_request, template, html_analysis)
    
    print(f"Plan creation success: {plan_result.get('success', False)}")
    if plan_result.get('success', False):
        plan = plan_result.get('plan', {})
        print(f"Intent analysis: {plan.get('intent_analysis', {})}")
        print(f"Target identification: {plan.get('target_identification', {})}")
        print(f"Steps: {len(plan.get('steps', []))}")
        print(f"Requires clarification: {plan.get('requires_clarification', False)}")
        
        # Show the plan details
        if 'steps' in plan:
            for i, step in enumerate(plan['steps']):
                print(f"  Step {i+1}: {step.get('action', 'unknown')} - {step.get('description', 'no description')}")
    else:
        print(f"Error: {plan_result.get('error', 'No error message')}")
    
    print()

def test_executor_agent():
    """Test the Executor Agent's ability to execute modification plans"""
    print("=== Testing Executor Agent ===")
    
    agent = UIEditingAgent()
    
    # Create a simple modification plan
    modification_plan = {
        "intent_analysis": {
            "user_goal": "Change text content",
            "target_element_type": "text",
            "modification_type": "content",
            "specific_change": "text replacement"
        },
        "target_identification": {
            "primary_target": {
                "text_content": "Our Product We Deliver",
                "css_selector": ".logo-text",
                "confidence": 0.95,
                "reasoning": "Exact text match found"
            },
            "alternative_targets": []
        },
        "requires_clarification": False,
        "steps": [
            {
                "step_number": 1,
                "action": "modify_text",
                "target_selector": ".logo-text",
                "new_value": "pioneer the future Starts from now",
                "description": "Change the logo text"
            }
        ],
        "expected_outcome": "Logo text will be updated"
    }
    
    # Create template
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
    
    print("Executing modification plan...")
    execution_result = agent.executor_agent.execute_modification_plan(modification_plan, template)
    
    print(f"Execution success: {execution_result.get('success', False)}")
    if execution_result.get('success', False):
        modified_template = execution_result.get('modified_template', {})
        changes_summary = execution_result.get('changes_summary', [])
        
        print(f"Changes summary: {changes_summary}")
        
        # Check if the modification was actually made
        modified_html = modified_template.get('html_export', '')
        if 'pioneer the future Starts from now' in modified_html:
            print("✓ Text was successfully modified")
        else:
            print("✗ Text was not modified as expected")
            print(f"Modified HTML: {modified_html[:200]}...")
    else:
        print(f"Error: {execution_result.get('error', 'No error message')}")
    
    print()

def test_full_workflow():
    """Test the complete Planner-Executor workflow"""
    print("=== Testing Complete Workflow ===")
    
    agent = UIEditingAgent()
    
    # Create a template
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
    
    # Test the complete workflow
    user_request = "change the text 'Our Product We Deliver' to 'pioneer the future Starts from now'"
    
    print(f"User request: {user_request}")
    print("Expected: Should successfully modify the text through the complete workflow")
    
    result = agent.process_modification_request(user_request, template)
    
    print(f"Workflow success: {result.get('success', False)}")
    if result.get('success', False):
        modified_template = result.get('modified_template', {})
        changes_summary = result.get('changes_summary', [])
        
        print(f"Changes summary: {changes_summary}")
        
        # Check if the modification was actually made
        modified_html = modified_template.get('html_export', '')
        if 'pioneer the future Starts from now' in modified_html:
            print("✓ Text was successfully modified through the complete workflow")
        else:
            print("✗ Text was not modified as expected")
            print(f"Modified HTML: {modified_html[:200]}...")
    else:
        print(f"Error: {result.get('error', 'No error message')}")
        if result.get('clarification_needed', False):
            print("Clarification needed - this is expected behavior for ambiguous requests")
    
    print()

def test_ambiguity_handling():
    """Test the ambiguity handling and clarification system"""
    print("=== Testing Ambiguity Handling ===")
    
    agent = UIEditingAgent()
    
    # Create a template with multiple similar elements
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

if __name__ == "__main__":
    print("Testing New Planner-Executor Architecture")
    print("=" * 60)
    
    test_beautifulsoup_analysis()
    test_planner_agent()
    test_executor_agent()
    test_full_workflow()
    test_ambiguity_handling()
    
    print("All tests completed!") 