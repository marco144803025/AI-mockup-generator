#!/usr/bin/env python3
"""
Comprehensive Migration Script: JSON to File-Based UI Code Storage
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UICodeMigrationManager:
    """Manages migration from JSON-based to file-based UI code storage"""
    
    def __init__(self, base_dir: str = "temp_ui_files"):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "backup_json_files"
        
        # Ensure directories exist
        self.base_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
    
    def find_json_files(self) -> List[Path]:
        """Find all JSON files that need to be migrated"""
        json_files = []
        for file_path in self.base_dir.glob("ui_codes_*.json"):
            if file_path.is_file():
                json_files.append(file_path)
        return json_files
    
    def extract_session_id(self, json_file: Path) -> str:
        """Extract session ID from JSON filename"""
        filename = json_file.stem  # Remove .json extension
        if filename.startswith("ui_codes_"):
            return filename[9:]  # Remove "ui_codes_" prefix
        return filename
    
    def migrate_json_file(self, json_file: Path) -> bool:
        """Migrate a single JSON file to file-based format"""
        try:
            session_id = self.extract_session_id(json_file)
            logger.info(f"Migrating session: {session_id}")
            
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Create session directory
            session_dir = self.base_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Extract template data
            current_codes = json_data.get("current_codes", {})
            template_info = json_data.get("template_info", {})
            
            # Write HTML file
            html_content = current_codes.get("html_export", "")
            if html_content:
                html_file = session_dir / "index.html"
                html_file.write_text(html_content, encoding='utf-8')
                logger.info(f"  - Created index.html ({len(html_content)} chars)")
            
            # Write CSS files
            style_css = current_codes.get("style_css", "")
            if style_css:
                style_file = session_dir / "style.css"
                style_file.write_text(style_css, encoding='utf-8')
                logger.info(f"  - Created style.css ({len(style_css)} chars)")
            
            globals_css = current_codes.get("globals_css", "")
            if globals_css:
                globals_file = session_dir / "globals.css"
                globals_file.write_text(globals_css, encoding='utf-8')
                logger.info(f"  - Created globals.css ({len(globals_css)} chars)")
            
            # Create metadata
            metadata = {
                "session_id": session_id,
                "template_id": json_data.get("template_id", ""),
                "template_name": template_info.get("name", ""),
                "template_category": template_info.get("category", ""),
                "created_at": json_data.get("last_updated", datetime.now().isoformat()),
                "last_updated": json_data.get("last_updated", datetime.now().isoformat()),
                "version": "1.0",
                "migrated_from": str(json_file),
                "migration_date": datetime.now().isoformat()
            }
            
            metadata_file = session_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"  - Created metadata.json")
            
            # Create history
            history = {
                "modifications": json_data.get("history", []),
                "total_modifications": len(json_data.get("history", [])),
                "last_modification": json_data.get("last_updated") if json_data.get("history") else None
            }
            
            history_file = session_dir / "history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            logger.info(f"  - Created history.json ({len(json_data.get('history', []))} entries)")
            
            # Backup original JSON file
            backup_file = self.backup_dir / json_file.name
            shutil.copy2(json_file, backup_file)
            logger.info(f"  - Backed up to {backup_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating {json_file}: {e}")
            return False
    
    def migrate_all_files(self, cleanup_old: bool = False) -> Dict[str, Any]:
        """Migrate all JSON files to file-based format"""
        logger.info("Starting comprehensive migration...")
        
        json_files = self.find_json_files()
        logger.info(f"Found {len(json_files)} JSON files to migrate")
        
        results = {
            "total_files": len(json_files),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "migrated_sessions": [],
            "failed_sessions": []
        }
        
        for json_file in json_files:
            session_id = self.extract_session_id(json_file)
            success = self.migrate_json_file(json_file)
            
            if success:
                results["successful_migrations"] += 1
                results["migrated_sessions"].append(session_id)
                logger.info(f"✅ Successfully migrated: {session_id}")
            else:
                results["failed_migrations"] += 1
                results["failed_sessions"].append(session_id)
                logger.error(f"❌ Failed to migrate: {session_id}")
        
        # Cleanup old files if requested
        if cleanup_old and results["failed_migrations"] == 0:
            logger.info("Cleaning up old JSON files...")
            for json_file in json_files:
                try:
                    json_file.unlink()
                    logger.info(f"  - Removed: {json_file}")
                except Exception as e:
                    logger.error(f"  - Failed to remove {json_file}: {e}")
        
        # Generate migration report
        self._generate_migration_report(results)
        
        return results
    
    def _generate_migration_report(self, results: Dict[str, Any]) -> None:
        """Generate a detailed migration report"""
        report_file = self.base_dir / "migration_report.json"
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "summary": {
                "total_files": results["total_files"],
                "successful_migrations": results["successful_migrations"],
                "failed_migrations": results["failed_migrations"],
                "success_rate": f"{(results['successful_migrations'] / results['total_files'] * 100):.1f}%" if results["total_files"] > 0 else "0%"
            },
            "migrated_sessions": results["migrated_sessions"],
            "failed_sessions": results["failed_sessions"],
            "new_structure": {
                "description": "File-based UI code storage",
                "structure": {
                    "session_id/": {
                        "index.html": "HTML content",
                        "style.css": "Component-specific CSS",
                        "globals.css": "Global CSS styles",
                        "metadata.json": "Session metadata",
                        "history.json": "Modification history"
                    }
                }
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Migration report saved to: {report_file}")
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify that all migrated sessions are valid"""
        logger.info("Verifying migration...")
        
        verification_results = {
            "total_sessions": 0,
            "valid_sessions": 0,
            "invalid_sessions": 0,
            "issues": []
        }
        
        # Check all session directories
        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                session_id = session_dir.name
                verification_results["total_sessions"] += 1
                
                # Check required files
                required_files = ["index.html", "style.css", "globals.css", "metadata.json", "history.json"]
                missing_files = []
                
                for file_name in required_files:
                    if not (session_dir / file_name).exists():
                        missing_files.append(file_name)
                
                if missing_files:
                    verification_results["invalid_sessions"] += 1
                    issue = f"Session {session_id}: Missing files - {', '.join(missing_files)}"
                    verification_results["issues"].append(issue)
                    logger.warning(f"❌ {issue}")
                else:
                    # Check file content validity
                    try:
                        html_content = (session_dir / "index.html").read_text(encoding='utf-8')
                        style_content = (session_dir / "style.css").read_text(encoding='utf-8')
                        
                        if len(html_content.strip()) > 50 and len(style_content.strip()) > 10:
                            verification_results["valid_sessions"] += 1
                            logger.info(f"✅ Session {session_id}: Valid")
                        else:
                            verification_results["invalid_sessions"] += 1
                            issue = f"Session {session_id}: Insufficient content"
                            verification_results["issues"].append(issue)
                            logger.warning(f"❌ {issue}")
                    except Exception as e:
                        verification_results["invalid_sessions"] += 1
                        issue = f"Session {session_id}: Error reading files - {e}"
                        verification_results["issues"].append(issue)
                        logger.error(f"❌ {issue}")
        
        logger.info(f"Verification complete: {verification_results['valid_sessions']}/{verification_results['total_sessions']} sessions valid")
        return verification_results

