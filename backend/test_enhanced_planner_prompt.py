#!/usr/bin/env python3
"""
Test script for the enhanced planner prompt with comprehensive HTML analysis
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.ui_editing_agent import UIEditingAgent

async def test_enhanced_planner_prompt():
    """Test the enhanced planner prompt with comprehensive HTML analysis"""
    print("🧪 Testing Enhanced Planner Prompt")
    print("=" * 50)
    
    # Create UI editing agent
    editing_agent = UIEditingAgent()
    
    # Create a test HTML with multiple similar elements
    test_html = """
    <div class="header">
        <h1 class="logo-text">Our Product We Deliver</h1>
        <p class="description">Our Product We Deliver</p>
        <span class="subtitle">Our Product We Deliver</span>
        <div class="hero-section">
            <h2 class="hero-title">Our Product We Deliver</h2>
        </div>
    </div>
    <div class="content">
        <p class="text-wrapper-10">Some other content</p>
        <button class="btn-primary">Login</button>
        <button class="btn-secondary">Sign Up</button>
    </div>
    """
    
    # Create a mock template
    mock_template = {
        "name": "Test Template",
        "category": "test",
        "html_export": test_html,
        "style_css": """
        .logo-text { color: black; }
        .description { color: gray; }
        .subtitle { color: darkgray; }
        .hero-title { color: navy; }
        .btn-primary { background-color: blue; }
        .btn-secondary { background-color: gray; }
        """,
        "globals_css": "body { font-family: Arial, sans-serif; }"
    }
    
    # Test 1: Analyze HTML structure
    print("\n📝 Test 1: HTML Structure Analysis")
    print("-" * 40)
    
    html_analysis = editing_agent._analyze_html_structure_with_beautifulsoup(test_html)
    
    print(f"✅ Total elements found: {html_analysis.get('debug_info', {}).get('total_elements_found', 0)}")
    print(f"✅ Text elements found: {html_analysis.get('debug_info', {}).get('text_elements_found', 0)}")
    print(f"✅ Elements by text: {len(html_analysis.get('elements_by_text', {}))}")
    print(f"✅ Elements by class: {len(html_analysis.get('elements_by_class', {}))}")
    print(f"✅ Header elements: {len(html_analysis.get('header_elements', []))}")
    print(f"✅ Navigation elements: {len(html_analysis.get('navigation_elements', []))}")
    
    # Show some sample elements
    print("\n📋 Sample Text Elements:")
    for text, info in list(html_analysis.get('elements_by_text', {}).items())[:5]:
        print(f"  - '{text}' (tag: {info.get('tag')}, classes: {info.get('classes')})")
    
    # Test 2: Build enhanced planning prompt
    print("\n📝 Test 2: Enhanced Planning Prompt")
    print("-" * 40)
    
    user_request = "change the color of 'Our Product We Deliver' to green"
    
    prompt = editing_agent.planner_agent._build_planning_prompt(
        user_request, 
        mock_template, 
        html_analysis
    )
    
    print(f"✅ Prompt length: {len(prompt)} characters")
    print(f"✅ Contains 'ALL TEXT ELEMENTS': {'ALL TEXT ELEMENTS' in prompt}")
    print(f"✅ Contains 'ELEMENTS BY CSS CLASS': {'ELEMENTS BY CSS CLASS' in prompt}")
    print(f"✅ Contains 'HEADER ELEMENTS': {'HEADER ELEMENTS' in prompt}")
    print(f"✅ Contains 'Our Product We Deliver': {'Our Product We Deliver' in prompt}")
    print(f"✅ Contains '.logo-text': {'.logo-text' in prompt}")
    print(f"✅ Contains '.hero-title': {'.hero-title' in prompt}")
    
    # Show a snippet of the prompt
    print("\n📋 Prompt Snippet (first 1000 chars):")
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    
    # Test 3: Test planner agent with enhanced prompt
    print("\n📝 Test 3: Planner Agent with Enhanced Prompt")
    print("-" * 40)
    
    try:
        result = editing_agent.planner_agent.create_modification_plan(
            user_request, 
            mock_template, 
            html_analysis
        )
        
        if result.get("success", False):
            plan = result.get("plan", {})
            print("✅ Plan created successfully!")
            print(f"✅ Intent analysis: {plan.get('intent_analysis', {}).get('user_goal', 'N/A')}")
            print(f"✅ Primary target: {plan.get('target_identification', {}).get('primary_target', {}).get('text_content', 'N/A')}")
            print(f"✅ CSS selector: {plan.get('target_identification', {}).get('primary_target', {}).get('css_selector', 'N/A')}")
            print(f"✅ Confidence: {plan.get('target_identification', {}).get('primary_target', {}).get('confidence', 'N/A')}")
            print(f"✅ Requires clarification: {plan.get('requires_clarification', False)}")
            print(f"✅ Steps count: {len(plan.get('steps', []))}")
            
            if plan.get('requires_clarification'):
                print(f"✅ Clarification options: {len(plan.get('clarification_options', []))}")
                for i, option in enumerate(plan.get('clarification_options', [])[:3]):
                    print(f"    {i+1}. {option.get('text_content', 'N/A')} ({option.get('css_selector', 'N/A')})")
        else:
            print(f"❌ Failed to create plan: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error creating plan: {e}")
    
    # Test 4: Test with ambiguous request
    print("\n📝 Test 4: Ambiguous Request Test")
    print("-" * 40)
    
    ambiguous_request = "change the color of 'Our Product We Deliver' to green"
    
    try:
        result = editing_agent.planner_agent.create_modification_plan(
            ambiguous_request, 
            mock_template, 
            html_analysis
        )
        
        if result.get("success", False):
            plan = result.get("plan", {})
            print("✅ Ambiguous plan created!")
            print(f"✅ Requires clarification: {plan.get('requires_clarification', False)}")
            
            if plan.get('requires_clarification'):
                print("✅ Correctly detected ambiguity!")
                clarification_options = plan.get('clarification_options', [])
                print(f"✅ Found {len(clarification_options)} clarification options:")
                
                for i, option in enumerate(clarification_options):
                    text = option.get('text_content', 'N/A')
                    selector = option.get('css_selector', 'N/A')
                    description = option.get('description', 'N/A')
                    print(f"    {i+1}. '{text}' ({selector}) - {description}")
            else:
                print("⚠️  Did not detect ambiguity (this might be correct if one target is clearly best)")
        else:
            print(f"❌ Failed to create ambiguous plan: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error creating ambiguous plan: {e}")
    
    print("\n🎉 Enhanced planner prompt testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_enhanced_planner_prompt()) 