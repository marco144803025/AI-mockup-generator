#!/usr/bin/env python3
"""
Simplified test for multi-agent system without AutoGen dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_agent_structure():
    """Test the basic agent structure without AutoGen"""
    
    print("🧪 Testing Basic Agent Structure...")
    
    try:
        # Test 1: Import base agent
        print("1. Testing base agent imports...")
        from agents.base_agent import BaseAgent
        print("✅ BaseAgent imported successfully")
        
        # Test 2: Test Claude API connection
        print("2. Testing Claude API connection...")
        if not os.getenv("CLAUDE_API_KEY"):
            print("❌ CLAUDE_API_KEY not found")
            return False
        
        # Create a simple test agent
        test_agent = BaseAgent("TestAgent", "You are a test agent.")
        print("✅ Test agent created successfully")
        
        # Test 3: Test Claude API call
        print("3. Testing Claude API call...")
        response = test_agent.call_claude("Hello, can you respond with 'Test successful'?")
        print(f"✅ Claude API response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_agents():
    """Test individual agents without AutoGen"""
    
    print("\n🧪 Testing Individual Agents...")
    
    try:
        # Test User Proxy Agent
        print("1. Testing User Proxy Agent...")
        from agents.user_proxy_agent import UserProxyAgent
        user_proxy = UserProxyAgent()
        requirements = user_proxy.understand_requirements("I want a modern landing page")
        print(f"✅ User Proxy Agent: {len(requirements)} requirements extracted")
        
        # Test Requirement Understanding Agent
        print("2. Testing Requirement Understanding Agent...")
        from agents.requirement_understanding_agent import RequirementUnderstandingAgent
        req_agent = RequirementUnderstandingAgent()
        specs = req_agent.analyze_requirements("I want a modern landing page")
        print(f"✅ Requirement Understanding Agent: {len(specs)} specifications generated")
        
        # Test UI Recommender Agent
        print("3. Testing UI Recommender Agent...")
        from agents.ui_recommender_agent import UIRecommenderAgent
        recommender = UIRecommenderAgent()
        search_criteria = {"category": "landing", "style": "modern"}
        recommendations = recommender.find_suitable_templates(search_criteria)
        print(f"✅ UI Recommender Agent: {len(recommendations)} recommendations found")
        
        # Test UI Modification Agent
        print("4. Testing UI Modification Agent...")
        from agents.ui_modification_agent import UIModificationAgent
        mod_agent = UIModificationAgent()
        template = {"title": "Test Template", "category": "landing", "tags": ["modern"]}
        mod_request = mod_agent.analyze_modification_request("Make it more colorful", template)
        print(f"✅ UI Modification Agent: {mod_request['modification_type']} modification analyzed")
        
        # Test UI Editing Agent
        print("5. Testing UI Editing Agent...")
        from agents.ui_editing_agent import UIEditingAgent
        edit_agent = UIEditingAgent()
        template_with_content = {
            "title": "Test Template",
            "html_content": "<div class='test'>Hello World</div>",
            "css_content": ".test { color: black; }"
        }
        mod_plan = {"implementation_steps": []}
        modified = edit_agent.apply_modifications(template_with_content, mod_plan)
        print(f"✅ UI Editing Agent: Template modified successfully")
        
        # Test Report Generation Agent
        print("6. Testing Report Generation Agent...")
        from agents.report_generation_agent import ReportGenerationAgent
        report_agent = ReportGenerationAgent()
        project_data = {"project_name": "Test Project"}
        summary = report_agent.generate_summary_report(project_data)
        print(f"✅ Report Generation Agent: Summary generated successfully")
        
        print("\n🎉 All individual agent tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Individual agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints without AutoGen"""
    
    print("\n🧪 Testing API Endpoints...")
    
    try:
        # Test main API
        print("1. Testing main API...")
        from main import app
        print("✅ Main API imported successfully")
        
        # Test AutoGen API (without AutoGen dependency)
        print("2. Testing AutoGen API structure...")
        from autogen_api import autogen_app
        print("✅ AutoGen API imported successfully")
        
        print("\n🎉 API endpoints test passed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("🚀 Starting Simplified Multi-Agent System Tests")
    print("=" * 50)
    
    # Check environment
    if not os.getenv("CLAUDE_API_KEY"):
        print("❌ CLAUDE_API_KEY not found in environment variables")
        print("Please set your Claude API key in the .env file")
        return False
    
    # Run tests
    basic_test_passed = test_basic_agent_structure()
    agent_test_passed = test_individual_agents()
    api_test_passed = test_api_endpoints()
    
    if basic_test_passed and agent_test_passed and api_test_passed:
        print("\n🎉 All simplified tests passed!")
        print("\nStatus Summary:")
        print("✅ Basic agent structure: Working")
        print("✅ Individual agents: Working")
        print("✅ API endpoints: Working")
        print("⚠️  AutoGen integration: Needs dependency fixes")
        print("\nThe multi-agent system core is functional!")
        print("AutoGen integration can be fixed by updating dependencies.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 