def main():
    """Main migration function"""
    print("=" * 60)
    print("UI Code Storage Migration: JSON to File-Based Structure")
    print("=" * 60)
    
    # Initialize migration manager
    migration_manager = UICodeMigrationManager()
    
    # Find JSON files
    json_files = migration_manager.find_json_files()
    print(f"\nFound {len(json_files)} JSON files to migrate:")
    for json_file in json_files:
        session_id = migration_manager.extract_session_id(json_file)
        print(f"  - {session_id} ({json_file.name})")
    
    if not json_files:
        print("\nNo JSON files found to migrate. Exiting.")
        return
    
    # Ask for confirmation
    response = input(f"\nProceed with migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    # Perform migration
    print("\nStarting migration...")
    results = migration_manager.migrate_all_files(cleanup_old=False)
    
    # Display results
    print("\n" + "=" * 60)
    print("MIGRATION RESULTS")
    print("=" * 60)
    print(f"Total files: {results['total_files']}")
    print(f"Successful: {results['successful_migrations']}")
    print(f"Failed: {results['failed_migrations']}")
    print(f"Success rate: {(results['successful_migrations'] / results['total_files'] * 100):.1f}%")
    
    if results['migrated_sessions']:
        print(f"\nSuccessfully migrated sessions:")
        for session_id in results['migrated_sessions']:
            print(f"  ✅ {session_id}")
    
    if results['failed_sessions']:
        print(f"\nFailed to migrate sessions:")
        for session_id in results['failed_sessions']:
            print(f"  ❌ {session_id}")
    
    # Verify migration
    print("\nVerifying migration...")
    verification = migration_manager.verify_migration()
    
    print(f"\nVerification results:")
    print(f"Total sessions: {verification['total_sessions']}")
    print(f"Valid sessions: {verification['valid_sessions']}")
    print(f"Invalid sessions: {verification['invalid_sessions']}")
    
    if verification['issues']:
        print(f"\nIssues found:")
        for issue in verification['issues']:
            print(f"  ⚠️  {issue}")
    
    # Ask about cleanup
    if results['failed_migrations'] == 0 and verification['invalid_sessions'] == 0:
        response = input(f"\nAll migrations successful! Remove old JSON files? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            print("Cleaning up old JSON files...")
            migration_manager.migrate_all_files(cleanup_old=True)
            print("Cleanup complete!")
    
    print("\nMigration process completed!")
    print("Check 'temp_ui_files/migration_report.json' for detailed report.")

if __name__ == "__main__":
    main() 