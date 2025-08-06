#!/usr/bin/env python3
"""
Debug script to examine the exact HTML and CSS content being passed to screenshot service
"""

from utils.file_manager import UICodeFileManager

def debug_screenshot_content():
    """Debug the exact content being passed to screenshot service"""
    print("🔍 Debugging screenshot content...")
    
    session_id = "cfa3365e-cc3c-43b4-b3bc-d7144f5b6014"
    
    # Load session data
    file_manager = UICodeFileManager()
    session_data = file_manager.load_session(session_id)
    
    if not session_data:
        print("   ❌ Failed to load session data")
        return
    
    # Extract content
    current_codes = session_data.get("current_codes", {})
    html_content = current_codes.get("html_export", "")
    style_css = current_codes.get("style_css", "")
    globals_css = current_codes.get("globals_css", "")
    
    print(f"   📊 Content Analysis:")
    print(f"      HTML length: {len(html_content)}")
    print(f"      Style CSS length: {len(style_css)}")
    print(f"      Global CSS length: {len(globals_css)}")
    
    # Show HTML content
    print(f"\n   📄 HTML Content (first 500 chars):")
    print("   " + "="*50)
    print(html_content[:500])
    print("   " + "="*50)
    
    # Show CSS content
    print(f"\n   🎨 Style CSS Content:")
    print("   " + "="*50)
    print(style_css)
    print("   " + "="*50)
    
    print(f"\n   🌐 Global CSS Content:")
    print("   " + "="*50)
    print(globals_css)
    print("   " + "="*50)
    
    # Check for specific issues
    print(f"\n   🔍 Content Analysis:")
    
    # Check if HTML has body content
    if '<body>' in html_content and '</body>' in html_content:
        body_start = html_content.find('<body>') + 6
        body_end = html_content.find('</body>')
        body_content = html_content[body_start:body_end].strip()
        print(f"      ✅ HTML has body content (length: {len(body_content)})")
        print(f"      📝 Body content preview: {body_content[:100]}...")
    else:
        print(f"      ❌ HTML missing body tags")
    
    # Check if CSS has background colors
    if 'background-color' in style_css.lower():
        print(f"      ✅ Style CSS contains background-color")
    else:
        print(f"      ⚠️  Style CSS missing background-color")
    
    # Check if CSS has color properties
    if 'color:' in style_css.lower():
        print(f"      ✅ Style CSS contains color properties")
    else:
        print(f"      ⚠️  Style CSS missing color properties")
    
    # Check for specific classes
    if '.login' in style_css:
        print(f"      ✅ Style CSS contains .login class")
    else:
        print(f"      ❌ Style CSS missing .login class")
    
    # Show what the screenshot service would receive
    combined_css = globals_css + "\n" + style_css
    print(f"\n   🔧 Combined CSS (first 500 chars):")
    print("   " + "="*50)
    print(combined_css[:500])
    print("   " + "="*50)

if __name__ == "__main__":
    debug_screenshot_content() 