#!/usr/bin/env python3
"""
Test script to verify the simplified UI editing approach
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ui_editing_agent import UIEditingAgent
from utils.file_manager import UICodeFileManager

def test_simplified_approach():
    """Test the simplified approach where editing agent outputs complete code"""
    print("=== Testing Simplified UI Editing Approach ===")
    
    # Initialize the agent
    agent = UIEditingAgent()
    
    # Load test session
    session_id = "8221258e-98ca-49fb-82de-211447caf521"
    file_manager = UICodeFileManager()
    
    if not file_manager.session_exists(session_id):
        print(f"Session {session_id} not found!")
        return
    
    session_data = file_manager.load_session(session_id)
    current_template = session_data["current_codes"]
    
    print(f"Loaded template with:")
    print(f"  HTML length: {len(current_template.get('html_export', ''))}")
    print(f"  Style CSS length: {len(current_template.get('style_css', ''))}")
    print(f"  Global CSS length: {len(current_template.get('globals_css', ''))}")
    
    # Test the same request that failed before
    user_request = "change the color of header 'our' in our home to be green instead of black"
    
    print(f"\nUser Request: {user_request}")
    
    try:
        result = agent.process_modification_request(user_request, current_template)
        
        print(f"\nResult:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            modified_template = result.get('modified_template', {})
            changes_summary = result.get('changes_summary', [])
            
            print(f"Changes Summary: {changes_summary}")
            print(f"Modified HTML length: {len(modified_template.get('html_export', ''))}")
            print(f"Modified Style CSS length: {len(modified_template.get('style_css', ''))}")
            print(f"Modified Global CSS length: {len(modified_template.get('globals_css', ''))}")
            
            # Check if the modification was applied
            modified_css = modified_template.get('style_css', '')
            if 'color: green' in modified_css.lower() or 'color:green' in modified_css.lower():
                print("✅ Green color modification found in CSS!")
            else:
                print("❌ Green color modification not found in CSS")
                
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during modification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Simplified UI Editing Approach")
    print("=" * 50)
    
    try:
        test_simplified_approach()
        
        print("\n" + "=" * 50)
        print("Testing completed!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc() 