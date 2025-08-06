#!/usr/bin/env python3
"""
File Manager for UI Codes - Replaces JSON-based storage with file-based storage
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

class UICodeFileManager:
    """Manages UI codes using individual files instead of JSON"""
    
    def __init__(self, base_dir: str = "temp_ui_files"):
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure base directory exists
        self.base_dir.mkdir(exist_ok=True)
    
    def get_session_dir(self, session_id: str) -> Path:
        """Get the directory for a specific session"""
        return self.base_dir / session_id
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session directory exists"""
        session_dir = self.get_session_dir(session_id)
        return session_dir.exists() and session_dir.is_dir()
    
    def create_session(self, session_id: str, template_data: Dict[str, Any]) -> bool:
        """Create a new session directory and write initial files"""
        try:
            session_dir = self.get_session_dir(session_id)
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract template data
            html_content = template_data.get("html_export", "")
            style_css = template_data.get("style_css", "")
            globals_css = template_data.get("globals_css", "")
            
            # Clean HTML content - remove external CSS links since CSS will be embedded
            html_content = self._clean_html_content(html_content)
            
            # Write files with proper extensions
            self._write_file(session_dir / "index.html", html_content)
            self._write_file(session_dir / "style.css", style_css)
            self._write_file(session_dir / "globals.css", globals_css)
            
            # Create original backup files
            self._write_file(session_dir / "original_index.html", html_content)
            self._write_file(session_dir / "original_style.css", style_css)
            self._write_file(session_dir / "original_globals.css", globals_css)
            
            # Create metadata
            metadata = {
                "session_id": session_id,
                "template_id": template_data.get("template_id", ""),
                "template_name": template_data.get("name", ""),
                "template_category": template_data.get("category", ""),
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            self._write_json_file(session_dir / "metadata.json", metadata)
            
            # Create empty history
            history = {
                "modifications": [],
                "total_modifications": 0,
                "last_modification": None
            }
            self._write_json_file(session_dir / "history.json", history)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from individual files"""
        try:
            session_dir = self.get_session_dir(session_id)
            if not session_dir.exists():
                return None
            
            # Load individual files
            html_content = self._read_file(session_dir / "index.html")
            style_css = self._read_file(session_dir / "style.css")
            globals_css = self._read_file(session_dir / "globals.css")
            metadata = self._read_json_file(session_dir / "metadata.json", {})
            history = self._read_json_file(session_dir / "history.json", {})
            
            # Validate that we have valid content
            if not self._is_valid_code(html_content) or not self._is_valid_code(style_css):
                self.logger.warning(f"Session {session_id} has insufficient content")
                return None
            
            # Construct the same structure as the old JSON format
            session_data = {
                "template_id": metadata.get("template_id", ""),
                "session_id": session_id,
                "last_updated": metadata.get("last_updated", ""),
                "current_codes": {
                    "html_export": html_content,
                    "style_css": style_css,
                    "globals_css": globals_css
                },
                "original_codes": {
                    "html_export": html_content,
                    "style_css": style_css,
                    "globals_css": globals_css
                },
                "template_info": {
                    "name": metadata.get("template_name", ""),
                    "category": metadata.get("template_category", ""),
                    "id": metadata.get("template_id", "")
                },
                "history": history.get("modifications", []),
                "metadata": metadata
            }
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def save_session(self, session_id: str, modified_template: Dict[str, Any], modification_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save modified template data to individual files"""
        try:
            session_dir = self.get_session_dir(session_id)
            if not session_dir.exists():
                self.logger.error(f"Session directory not found: {session_dir}")
                return False
            
            # Extract content from modified template
            html_content = modified_template.get("html_export", "")
            style_css = modified_template.get("style_css", "")
            globals_css = modified_template.get("globals_css", "")
            
            # Clean HTML content - remove external CSS links
            html_content = self._clean_html_content(html_content)
            
            # Validate content before saving
            if not self._is_valid_code(html_content):
                self.logger.error("Modified template contains invalid HTML content - refusing to save")
                return False
            
            if not self._is_valid_code(style_css):
                self.logger.error("Modified template contains invalid CSS content - refusing to save")
                return False
            
            # Write individual files
            self._write_file(session_dir / "index.html", html_content)
            self._write_file(session_dir / "style.css", style_css)
            self._write_file(session_dir / "globals.css", globals_css)
            
            # Update metadata
            metadata = self._read_json_file(session_dir / "metadata.json", {})
            metadata["last_updated"] = datetime.now().isoformat()
            self._write_json_file(session_dir / "metadata.json", metadata)
            
            # Add to history
            history = self._read_json_file(session_dir / "history.json", {})
            if "modifications" not in history:
                history["modifications"] = []
            
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_request": modification_metadata.get("user_request", "UI modification") if modification_metadata else "UI modification",
                "modification_type": modification_metadata.get("modification_type", "general") if modification_metadata else "general",
                "changes_applied": modification_metadata.get("changes_applied", ["UI modifications applied"]) if modification_metadata else ["UI modifications applied"],
                "success": True
            }
            
            history["modifications"].append(history_entry)
            history["total_modifications"] = len(history["modifications"])
            history["last_modification"] = history_entry["timestamp"]
            
            self._write_json_file(session_dir / "history.json", history)
            
            self.logger.info(f"Session {session_id} saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session directory and all its files"""
        try:
            session_dir = self.get_session_dir(session_id)
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def reset_to_original(self, session_id: str) -> bool:
        """Reset session files to their original state"""
        try:
            session_dir = self.get_session_dir(session_id)
            if not session_dir.exists():
                self.logger.error(f"Session directory does not exist: {session_id}")
                return False
            
            # Check if original backup files exist
            original_files = [
                "original_index.html",
                "original_style.css", 
                "original_globals.css"
            ]
            
            for original_file in original_files:
                original_path = session_dir / original_file
                if not original_path.exists():
                    self.logger.error(f"Original backup file not found: {original_file}")
                    return False
            
            # Restore original files to current files
            self._write_file(session_dir / "index.html", self._read_file(session_dir / "original_index.html"))
            self._write_file(session_dir / "style.css", self._read_file(session_dir / "original_style.css"))
            self._write_file(session_dir / "globals.css", self._read_file(session_dir / "original_globals.css"))
            
            # Update metadata
            metadata = self._read_json_file(session_dir / "metadata.json", {})
            metadata["last_updated"] = datetime.now().isoformat()
            metadata["reset_to_original"] = True
            self._write_json_file(session_dir / "metadata.json", metadata)
            
            # Add reset entry to history
            history = self._read_json_file(session_dir / "history.json", {})
            if "modifications" not in history:
                history["modifications"] = []
            
            history["modifications"].append({
                "timestamp": datetime.now().isoformat(),
                "modification": "Reset to original template state",
                "modification_type": "reset",
                "changes_applied": ["Restored all files to original state"]
            })
            history["total_modifications"] = len(history["modifications"])
            history["last_modification"] = datetime.now().isoformat()
            
            self._write_json_file(session_dir / "history.json", history)
            
            self.logger.info(f"Successfully reset session {session_id} to original state")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting session {session_id} to original: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        try:
            sessions = []
            for item in self.base_dir.iterdir():
                if item.is_dir() and (item / "metadata.json").exists():
                    sessions.append(item.name)
            return sessions
        except Exception as e:
            self.logger.error(f"Error listing sessions: {e}")
            return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get basic session information"""
        try:
            session_dir = self.get_session_dir(session_id)
            metadata_file = session_dir / "metadata.json"
            
            if metadata_file.exists():
                return self._read_json_file(metadata_file, {})
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting session info for {session_id}: {e}")
            return None
    
    def _write_file(self, file_path: Path, content: str) -> None:
        """Write content to a file"""
        file_path.write_text(content, encoding='utf-8')
    
    def _read_file(self, file_path: Path) -> str:
        """Read content from a file"""
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return ""
    
    def _write_json_file(self, file_path: Path, data: Any) -> None:
        """Write JSON data to a file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _read_json_file(self, file_path: Path, default: Any = None) -> Any:
        """Read JSON data from a file"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading JSON file {file_path}: {e}")
                return default
        return default
    
    def _is_valid_code(self, content: str) -> bool:
        """Check if content is valid code (not placeholder)"""
        if not content or len(content.strip()) == 0:
            return False
        
        # Check for placeholder patterns
        placeholder_patterns = [
            "[complete original html - no changes]",
            "[complete original globals css - no changes]",
            "[modified style css with gradient updates]",
            "[content unchanged]",
            "[unchanged]",
            "[same as original]",
            "[no changes]",
            "[rest unchanged]",
            "[... rest of content ...]",
            "[placeholder]",
            "[template content]",
            "[original content]"
        ]
        
        content_lower = content.lower()
        
        # Check if content contains any placeholder patterns
        for pattern in placeholder_patterns:
            if pattern in content_lower:
                return False
        
        # Additional checks for valid HTML/CSS
        if content.strip().startswith("<!DOCTYPE") or content.strip().startswith("<html"):
            # This looks like valid HTML - should be longer
            return len(content.strip()) >= 50
        
        if "{" in content and "}" in content and ":" in content:
            # This looks like valid CSS - can be shorter
            return len(content.strip()) >= 10
        
        # If content is long enough and doesn't contain placeholders, it's probably valid
        return len(content.strip()) >= 50
    
    def _clean_html_content(self, html_content: str) -> str:
        """Remove external CSS links from HTML content since CSS will be embedded"""
        import re
        
        # Remove link tags that reference CSS files
        # This pattern matches <link> tags that reference .css files
        css_link_pattern = r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\'][^"\']*\.css["\'][^>]*/?>'
        cleaned_html = re.sub(css_link_pattern, '', html_content, flags=re.IGNORECASE)
        
        # Also remove any styleguide.css references specifically
        styleguide_pattern = r'<link[^>]*href=["\'][^"\']*styleguide\.css["\'][^>]*/?>'
        cleaned_html = re.sub(styleguide_pattern, '', cleaned_html, flags=re.IGNORECASE)
        
        return cleaned_html
    
    def migrate_from_json(self, session_id: str, json_file_path: str) -> bool:
        """Migrate from old JSON format to new file format"""
        try:
            # Read the old JSON file
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract data
            current_codes = json_data.get("current_codes", {})
            template_data = {
                "html_export": current_codes.get("html_export", ""),
                "style_css": current_codes.get("style_css", ""),
                "globals_css": current_codes.get("globals_css", ""),
                "template_id": json_data.get("template_id", ""),
                "name": json_data.get("template_info", {}).get("name", ""),
                "category": json_data.get("template_info", {}).get("category", "")
            }
            
            # Create new session
            success = self.create_session(session_id, template_data)
            
            if success:
                # Copy history if it exists
                history_data = json_data.get("history", [])
                if history_data:
                    session_dir = self.get_session_dir(session_id)
                    # Ensure history is in the correct format
                    if isinstance(history_data, list):
                        history = {
                            "modifications": history_data,
                            "total_modifications": len(history_data),
                            "last_modification": history_data[-1].get("timestamp") if history_data else None
                        }
                    else:
                        history = history_data
                    
                    self._write_json_file(session_dir / "history.json", history)
                
                self.logger.info(f"Successfully migrated session {session_id} from JSON")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error migrating session {session_id} from JSON: {e}")
            return False 