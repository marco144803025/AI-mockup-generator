#!/usr/bin/env python3
"""
Test script to verify the simplified single-prompt UI editing approach
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ui_editing_agent import UIEditingAgent
from utils.file_manager import UICodeFileManager

def test_single_prompt_approach():
    """Test the simplified single-prompt approach"""
    print("=== Testing Single-Prompt UI Editing Approach ===")
    
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

def test_single_prompt_vs_two_step():
    """Compare the new single-prompt approach with the old two-step approach"""
    print("\n=== Comparing Single-Prompt vs Two-Step Approach ===")
    
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
    
    # Test request
    user_request = "change the background color of the login button to blue"
    
    print(f"Testing request: {user_request}")
    
    try:
        # Test single-prompt approach
        print("\n--- Single-Prompt Approach ---")
        result_single = agent.process_modification_request(user_request, current_template)
        
        print(f"Success: {result_single.get('success', False)}")
        if result_single.get('success'):
            changes = result_single.get('changes_summary', [])
            print(f"Changes: {changes}")
            
            # Check for blue background
            modified_css = result_single.get('modified_template', {}).get('style_css', '')
            if 'background-color: blue' in modified_css.lower() or 'background-color:blue' in modified_css.lower():
                print("✅ Blue background modification found!")
            else:
                print("❌ Blue background modification not found")
        else:
            print(f"Error: {result_single.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during single-prompt test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Single-Prompt UI Editing Approach")
    print("=" * 50)
    
    try:
        test_single_prompt_approach()
        test_single_prompt_vs_two_step()
        
        print("\n" + "=" * 50)
        print("Testing completed!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc() 