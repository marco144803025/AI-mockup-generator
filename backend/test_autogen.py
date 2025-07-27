#!/usr/bin/env python3
"""
Test script for AutoGen Multi-Agent System
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_autogen_system():
    """Test the AutoGen multi-agent system"""
    
    print("🧪 Testing AutoGen Multi-Agent System...")
    
    try:
        # Test 1: Import orchestrator
        print("1. Testing imports...")
        from agents.orchestrator import AutoGenOrchestrator
        print("✅ Orchestrator imported successfully")
        
        # Test 2: Initialize orchestrator
        print("2. Testing orchestrator initialization...")
        orchestrator = AutoGenOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Test 3: Test project start
        print("3. Testing project start...")
        test_project_name = "Test UI Project"
        test_user_prompt = "I want a modern landing page for a tech startup with a clean design"
        
        result = orchestrator.start_project(test_project_name, test_user_prompt)
        print(f"✅ Project started: {result['status']}")
        
        # Test 4: Test project status
        print("4. Testing project status...")
        status = orchestrator.get_project_status()
        print(f"✅ Project status: {status}")
        
        # Test 5: Test conversation history
        print("5. Testing conversation history...")
        history = orchestrator.get_conversation_history()
        print(f"✅ Conversation history: {len(history)} entries")
        
        # Test 6: Test project reset
        print("6. Testing project reset...")
        reset_result = orchestrator.reset_project()
        print(f"✅ Project reset: {reset_result['status']}")
        
        print("\n🎉 All tests passed! AutoGen system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_agents():
    """Test individual agents"""
    
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

def main():
    """Main test function"""
    
    print("🚀 Starting AutoGen Multi-Agent System Tests")
    print("=" * 50)
    
    # Check environment
    if not os.getenv("CLAUDE_API_KEY"):
        print("❌ CLAUDE_API_KEY not found in environment variables")
        print("Please set your Claude API key in the .env file")
        return False
    
    # Run tests
    system_test_passed = test_autogen_system()
    agent_test_passed = test_individual_agents()
    
    if system_test_passed and agent_test_passed:
        print("\n🎉 All tests passed! Your AutoGen system is ready to use.")
        print("\nNext steps:")
        print("1. Start the AutoGen API server: python autogen_api.py")
        print("2. Access the API documentation at: http://localhost:8001/docs")
        print("3. Integrate with your frontend application")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 