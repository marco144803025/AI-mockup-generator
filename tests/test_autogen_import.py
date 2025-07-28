#!/usr/bin/env python3
"""
Simple autogen import test
"""

def test_autogen_import():
    """Test if autogen can be imported correctly"""
    try:
        import autogen
        print("✓ AutoGen imported successfully")
        
        # Test basic autogen functionality
        if hasattr(autogen, 'AssistantAgent'):
            print("✓ AssistantAgent is available")
        else:
            print("✗ AssistantAgent is NOT available")
            
        if hasattr(autogen, 'UserProxyAgent'):
            print("✓ UserProxyAgent is available")
        else:
            print("✗ UserProxyAgent is NOT available")
            
        if hasattr(autogen, 'GroupChat'):
            print("✓ GroupChat is available")
        else:
            print("✗ GroupChat is NOT available")
            
        return True
        
    except Exception as e:
        print(f"✗ Error importing autogen: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing AutoGen Import...")
    success = test_autogen_import()
    print(f"\n{'✓ All tests passed' if success else '✗ Tests failed'}") 