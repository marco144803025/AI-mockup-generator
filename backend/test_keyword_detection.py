#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from config.keyword_manager import KeywordManager

def test_keyword_detection():
    try:
        keyword_manager = KeywordManager()
        
        print("=== TESTING KEYWORD DETECTION ===")
        
        # Test 1: Check page type keywords
        print("\n1. Page type keywords:")
        page_type_keywords = keyword_manager.get_page_type_keywords()
        print(f"Login keywords: {page_type_keywords.get('login', [])}")
        
        # Test 2: Test detection with "login UI mockup"
        print("\n2. Testing detection with 'I want to build a login UI mockup':")
        detected_type = keyword_manager.detect_page_type("I want to build a login UI mockup")
        print(f"Detected page type: {detected_type}")
        
        # Test 3: Test detection with "login"
        print("\n3. Testing detection with 'login':")
        detected_type2 = keyword_manager.detect_page_type("login")
        print(f"Detected page type: {detected_type2}")
        
        # Test 4: Test detection with "signin"
        print("\n4. Testing detection with 'signin':")
        detected_type3 = keyword_manager.detect_page_type("signin")
        print(f"Detected page type: {detected_type3}")
        
        # Test 5: Check configuration
        print("\n5. Configuration validation:")
        validation = keyword_manager.validate_config()
        print(f"Config valid: {validation['is_valid']}")
        if validation['errors']:
            print(f"Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"Warnings: {validation['warnings']}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_keyword_detection() 