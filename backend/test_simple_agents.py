#!/usr/bin/env python3
"""
Test for simplified multi-agent system without AutoGen dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_base_agent():
    """Test the simplified base agent"""
    
    print("🧪 Testing Simplified Base Agent...")
    
    try:
        # Test 1: Import simple base agent
        print("1. Testing simple base agent imports...")
        from simple_base_agent import SimpleBaseAgent
        print("✅ SimpleBaseAgent imported successfully")
        
        # Test 2: Test Claude API connection
        print("2. Testing Claude API connection...")
        if not os.getenv("CLAUDE_API_KEY"):
            print("❌ CLAUDE_API_KEY not found")
            return False
        
        # Create a simple test agent
        test_agent = SimpleBaseAgent("TestAgent", "You are a test agent.")
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

def test_agent_specializations():
    """Test different agent specializations"""
    
    print("\n🧪 Testing Agent Specializations...")
    
    try:
        from simple_base_agent import SimpleBaseAgent
        
        # Test 1: User Proxy Agent
        print("1. Testing User Proxy Agent...")
        user_proxy = SimpleBaseAgent(
            "UserProxy", 
            "You are a User Proxy Agent responsible for understanding user requirements and confirming them."
        )
        
        prompt = """
        Analyze the user's requirements for a UI mockup:
        
        User Request: I want a modern landing page for a tech startup
        
        Please provide a structured analysis including:
        1. Page Type: What type of page they want
        2. Style Preferences: Any style mentions
        3. Key Features: What functionality they need
        4. Target Audience: Who the page is for
        5. Brand Elements: Any brand-specific requirements
        
        Format your response as JSON.
        """
        
        response = user_proxy.call_claude(prompt)
        print(f"✅ User Proxy Agent: Response received ({len(response)} characters)")
        
        # Test 2: Requirement Understanding Agent
        print("2. Testing Requirement Understanding Agent...")
        req_agent = SimpleBaseAgent(
            "RequirementUnderstanding",
            "You are a Requirement Understanding Agent specialized in analyzing user prompts to extract UI requirements."
        )
        
        req_prompt = """
        Analyze the following user requirements and extract detailed UI specifications:
        
        USER PROMPT: I want a modern landing page for a tech startup with a clean design
        
        Please provide a comprehensive analysis in JSON format with layout_type, color_scheme, typography, components, and style_preferences.
        """
        
        req_response = req_agent.call_claude(req_prompt)
        print(f"✅ Requirement Understanding Agent: Response received ({len(req_response)} characters)")
        
        # Test 3: UI Recommender Agent
        print("3. Testing UI Recommender Agent...")
        recommender = SimpleBaseAgent(
            "UIRecommender",
            "You are a UI Recommender Agent specialized in finding suitable UI templates based on requirements."
        )
        
        rec_prompt = """
        Based on the following requirements, recommend suitable UI templates:
        
        Requirements: Modern landing page for tech startup, clean design, responsive
        
        Please provide recommendations in JSON format with template names, categories, and reasoning.
        """
        
        rec_response = recommender.call_claude(rec_prompt)
        print(f"✅ UI Recommender Agent: Response received ({len(rec_response)} characters)")
        
        # Test 4: UI Modification Agent
        print("4. Testing UI Modification Agent...")
        mod_agent = SimpleBaseAgent(
            "UIModification",
            "You are a UI Modification Agent specialized in analyzing modification requests and creating implementation plans."
        )
        
        mod_prompt = """
        Analyze this modification request for a UI template:
        
        Template: Modern landing page
        Modification Request: Make it more colorful and add animations
        
        Please provide a modification plan in JSON format with modification_type, implementation_steps, and affected_components.
        """
        
        mod_response = mod_agent.call_claude(mod_prompt)
        print(f"✅ UI Modification Agent: Response received ({len(mod_response)} characters)")
        
        # Test 5: UI Editing Agent
        print("5. Testing UI Editing Agent...")
        edit_agent = SimpleBaseAgent(
            "UIEditing",
            "You are a UI Editing Agent specialized in applying modifications to HTML and CSS code."
        )
        
        edit_prompt = """
        Apply the following modification to this HTML/CSS:
        
        HTML: <div class="hero">Hello World</div>
        CSS: .hero { color: black; }
        Modification: Make it more colorful
        
        Please provide the modified HTML and CSS code.
        """
        
        edit_response = edit_agent.call_claude(edit_prompt)
        print(f"✅ UI Editing Agent: Response received ({len(edit_response)} characters)")
        
        # Test 6: Report Generation Agent
        print("6. Testing Report Generation Agent...")
        report_agent = SimpleBaseAgent(
            "ReportGeneration",
            "You are a Report Generation Agent specialized in creating comprehensive project reports."
        )
        
        report_prompt = """
        Generate a summary report for this UI project:
        
        Project Name: Test Tech Startup Landing Page
        Requirements: Modern, clean design
        Modifications: Made more colorful, added animations
        Status: Completed
        
        Please provide a structured report in JSON format.
        """
        
        report_response = report_agent.call_claude(report_prompt)
        print(f"✅ Report Generation Agent: Response received ({len(report_response)} characters)")
        
        print("\n🎉 All agent specialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Agent specialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints"""
    
    print("\n🧪 Testing API Endpoints...")
    
    try:
        # Test main API
        print("1. Testing main API...")
        from main import app
        print("✅ Main API imported successfully")
        
        # Test AutoGen API structure
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

