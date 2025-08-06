#!/usr/bin/env python3
"""
Test Script for New File-Based UI Code Storage System
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the file manager
from utils.file_manager import UICodeFileManager

class FileSystemTester:
    """Test the new file-based UI code storage system"""
    
    def __init__(self):
        self.test_dir = Path("temp_ui_files/test_sessions")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.file_manager = UICodeFileManager(str(self.test_dir))
    
    def create_test_template_data(self) -> Dict[str, Any]:
        """Create sample template data for testing"""
        return {
            "html_export": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Template</title>
    <link rel="stylesheet" href="globals.css">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Test Website</h1>
            <nav>
                <ul>
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>
        <main class="main">
            <section class="hero">
                <h2>Welcome to Our Site</h2>
                <p>This is a test template for the new file-based system.</p>
                <button class="cta-button">Get Started</button>
            </section>
        </main>
        <footer class="footer">
            <p>&copy; 2024 Test Company. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>""",
            "style_css": """.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    border-radius: 0 0 10px 10px;
}

.header h1 {
    margin: 0;
    font-size: 2rem;
    text-align: center;
}

nav ul {
    list-style: none;
    padding: 0;
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.3s;
}

nav a:hover {
    opacity: 0.8;
}

.main {
    padding: 3rem 0;
}

.hero {
    text-align: center;
    padding: 4rem 0;
}

.hero h2 {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #333;
}

.hero p {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}

.cta-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 50px;
    cursor: pointer;
    transition: transform 0.3s;
}

.cta-button:hover {
    transform: translateY(-2px);
}

.footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
    border-radius: 10px 10px 0 0;
}""",
            "globals_css": """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.2;
}

a {
    color: inherit;
    text-decoration: none;
}

button {
    font-family: inherit;
}

img {
    max-width: 100%;
    height: auto;
}""",
            "template_id": "test_template_001",
            "name": "Test Landing Page",
            "category": "landing"
        }
    
    def test_session_creation(self) -> bool:
        """Test creating a new session"""
        logger.info("Testing session creation...")
        
        session_id = "test_session_001"
        template_data = self.create_test_template_data()
        
        # Create session
        success = self.file_manager.create_session(session_id, template_data)
        
        if not success:
            logger.error("❌ Session creation failed")
            return False
        
        # Verify session directory exists
        session_dir = self.file_manager.get_session_dir(session_id)
        if not session_dir.exists():
            logger.error("❌ Session directory not created")
            return False
        
        # Verify all required files exist
        required_files = ["index.html", "style.css", "globals.css", "metadata.json", "history.json"]
        for file_name in required_files:
            file_path = session_dir / file_name
            if not file_path.exists():
                logger.error(f"❌ Required file missing: {file_name}")
                return False
        
        logger.info("✅ Session creation test passed")
        return True
    
    def test_session_loading(self) -> bool:
        """Test loading a session"""
        logger.info("Testing session loading...")
        
        session_id = "test_session_001"
        
        # Load session
        session_data = self.file_manager.load_session(session_id)
        
        if not session_data:
            logger.error("❌ Session loading failed")
            return False
        
        # Verify data structure
        required_keys = ["template_id", "session_id", "current_codes", "template_info"]
        for key in required_keys:
            if key not in session_data:
                logger.error(f"❌ Missing key in session data: {key}")
                return False
        
        # Verify content
        current_codes = session_data["current_codes"]
        if not current_codes.get("html_export") or not current_codes.get("style_css"):
            logger.error("❌ Missing content in current_codes")
            return False
        
        logger.info("✅ Session loading test passed")
        return True
    
    def test_session_saving(self) -> bool:
        """Test saving modifications to a session"""
        logger.info("Testing session saving...")
        
        session_id = "test_session_001"
        
        # Create modified template data
        modified_template = {
            "html_export": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modified Test Template</title>
    <link rel="stylesheet" href="globals.css">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Modified Test Website</h1>
            <nav>
                <ul>
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                    <li><a href="#services">Services</a></li>
                </ul>
            </nav>
        </header>
        <main class="main">
            <section class="hero">
                <h2>Welcome to Our Modified Site</h2>
                <p>This template has been modified to test the save functionality.</p>
                <button class="cta-button">Get Started Now</button>
            </section>
        </main>
        <footer class="footer">
            <p>&copy; 2024 Modified Test Company. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>""",
            "style_css": """.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    padding: 1.5rem 0;
    border-radius: 0 0 15px 15px;
}

.header h1 {
    margin: 0;
    font-size: 2.5rem;
    text-align: center;
}

nav ul {
    list-style: none;
    padding: 0;
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    margin-top: 1.5rem;
}

nav a {
    color: white;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s;
}

nav a:hover {
    opacity: 0.8;
    transform: translateY(-2px);
}

.main {
    padding: 4rem 0;
}

.hero {
    text-align: center;
    padding: 5rem 0;
}

.hero h2 {
    font-size: 3.5rem;
    margin-bottom: 1.5rem;
    color: #2c3e50;
}

.hero p {
    font-size: 1.3rem;
    color: #7f8c8d;
    margin-bottom: 2.5rem;
}

.cta-button {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    border: none;
    padding: 1.2rem 2.5rem;
    font-size: 1.2rem;
    border-radius: 50px;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.cta-button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

.footer {
    background: #2c3e50;
    color: white;
    text-align: center;
    padding: 2.5rem 0;
    margin-top: 4rem;
    border-radius: 15px 15px 0 0;
}""",
            "globals_css": """@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.7;
    color: #2c3e50;
    background-color: #ecf0f1;
}

