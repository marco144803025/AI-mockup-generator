#!/usr/bin/env python3
"""
Migration script to update existing sessions to use the new file format
"""

import os
import shutil
from pathlib import Path
from utils.file_manager import UICodeFileManager

def migrate_session_to_new_format(session_id: str):
    """Migrate a specific session to the new file format"""
    print(f"🔄 Migrating session {session_id} to new format...")
    
    file_manager = UICodeFileManager()
    session_dir = file_manager.get_session_dir(session_id)
    
    if not session_dir.exists():
        print(f"   ❌ Session directory not found: {session_dir}")
        return False
    
    try:
        # Check if old format files exist
        old_html_file = session_dir / "html.txt"
        if not old_html_file.exists():
            print(f"   ❌ Old HTML file not found: {old_html_file}")
            return False
        
        # Read old files
        old_html_content = file_manager._read_file(old_html_file)
        style_css = file_manager._read_file(session_dir / "style.css")
        globals_css = file_manager._read_file(session_dir / "globals.css")
        metadata = file_manager._read_json_file(session_dir / "metadata.json", {})
        history = file_manager._read_json_file(session_dir / "history.json", {})
        
        # Clean HTML content - remove external CSS links
        cleaned_html = file_manager._clean_html_content(old_html_content)
        
        # Create backup of old files
        backup_dir = session_dir / "backup_old_format"
        backup_dir.mkdir(exist_ok=True)
        
        if old_html_file.exists():
            shutil.copy2(old_html_file, backup_dir / "html.txt")
        
        # Write new files with proper extensions
        file_manager._write_file(session_dir / "index.html", cleaned_html)
        file_manager._write_file(session_dir / "style.css", style_css)
        file_manager._write_file(session_dir / "globals.css", globals_css)
        
        # Update history format if needed
        if isinstance(history, list):
            # Convert old list format to new dict format
            new_history = {
                "modifications": history,
                "total_modifications": len(history),
                "last_modification": history[-1]["timestamp"] if history else None
            }
            file_manager._write_json_file(session_dir / "history.json", new_history)
        
        # Remove old html.txt file
        if old_html_file.exists():
            old_html_file.unlink()
        
        print(f"   ✅ Successfully migrated session {session_id}")
        print(f"   📁 New files: index.html, style.css, globals.css")
        print(f"   🔧 Cleaned HTML: removed external CSS links")
        print(f"   💾 Backup created in: {backup_dir}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error migrating session {session_id}: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Session Migration to New File Format\n")
    
    # Migrate the specific session
    session_id = "cfa3365e-cc3c-43b4-b3bc-d7144f5b6014"
    
    success = migrate_session_to_new_format(session_id)
    
    print("\n" + "="*60)
    print("📊 MIGRATION SUMMARY")
    print("="*60)
    
    if success:
        print("✅ Migration completed successfully!")
        print("\n🎉 The session now uses the new file format:")
        print("   - index.html (instead of html.txt)")
        print("   - Cleaned HTML (no external CSS links)")
        print("   - Proper file extensions")
        print("\n💡 This should fix the black preview issue!")
    else:
        print("❌ Migration failed")
        print("\n⚠️  Please check the error messages above")
    
    return success

if __name__ == "__main__":
    main() 