#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from agents.template_recommendation_agent import TemplateRecommendationAgent

def test_requirements_debug():
    try:
        print("=== TESTING REQUIREMENTS DEBUG ===")
        
        # Create template recommendation agent
        agent = TemplateRecommendationAgent()
        
        # Test 1: Test with different requirements structures
        print("\n1. Testing with page_type in requirements:")
        requirements1 = {"page_type": "login"}
        result1 = agent._get_templates_from_database(requirements1)
        print(f"Result: {len(result1)} templates found")
        
        # Test 2: Test with category parameter
        print("\n2. Testing with category parameter:")
        requirements2 = {}
        result2 = agent._get_templates_from_database(requirements2, category="login")
        print(f"Result: {len(result2)} templates found")
        
        # Test 3: Test with fallback category
        print("\n3. Testing with fallback category:")
        requirements3 = {}
        result3 = agent._get_templates_from_database(requirements3)
        print(f"Result: {len(result3)} templates found")
        
        # Test 4: Test the tool utility directly
        print("\n4. Testing tool utility directly:")
        from tools.tool_utility import ToolUtility
        tool_utility = ToolUtility("test")
        
        result4 = tool_utility.call_function("get_templates_by_category", {"category": "login", "limit": 10})
        print(f"Tool result: {result4}")
        
        # Test 5: Test with requirements from orchestrator
        print("\n5. Testing with orchestrator-style requirements:")
        # Simulate what the orchestrator might pass
        requirements5 = {
            "page_type": "login",
            "style_preferences": [],
            "key_features": [],
            "target_audience": "general users"
        }
        result5 = agent._get_templates_from_database(requirements5)
        print(f"Result: {len(result5)} templates found")
        
        # Test 6: Check what the requirements object actually contains
        print("\n6. Checking requirements object structure:")
        print(f"Requirements1 type: {type(requirements1)}")
        print(f"Requirements1 content: {requirements1}")
        print(f"Requirements1.get('page_type'): {requirements1.get('page_type')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_requirements_debug() 