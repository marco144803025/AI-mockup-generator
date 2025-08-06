#!/usr/bin/env python3
"""
Migration script to convert existing JSON-based UI codes to file-based storage
"""

import os
import json
import shutil
from pathlib import Path
from utils.file_manager import UICodeFileManager

def migrate_json_to_files():
    """Migrate all existing JSON files to the new file-based format"""
    print("🚀 Starting migration from JSON to file-based storage...")
    
    file_manager = UICodeFileManager()
    temp_dir = Path("temp_ui_files")
    
    if not temp_dir.exists():
        print("❌ temp_ui_files directory not found")
        return False
    
    # Find all JSON files
    json_files = list(temp_dir.glob("ui_codes_*.json"))
    
    if not json_files:
        print("✅ No JSON files found to migrate")
        return True
    
    print(f"📁 Found {len(json_files)} JSON files to migrate")
    
    migrated_count = 0
    failed_count = 0
    
    for json_file in json_files:
        try:
            # Extract session ID from filename
            session_id = json_file.stem.replace("ui_codes_", "")
            
            print(f"\n📝 Migrating session: {session_id}")
            
            # Check if session directory already exists
            if file_manager.session_exists(session_id):
                print(f"   ⚠️  Session {session_id} already exists, skipping")
                continue
            
            # Migrate the file
            success = file_manager.migrate_from_json(session_id, str(json_file))
            
            if success:
                print(f"   ✅ Successfully migrated {session_id}")
                migrated_count += 1
                
                # Optionally backup the original JSON file
                backup_file = json_file.with_suffix('.json.backup')
                shutil.copy2(json_file, backup_file)
                print(f"   📦 Backed up to {backup_file.name}")
            else:
                print(f"   ❌ Failed to migrate {session_id}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error migrating {json_file.name}: {e}")
            failed_count += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Successfully migrated: {migrated_count}")
    print(f"   ❌ Failed migrations: {failed_count}")
    print(f"   📁 Total JSON files: {len(json_files)}")
    
    return failed_count == 0

def cleanup_old_json_files():
    """Remove old JSON files after successful migration"""
    print("\n🧹 Cleaning up old JSON files...")
    
    temp_dir = Path("temp_ui_files")
    json_files = list(temp_dir.glob("ui_codes_*.json"))
    
    removed_count = 0
    
    for json_file in json_files:
        try:
            # Check if corresponding session directory exists
            session_id = json_file.stem.replace("ui_codes_", "")
            session_dir = temp_dir / session_id
            
            if session_dir.exists() and session_dir.is_dir():
                # Verify the session has the required files
                required_files = ["html.txt", "style.css", "globals.css", "metadata.json"]
                has_all_files = all((session_dir / file).exists() for file in required_files)
                
                if has_all_files:
                    json_file.unlink()
                    print(f"   🗑️  Removed {json_file.name}")
                    removed_count += 1
                else:
                    print(f"   ⚠️  Keeping {json_file.name} (incomplete migration)")
            else:
                print(f"   ⚠️  Keeping {json_file.name} (no session directory)")
                
        except Exception as e:
            print(f"   ❌ Error removing {json_file.name}: {e}")
    
    print(f"   📊 Removed {removed_count} JSON files")

def verify_migration():
    """Verify that all sessions were migrated correctly"""
    print("\n🔍 Verifying migration...")
    
    file_manager = UICodeFileManager()
    sessions = file_manager.list_sessions()
    
    print(f"📁 Found {len(sessions)} migrated sessions")
    
    verified_count = 0
    failed_count = 0
    
    for session_id in sessions:
        try:
            session_data = file_manager.load_session(session_id)
            
            if session_data:
                current_codes = session_data.get("current_codes", {})
                html_content = current_codes.get("html_export", "")
                style_css = current_codes.get("style_css", "")
                
                if html_content and style_css and len(html_content) > 100 and len(style_css) > 50:
                    print(f"   ✅ Session {session_id} verified")
                    verified_count += 1
                else:
                    print(f"   ⚠️  Session {session_id} has insufficient content")
                    failed_count += 1
            else:
                print(f"   ❌ Session {session_id} failed to load")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error verifying {session_id}: {e}")
            failed_count += 1
    
    print(f"\n📊 Verification Summary:")
    print(f"   ✅ Verified sessions: {verified_count}")
    print(f"   ❌ Failed verifications: {failed_count}")
    
    return failed_count == 0

def main():
    """Run the complete migration process"""
    print("=" * 60)
    print("🔄 JSON TO FILE-BASED MIGRATION")
    print("=" * 60)
    
    # Step 1: Migrate JSON files to file-based format
    migration_success = migrate_json_to_files()
    
    if not migration_success:
        print("\n❌ Migration failed, stopping here")
        return False
    
    # Step 2: Verify migration
    verification_success = verify_migration()
    
    if not verification_success:
        print("\n❌ Verification failed, keeping JSON files")
        return False
    
    # Step 3: Clean up old JSON files (optional)
    print("\n🤔 Do you want to remove old JSON files? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            cleanup_old_json_files()
        else:
            print("   📦 Keeping JSON files as backup")
    except KeyboardInterrupt:
        print("\n   📦 Keeping JSON files as backup")
    
    print("\n🎉 Migration completed successfully!")
    print("\n💡 New file structure:")
    print("   temp_ui_files/")
    print("   ├── session_id_1/")
    print("   │   ├── html.txt")
    print("   │   ├── style.css")
    print("   │   ├── globals.css")
    print("   │   ├── metadata.json")
    print("   │   └── history.json")
    print("   └── session_id_2/")
    print("       └── ...")
    
    return True

if __name__ == "__main__":
    main() 