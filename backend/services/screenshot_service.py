#!/usr/bin/env python3
"""
HTML2Image Screenshot Service for UI Preview Generation
"""

import os
import tempfile
import uuid
import base64
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from html2image import Html2Image
    HTML2IMAGE_AVAILABLE = True
except ImportError:
    HTML2IMAGE_AVAILABLE = False
    logger.warning("Html2Image not available, falling back to mock service")

class Html2ImageScreenshotService:
    """Service for generating real screenshots using Html2Image"""
    
    def __init__(self):
        self.temp_dir = Path("temp_previews")
        self.temp_dir.mkdir(exist_ok=True)
        self.hti = None
        
    def initialize(self):
        """Initialize Html2Image"""
        if not HTML2IMAGE_AVAILABLE:
            raise Exception("Html2Image not available")
            
        try:
            logger.info(f"Initializing Html2Image with output_path: {str(self.temp_dir)}")
            self.hti = Html2Image(
                output_path=str(self.temp_dir),
                size=(1920, 1580),  # Standard desktop width 1920x1080 for good detail
                browser_executable="chrome"  # Use Chrome if available
            )
            logger.info("Html2Image initialized successfully")
            logger.info(f"Html2Image instance: {self.hti}")
        except Exception as e:
            logger.error(f"Failed to initialize Html2Image: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def create_html_template(self, html_content: str, css_content: str) -> str:
        """Create HTML template with embedded CSS"""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, initial-scale=1.0">
    <title>UI Preview</title>
    <style>
        /* Reset and full-page styles */
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: auto;
            min-height: 100vh;
            box-sizing: border-box;
        }}
        
        /* User styles */
        {css_content}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
        return html_template
        
    async def generate_screenshot(self, html_content: str, css_content: str, session_id: str) -> Dict[str, Any]:
        """Generate a real screenshot from HTML/CSS content using Html2Image"""
        try:
            logger.info(f"Generating real screenshot for session: {session_id}")
            
            if not HTML2IMAGE_AVAILABLE:
                logger.error("Html2Image not available")
                return {
                    "success": False,
                    "error": "Html2Image not available",
                    "session_id": session_id
                }
            
            # Initialize Html2Image if not already done
            if not self.hti:
                logger.info("Initializing Html2Image...")
                try:
                    self.initialize()
                    logger.info("Html2Image initialized successfully")
                except Exception as init_error:
                    logger.error(f"Failed to initialize Html2Image: {init_error}")
                    return {
                        "success": False,
                        "error": f"Html2Image initialization failed: {init_error}",
                        "session_id": session_id
                    }
            
            # Create session-specific temp directory
            session_temp_dir = self.temp_dir / session_id
            session_temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())[:8]
            screenshot_name = f"screenshot_{file_id}.png"
            
            # Create HTML template with embedded CSS
            logger.info("Creating HTML template...")
            html_template = self.create_html_template(html_content, css_content)
            
            # Save HTML as a file so local images can be accessed
            html_filename = f"preview_{file_id}.html"
            html_file_path = session_temp_dir / html_filename
            
            # Convert relative image paths to base64 for Html2Image
            import re
            import base64
            updated_html = html_template
            
            # Find all img tags with relative src paths and convert them to base64
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            def replace_img_src(match):
                img_tag = match.group(0)
                src = match.group(1)
                
                # If it's a relative path (starts with ./ or just filename)
                if src.startswith('./') or (not src.startswith(('http://', 'https://', 'data:', '/'))):
                    # Remove ./ if present
                    clean_src = src.replace('./', '')
                    # Check if the image file exists in the session directory
                    image_path = session_temp_dir / clean_src
                    
                    if image_path.exists():
                        try:
                            # Read the image file and convert to base64
                            with open(image_path, 'rb') as img_file:
                                img_data = img_file.read()
                                img_base64 = base64.b64encode(img_data).decode('utf-8')
                                
                                # Determine MIME type based on file extension
                                mime_type = 'image/png'  # default
                                if clean_src.lower().endswith('.jpg') or clean_src.lower().endswith('.jpeg'):
                                    mime_type = 'image/jpeg'
                                elif clean_src.lower().endswith('.gif'):
                                    mime_type = 'image/gif'
                                elif clean_src.lower().endswith('.webp'):
                                    mime_type = 'image/webp'
                                
                                # Replace the src attribute with base64 data URL
                                data_url = f"data:{mime_type};base64,{img_base64}"
                                new_img_tag = img_tag.replace(f'src="{src}"', f'src="{data_url}"')
                                logger.info(f"Converted image to base64: {src} -> {mime_type} ({len(img_data)} bytes)")
                                return new_img_tag
                                
                        except Exception as e:
                            logger.error(f"Failed to convert image {src} to base64: {e}")
                            # Fall back to original tag if conversion fails
                            return img_tag
                    else:
                        logger.warning(f"Image file not found: {image_path}")
                        return img_tag
                return img_tag
            
            updated_html = re.sub(img_pattern, replace_img_src, updated_html)
            
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)
            logger.info(f"HTML file saved with absolute image paths: {html_file_path}")
            
            # Generate screenshot using Html2Image with HTML file
            logger.info("Generating screenshot with Html2Image...")
            logger.info(f"HTML file path: {html_file_path}")
            logger.info(f"Screenshot name: {screenshot_name}")
            
            screenshot_paths = self.hti.screenshot(
                html_file=str(html_file_path),
                save_as=screenshot_name,
                size=(1920, 1080)  # Standard desktop width (1920) for good detail
            )
            
            logger.info(f"Screenshot paths returned: {screenshot_paths}")
            
            # Find the generated screenshot
            logger.info(f"Looking for screenshot in paths: {screenshot_paths}")
            screenshot_path = None
            for path in screenshot_paths:
                logger.info(f"Checking path: {path}")
                if path.endswith(screenshot_name):
                    screenshot_path = Path(path)
                    logger.info(f"Found screenshot at: {screenshot_path}")
                    break
            
            if not screenshot_path:
                logger.error(f"No screenshot path found in returned paths: {screenshot_paths}")
                return {
                    "success": False,
                    "error": f"No screenshot path found in returned paths: {screenshot_paths}",
                    "session_id": session_id
                }
            
            if not screenshot_path.exists():
                logger.error(f"Screenshot file does not exist at: {screenshot_path}")
                return {
                    "success": False,
                    "error": f"Screenshot file does not exist at: {screenshot_path}",
                    "session_id": session_id
                }
            
            # Move to session directory
            final_screenshot_path = session_temp_dir / screenshot_name
            if screenshot_path != final_screenshot_path:
                screenshot_path.replace(final_screenshot_path)
                screenshot_path = final_screenshot_path
            
            # Convert to base64
            logger.info("Converting to base64...")
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            logger.info(f"Generated real screenshot: {screenshot_path}, size: {len(base64_image)} bytes")
            
            return {
                "success": True,
                "screenshot_path": str(screenshot_path),
                "base64_image": base64_image,
                "html_file_path": str(html_file_path),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error generating real screenshot: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

# Global instance
screenshot_service = Html2ImageScreenshotService()

async def get_screenshot_service() -> Html2ImageScreenshotService:
    """Get the screenshot service instance"""
    return screenshot_service

class MockScreenshotService:
    """Mock service for when Html2Image is not available"""
    
    async def generate_screenshot(self, html_content: str, css_content: str, session_id: str) -> Dict[str, Any]:
        """Mock screenshot generation"""
        logger.warning("Using mock screenshot service - no preview available")
        return {
            "success": False,
            "error": "Html2Image not available",
            "session_id": session_id
        } 