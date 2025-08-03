#!/usr/bin/env python3
"""
Test screenshot service in FastAPI-like environment
"""

import asyncio
import sys
import json
from pathlib import Path

# Set Windows event loop policy for Playwright compatibility
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from services.screenshot_service import get_screenshot_service

async def test_fastapi_screenshot():
    """Test screenshot service in FastAPI-like environment"""
    try:
        # Load test data (same as FastAPI endpoint)
        test_file_path = Path("temp_ui_files/ui_codes_test_session.json")
        
        if not test_file_path.exists():
            print("Test file not found!")
            return
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print("✅ Test data loaded successfully")
        print(f"Template name: {test_data['template_info']['name']}")
        
        # Test screenshot service (same as FastAPI endpoint)
        screenshot_service = await get_screenshot_service()
        html_content = test_data["current_codes"]["html_export"]
        css_content = test_data["current_codes"]["globals_css"] + "\n" + test_data["current_codes"]["style_css"]
        
        print("✅ HTML and CSS content extracted")
        print(f"HTML length: {len(html_content)}")
        print(f"CSS length: {len(css_content)}")
        
        # Test image generation (same as FastAPI endpoint)
        result = await screenshot_service.generate_screenshot(html_content, css_content, "default")
        
        print("✅ Screenshot generation completed")
        print(f"Success: {result['success']}")
        print(f"Screenshot length: {len(result.get('base64_image', ''))}")
        
        if result['success']:
            print("🎉 Screenshot generated successfully!")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fastapi_screenshot()) 