#!/usr/bin/env python3
"""
Script to create original backup files for existing sessions
"""

import os
import json
from pathlib import Path
from datetime import datetime
from utils.file_manager import UICodeFileManager

def create_original_backups():
    """Create original backup files for all existing sessions"""
    print("=" * 60)
    print("Creating Original Backup Files for Existing Sessions")
    print("=" * 60)
    
    # Initialize file manager
    file_manager = UICodeFileManager()
    
    # Get all session directories
    base_dir = Path("temp_ui_files")
    session_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"\nFound {len(session_dirs)} session directories:")
    
    created_backups = 0
    skipped_sessions = 0
    failed_sessions = 0
    
    for session_dir in session_dirs:
        session_id = session_dir.name
        print(f"\nProcessing session: {session_id}")
        
        # Check if original backup files already exist
        original_files = [
            "original_index.html",
            "original_style.css",
            "original_globals.css"
        ]
        
        existing_originals = [f for f in original_files if (session_dir / f).exists()]
        
        if len(existing_originals) == 3:
            print(f"  ✅ Original backups already exist, skipping...")
            skipped_sessions += 1
            continue
        
        # Check if current files exist
        current_files = ["index.html", "style.css", "globals.css"]
        missing_current = [f for f in current_files if not (session_dir / f).exists()]
        
        if missing_current:
            print(f"  ❌ Missing current files: {missing_current}")
            failed_sessions += 1
            continue
        
        try:
            # Read current files
            html_content = file_manager._read_file(session_dir / "index.html")
            style_css = file_manager._read_file(session_dir / "style.css")
            globals_css = file_manager._read_file(session_dir / "globals.css")
            
            # Create original backup files
            file_manager._write_file(session_dir / "original_index.html", html_content)
            file_manager._write_file(session_dir / "original_style.css", style_css)
            file_manager._write_file(session_dir / "original_globals.css", globals_css)
            
            print(f"  ✅ Created original backup files")
            created_backups += 1
            
        except Exception as e:
            print(f"  ❌ Error creating backups: {e}")
            failed_sessions += 1
    
    print("\n" + "=" * 60)
    print("BACKUP CREATION RESULTS")
    print("=" * 60)
    print(f"Total sessions: {len(session_dirs)}")
    print(f"Created backups: {created_backups}")
    print(f"Skipped (already exist): {skipped_sessions}")
    print(f"Failed: {failed_sessions}")
    
    if created_backups > 0:
        print(f"\n✅ Successfully created original backups for {created_backups} sessions!")
    else:
        print(f"\nℹ️  No new backups were created.")
    
    return created_backups > 0

def test_reset_functionality():
    """Test the reset functionality on a sample session"""
    print("\n" + "=" * 60)
    print("Testing Reset Functionality")
    print("=" * 60)
    
    file_manager = UICodeFileManager()
    
    # Find a session with original backups
    base_dir = Path("temp_ui_files")
    session_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    test_session = None
    for session_dir in session_dirs:
        if (session_dir / "original_index.html").exists():
            test_session = session_dir.name
            break
    
    if not test_session:
        print("❌ No session with original backups found for testing")
        return False
    
    print(f"Testing reset functionality on session: {test_session}")
    
    try:
        # Load current state
        current_data = file_manager.load_session(test_session)
        if not current_data:
            print("❌ Failed to load current session data")
            return False
        
        print(f"  Current HTML length: {len(current_data['current_codes']['html_export'])}")
        
        # Test reset
        success = file_manager.reset_to_original(test_session)
        
        if success:
            print("  ✅ Reset to original successful")
            
            # Verify reset worked
            reset_data = file_manager.load_session(test_session)
            if reset_data:
                print(f"  Reset HTML length: {len(reset_data['current_codes']['html_export'])}")
                print("  ✅ Reset functionality working correctly!")
                return True
            else:
                print("  ❌ Failed to load session after reset")
                return False
        else:
            print("  ❌ Reset to original failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing reset: {e}")
        return False

def main():
    """Main function"""
    # Create original backups
    backups_created = create_original_backups()
    
    # Test reset functionality if backups were created or already exist
    if backups_created or any((Path("temp_ui_files") / d.name / "original_index.html").exists() 
                             for d in Path("temp_ui_files").iterdir() 
                             if d.is_dir() and not d.name.startswith('.')):
        test_reset_functionality()
    
    print("\nOriginal backup creation process completed!")
    print("You can now use the 'Reset to Original' button in the frontend.")

if __name__ == "__main__":
    main() 