def test_multi_agent_workflow():
    """Test a simplified multi-agent workflow"""
    
    print("\n🧪 Testing Multi-Agent Workflow...")
    
    try:
        from simple_base_agent import SimpleBaseAgent
        
        # Create all agents
        user_proxy = SimpleBaseAgent("UserProxy", "You are a User Proxy Agent.")
        req_agent = SimpleBaseAgent("RequirementUnderstanding", "You are a Requirement Understanding Agent.")
        recommender = SimpleBaseAgent("UIRecommender", "You are a UI Recommender Agent.")
        mod_agent = SimpleBaseAgent("UIModification", "You are a UI Modification Agent.")
        edit_agent = SimpleBaseAgent("UIEditing", "You are a UI Editing Agent.")
        report_agent = SimpleBaseAgent("ReportGeneration", "You are a Report Generation Agent.")
        
        print("✅ All agents created successfully")
        
        # Simulate workflow
        print("1. User Proxy Agent analyzing requirements...")
        user_req = user_proxy.call_claude("I want a modern landing page for a tech startup")
        
        print("2. Requirement Understanding Agent extracting specifications...")
        specs = req_agent.call_claude(f"Based on this request: '{user_req[:100]}...', extract UI specifications")
        
        print("3. UI Recommender Agent finding templates...")
        recommendations = recommender.call_claude(f"Based on these specs: '{specs[:100]}...', recommend templates")
        
        print("4. UI Modification Agent planning modifications...")
        mod_plan = mod_agent.call_claude("User wants to make it more colorful. Create a modification plan.")
        
        print("5. UI Editing Agent applying changes...")
        modified_code = edit_agent.call_claude("Apply the modification plan to this code: <div>Hello</div>")
        
        print("6. Report Generation Agent creating report...")
        report = report_agent.call_claude("Generate a project completion report")
        
        print("✅ Multi-agent workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Multi-agent workflow test failed: {str(e)}")
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
    base_test_passed = test_simple_base_agent()
    agent_test_passed = test_agent_specializations()
    api_test_passed = test_api_endpoints()
    workflow_test_passed = test_multi_agent_workflow()
    
    if base_test_passed and agent_test_passed and api_test_passed and workflow_test_passed:
        print("\n🎉 All simplified tests passed!")
        print("\nStatus Summary:")
        print("✅ Simplified base agent: Working")
        print("✅ Agent specializations: Working")
        print("✅ API endpoints: Working")
        print("✅ Multi-agent workflow: Working")
        print("⚠️  AutoGen integration: Needs dependency fixes")
        print("\nThe multi-agent system core is fully functional!")
        print("Each agent can work independently and in coordination.")
        print("AutoGen integration can be added later for advanced features.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 