h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.3;
}

a {
    color: inherit;
    text-decoration: none;
}

button {
    font-family: inherit;
}

img {
    max-width: 100%;
    height: auto;
}"""
        }
        
        # Save modifications
        modification_metadata = {
            "user_request": "Change the color scheme to red and add a services link",
            "modification_type": "color_and_content",
            "changes_applied": [
                "Changed header gradient to red tones",
                "Updated button colors to match new theme",
                "Added services link to navigation",
                "Modified title and description text",
                "Updated font family to Poppins"
            ]
        }
        
        success = self.file_manager.save_session(session_id, modified_template, modification_metadata)
        
        if not success:
            logger.error("❌ Session saving failed")
            return False
        
        # Verify the changes were saved
        session_data = self.file_manager.load_session(session_id)
        if not session_data:
            logger.error("❌ Could not reload saved session")
            return False
        
        # Check if modifications are reflected
        current_codes = session_data["current_codes"]
        if "Modified Test Website" not in current_codes.get("html_export", ""):
            logger.error("❌ HTML modifications not saved")
            return False
        
        if "ff6b6b" not in current_codes.get("style_css", ""):
            logger.error("❌ CSS modifications not saved")
            return False
        
        # Check history
        history = self.file_manager._read_json_file(self.file_manager.get_session_dir(session_id) / "history.json", {})
        if not history.get("modifications"):
            logger.error("❌ History not updated")
            return False
        
        logger.info("✅ Session saving test passed")
        return True
    
    def test_session_operations(self) -> bool:
        """Test various session operations"""
        logger.info("Testing session operations...")
        
        # Test session existence
        session_id = "test_session_001"
        if not self.file_manager.session_exists(session_id):
            logger.error("❌ Session existence check failed")
            return False
        
        # Test listing sessions
        sessions = self.file_manager.list_sessions()
        if session_id not in sessions:
            logger.error("❌ Session listing failed")
            return False
        
        # Test getting session info
        session_info = self.file_manager.get_session_info(session_id)
        if not session_info:
            logger.error("❌ Session info retrieval failed")
            return False
        
        logger.info("✅ Session operations test passed")
        return True
    
    def test_migration_from_json(self) -> bool:
        """Test migration from old JSON format"""
        logger.info("Testing JSON migration...")
        
        # Create a test JSON file in old format
        test_json_data = {
            "template_id": "migration_test_001",
            "session_id": "migration_test_session",
            "last_updated": datetime.now().isoformat(),
            "current_codes": {
                "html_export": "<!DOCTYPE html><html><head><title>Migration Test</title></head><body><h1>Migration Test</h1></body></html>",
                "style_css": "body { font-family: Arial; } h1 { color: blue; }",
                "globals_css": "* { margin: 0; padding: 0; }"
            },
            "history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "modification": "Test migration",
                    "changes": ["Created test template"]
                }
            ],
            "template_info": {
                "name": "Migration Test Template",
                "category": "test",
                "description": "Template for testing migration"
            }
        }
        
        # Write test JSON file
        test_json_file = self.test_dir / "ui_codes_migration_test_session.json"
        with open(test_json_file, 'w', encoding='utf-8') as f:
            json.dump(test_json_data, f, indent=2, ensure_ascii=False)
        
        # Test migration
        success = self.file_manager.migrate_from_json("migration_test_session", str(test_json_file))
        
        if not success:
            logger.error("❌ JSON migration failed")
            return False
        
        # Verify migrated session
        session_data = self.file_manager.load_session("migration_test_session")
        if not session_data:
            logger.error("❌ Migrated session not loadable")
            return False
        
        # Verify content was preserved
        if "Migration Test" not in session_data["current_codes"]["html_export"]:
            logger.error("❌ HTML content not preserved in migration")
            return False
        
        logger.info("✅ JSON migration test passed")
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        logger.info("Testing error handling...")
        
        # Test loading non-existent session
        session_data = self.file_manager.load_session("non_existent_session")
        if session_data is not None:
            logger.error("❌ Should return None for non-existent session")
            return False
        
        # Test saving to non-existent session
        modified_template = {"html_export": "<html></html>", "style_css": "body {}", "globals_css": ""}
        success = self.file_manager.save_session("non_existent_session", modified_template)
        if success:
            logger.error("❌ Should fail to save to non-existent session")
            return False
        
        logger.info("✅ Error handling test passed")
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        try:
            shutil.rmtree(self.test_dir)
            logger.info("✅ Test data cleaned up")
        except Exception as e:
            logger.error(f"❌ Error cleaning up test data: {e}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests"""
        logger.info("Starting comprehensive file system tests...")
        
        test_results = {}
        
        try:
            test_results["session_creation"] = self.test_session_creation()
            test_results["session_loading"] = self.test_session_loading()
            test_results["session_saving"] = self.test_session_saving()
            test_results["session_operations"] = self.test_session_operations()
            test_results["json_migration"] = self.test_migration_from_json()
            test_results["error_handling"] = self.test_error_handling()
            
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            return {"error": False}
        
        finally:
            self.cleanup_test_data()
        
        return test_results

def main():
    """Main test function"""
    print("=" * 60)
    print("File-Based UI Code Storage System Tests")
    print("=" * 60)
    
    tester = FileSystemTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, result in results.items():
        total += 1
        if result:
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The new file system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 