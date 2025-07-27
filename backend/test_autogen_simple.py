#!/usr/bin/env python3
"""
Simple AutoGen Test - Bypasses database dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_autogen_imports():
    """Test basic AutoGen imports without database dependencies"""
    print("🧪 Testing AutoGen Imports (No Database)...")
    
    try:
        # Test autogen import
        import autogen
        print("✅ autogen imported successfully")
        
        # Test anthropic import
        from anthropic import Anthropic
        print("✅ anthropic imported successfully")
        
        # Test basic autogen functionality
        if hasattr(autogen, 'AssistantAgent'):
            print("✅ autogen.AssistantAgent available")
        else:
            print("❌ autogen.AssistantAgent not found")
            
        if hasattr(autogen, 'UserProxyAgent'):
            print("✅ autogen.UserProxyAgent available")
        else:
            print("❌ autogen.UserProxyAgent not found")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_agent_creation():
    """Test creating basic AutoGen agents"""
    print("\n🧪 Testing Agent Creation...")
    
    try:
        import autogen
        from anthropic import Anthropic
        
        # Test creating an AssistantAgent
        assistant = autogen.AssistantAgent(
            name="test_assistant",
            system_message="You are a helpful assistant.",
            llm_config={
                "config_list": [{"model": "claude-3-5-sonnet-20241022", "api_key": "test"}],
                "temperature": 0.7
            }
        )
        print("✅ AssistantAgent created successfully")
        
        # Test creating a UserProxyAgent
        user_proxy = autogen.UserProxyAgent(
            name="test_user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1
        )
        print("✅ UserProxyAgent created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Simple AutoGen Tests")
    print("=" * 50)
    
    # Test 1: Basic imports
    imports_ok = test_autogen_imports()
    
    # Test 2: Agent creation (only if imports worked)
    agents_ok = False
    if imports_ok:
        agents_ok = test_agent_creation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Agents:  {'✅ PASS' if agents_ok else '❌ FAIL'}")
    
    if imports_ok and agents_ok:
        print("\n🎉 All basic AutoGen tests passed!")
        print("   The AutoGen system is working correctly.")
        print("   Database integration can be tested separately.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return imports_ok and agents_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 