#!/usr/bin/env python3
"""
Simple Screenshot Service Testing Script

One function to test the screenshot service with all parameters.
No defaults, no error handling - you'll see exactly what fails.
"""

import os
import sys
import asyncio

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.screenshot_service import get_screenshot_service


async def test_screenshot_service_from_session(session_id: str):
    """
        Dictionary with screenshot generation results:
        {
            "success": True/False,
            "screenshot_path": "path/to/screenshot.png",
            "base64_image": "base64_encoded_image_data",
            "html_file_path": "preview_filename.html",
            "session_id": "session_id",
            "session_data": "loaded session data"
        }
    """
    try:
        # Import the file manager to load session data
        from utils.file_manager import UICodeFileManager
        import shutil
        import os
        
        # Initialize file manager and load session
        file_manager = UICodeFileManager()
        
        if not file_manager.session_exists(session_id):
            return {
                "success": False,
                "error": f"Session {session_id} does not exist",
                "session_id": session_id
            }
        
        # Load session data
        session_data = file_manager.load_session(session_id)
        if not session_data:
            return {
                "success": False,
                "error": f"Failed to load session data for {session_id}",
                "session_id": session_id
            }
        
        # Extract HTML and CSS content from session
        current_codes = session_data.get('current_codes', {})
        html_content = current_codes.get('html_export', '')
        css_content = current_codes.get('style_css', '')
        globals_css = current_codes.get('globals_css', '')
        
        if not html_content:
            return {
                "success": False,
                "error": f"No HTML content found in session {session_id}",
                "session_id": session_id
            }
        
        # Create screenshot directory
        screenshot_dir = f"temp_previews/{session_id}"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Copy logo.png to screenshot directory if it exists
        ui_folder = f"temp_ui_files/{session_id}"
        logo_source = os.path.join(ui_folder, "logo.png")
        if os.path.exists(logo_source):
            logo_dest = os.path.join(screenshot_dir, "logo.png")
            shutil.copy2(logo_source, logo_dest)
            print(f" Logo copied to screenshot directory: {logo_dest}")
            print(f" Logo source: {logo_source}")
            print(f" Logo destination: {logo_dest}")
        else:
            print(f"  No logo.png found in session folder: {ui_folder}")
            print(f" To test with logo, add logo.png to: {ui_folder}")
        
        # Combine CSS content (style.css + globals.css)
        combined_css = ""
        if globals_css:
            combined_css += globals_css + "\n"
        if css_content:
            combined_css += css_content
        
        # Generate screenshot using the service
        screenshot_service = await get_screenshot_service()
        result = await screenshot_service.generate_screenshot(
            html_content=html_content,
            css_content=combined_css,
            session_id=session_id
        )
        
        # Add session data to result
        result['session_data'] = {
            'template_name': session_data.get('template_info', {}).get('name', 'Unknown'),
            'template_category': session_data.get('template_info', {}).get('category', 'Unknown'),
            'html_length': len(html_content),
            'css_length': len(combined_css),
            'metadata': session_data.get('metadata', {}),
            'history_count': len(session_data.get('history', []))
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error loading session data: {str(e)}",
            "session_id": session_id
        }


async def test_screenshot_service(
    html_content: str,
    css_content: str,
    session_id: str
):
    """
    Test screenshot generation with the given parameters.
    
    Args:
        html_content: The HTML content to render
            Sample: "<div class='container'><h1>Hello World</h1><p>This is a test</p></div>"
            Must be valid HTML content
        
        css_content: The CSS styling content
            Sample: ".container { max-width: 800px; margin: 0 auto; padding: 20px; } h1 { color: blue; }"
            Must be valid CSS content
        
        session_id: The session ID for organizing screenshots
            Sample: "test_session", "my_project_123", "user_abc_session"
            Will create temp_previews/{session_id}/ directory
    
    Returns:
        Dictionary with screenshot generation results:
        {
            "success": True/False,
            "screenshot_path": "path/to/screenshot.png",
            "base64_image": "base64_encoded_image_data",
            "html_file_path": "preview_filename.html",
            "session_id": "session_id"
        }
    """
    screenshot_service = await get_screenshot_service()
    result = await screenshot_service.generate_screenshot(
        html_content=html_content,
        css_content=css_content,
        session_id=session_id
    )
    return result


