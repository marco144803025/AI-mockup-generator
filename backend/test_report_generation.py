#!/usr/bin/env python3
"""
Simple Report Generation Testing Script

One function to test the report generation service with all parameters.
No defaults, no error handling - you'll see exactly what fails.
"""

import os
import sys

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.report_generator import ReportGenerator


def test_report_generation(
    session_id: str,
    report_options: dict,
    project_info: dict
):
    """
    Test report generation with the given parameters.
    
    Args:
        session_id: The session ID to test
            Sample: "test_session", "my_project_123", "user_abc_session"
            Must be an existing session ID from temp_ui_files/
        
        report_options: Report generation options
            Sample: {
                "uiDescription": True,      # Include UI description section
                "uiTags": True,             # Include UI tags section  
                "uiPreview": True,          # Include UI preview/screenshot
                "uiCode": True,             # Include HTML/CSS code sections
                "changesMade": True,        # Include modification history
                "creationDate": True,       # Include creation date info
                "logoAnalysis": False       # Include logo analysis (if available)
            }
            All values must be boolean (True/False)
        
        project_info: Project information
            Sample: {
                "template_name": "My Template",           # Name of the template
                "category": "web-app",                    # Template category
                "description": "Project description",     # Project description
                "author": "Marco Cheng",                     # Author name
                "version": "1.0.0",                       # Version number
                "client": "Client Corp",                  # Client name
                "budget": "$5000",                        # Project budget
                "deadline": "2025-02-15"                 # Project deadline
            }
            All fields are optional except template_name and category
    
    Returns:
        The path to the generated PDF report
    """
    generator = ReportGenerator()
    pdf_path = generator.generate(
        session_id=session_id,
        report_options=report_options,
        project_info=project_info
    )
    return pdf_path


if __name__ == "__main__":
    # Example usage - modify these values as needed
    
    # SAMPLE SESSION IDs (must exist in temp_ui_files/):
    # session_id = "test_session"                    # Basic test session
    # session_id = "bc9ea517-024c-461b-b78a-fd414d58e701"  # Real session from your system
    # session_id = "eb8ea5c4-6da6-4b12-8cae-ccf2db3594c8"  # Another real session
    session_id = "mgoe1575b6-8b54-4dff-854b-b4ab3bbb4c00"
    
    # SAMPLE REPORT OPTIONS (all boolean values):
    # Minimal report: only preview and creation date
    # report_options = {
    #     "uiDescription": False,
    #     "uiTags": False,
    #     "uiPreview": True,
    #     "uiCode": False,
    #     "changesMade": False,
    #     "creationDate": True,
    #     "logoAnalysis": False
    # }
    
    # Full report: everything enabled
    report_options = {
        "uiDescription": True,
        "uiTags": True,
        "uiPreview": True,
        "uiCode": True,
        "changesMade": True,
        "creationDate": True,
        "logoAnalysis": False,
        "agentRationale": True
    }
    
    # SAMPLE PROJECT INFO (template_name and category are required):
    # Basic project info
    # project_info = {
    #     "template_name": "My Web App",
    #     "category": "web-application"
    # }
    
    # Detailed project info
    project_info = {
        "template_name": "Profile 4",
        "category": "Profile",
        "description": "",
        "author": ""
    }
    
    try:
        pdf_path = test_report_generation(session_id, report_options, project_info)
        print(f"Report generated: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
