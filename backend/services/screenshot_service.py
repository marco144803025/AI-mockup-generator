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
            self.hti = Html2Image(
                output_path=str(self.temp_dir),
                size=(1920, 4800),  # Standard desktop width 1920x4800 for good detail
                browser_executable="chrome"  # Use Chrome if available
            )
            logger.info("Html2Image initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Html2Image: {e}")
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
            
            # Generate screenshot using Html2Image
            logger.info("Generating screenshot with Html2Image...")
            screenshot_paths = self.hti.screenshot(
                html_str=html_template,
                save_as=screenshot_name,
                size=(1920, 4800)  # Standard desktop width (1920) for good detail
            )
            
            # Find the generated screenshot
            screenshot_path = None
            for path in screenshot_paths:
                if path.endswith(screenshot_name):
                    screenshot_path = Path(path)
                    break
            
            if not screenshot_path or not screenshot_path.exists():
                logger.error("Screenshot file not generated")
                return {
                    "success": False,
                    "error": "Screenshot file not generated",
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
                "html_file_path": f"preview_{file_id}.html",
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