async def test_screenshot_with_local_image(session_id: str):
    """
    Test screenshot generation with a simple HTML that references a local image.
    This will help verify if the screenshot service can actually access local files.
    """
    try:
        import shutil
        import os
        
        # Create a simple HTML with local image reference
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .logo { max-width: 200px; border: 2px solid #ccc; }
                .test-content { margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>Local Image Test</h1>
            <p>This tests if the screenshot service can access local images:</p>
            
            <div class="test-content">
                <h2>Logo Test:</h2>
                <img src="./logo.png" alt="Test Logo" class="logo">
                <p>If you see the logo above, local image access is working!</p>
            </div>
            
            <div class="test-content">
                <h2>Fallback Test:</h2>
                <img src="./nonexistent.png" alt="This should show broken image" class="logo">
                <p>If you see a broken image above, the service is trying to load local files.</p>
            </div>
        </body>
        </html>
        """
        
        # Create screenshot directory
        screenshot_dir = f"temp_previews/{session_id}"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Copy logo.png to screenshot directory if it exists
        ui_folder = f"temp_ui_files/{session_id}"
        logo_source = os.path.join(ui_folder, "logo.png")
        if os.path.exists(logo_source):
            logo_dest = os.path.join(screenshot_dir, "logo.png")
            shutil.copy2(logo_source, logo_dest)
            print(f"Logo copied to screenshot directory: {logo_dest}")
        else:
            print(f"ℹ️  No logo.png found in session folder: {ui_folder}")
            print(f"💡 Creating a test logo for testing...")
            # Create a simple test image if no logo exists
            from PIL import Image, ImageDraw
            test_logo = Image.new('RGB', (200, 100), color='lightblue')
            draw = ImageDraw.Draw(test_logo)
            draw.text((50, 40), "TEST LOGO", fill='darkblue')
            test_logo.save(logo_dest)
            print(f"Test logo created: {logo_dest}")
        
        # Generate screenshot with the test HTML
        screenshot_service = await get_screenshot_service()
        result = await screenshot_service.generate_screenshot(
            html_content=test_html,
            css_content="",  # CSS is embedded in HTML
            session_id=session_id
        )
        
        if result["success"]:
                    print(f"Test screenshot generated: {result['screenshot_path']}")
        print(f"HTML file saved: {result['html_file_path']}")
            
            # Check if the HTML file actually contains the image reference
            with open(result['html_file_path'], 'r', encoding='utf-8') as f:
                html_content = f.read()
                if './logo.png' in html_content:
                                print("HTML file contains local image reference")
        else:
            print("HTML file missing local image reference")
        else:
            print(f"Test screenshot failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"Error in local image test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function to run the screenshot test"""
    
    # MANUALLY INPUT YOUR SESSION ID HERE:
    session_id = "mgoe1575b6-8b54-4dff-854b-b4ab3bbb4c00"
    
    # 💡 TIP: To test with logo.png, make sure your session folder contains:
    # - index.html (with <img src="./logo.png"> references)
    # - style.css
    # - globals.css  
    # - logo.png (will be automatically copied to screenshot directory)
    
    if not session_id:
        print("Please set the session_id variable in the script")
        return None
    
    try:
        print("📸 Testing Screenshot Service from Session...")
        print(f"Session ID: {session_id}")
        
        result = await test_screenshot_service_from_session(session_id)
        
        if result["success"]:
                    print("Screenshot generated successfully!")
        print(f"Screenshot saved to: {result['screenshot_path']}")
            print(f"📊 Base64 size: {len(result['base64_image'])} characters")
            print(f"🌐 HTML file: {result['html_file_path']}")
            
            # Display session data
            session_data = result.get('session_data', {})
            print(f"📋 Template: {session_data.get('template_name', 'Unknown')}")
            print(f"🏷️  Category: {session_data.get('template_category', 'Unknown')}")
            print(f"HTML Length: {session_data.get('html_length', 0)} characters")
            print(f"CSS Length: {session_data.get('css_length', 0)} characters")
            print(f"History Entries: {session_data.get('history_data', 0)}")
        else:
            print("Screenshot generation failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"Error testing screenshot service: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())
