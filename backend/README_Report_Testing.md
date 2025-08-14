# Report Generation Testing Script

This comprehensive testing script allows you to test the report generation system with full control over every aspect of the process, including session IDs, content, metadata, and report options.

## Features

- **Session Management**: Create, test, and clean up test sessions
- **Content Control**: Define custom HTML, CSS, and metadata
- **Report Options**: Control which sections appear in generated reports
- **Comprehensive Testing**: Run full test scenarios from configuration files
- **Validation**: Basic validation of generated reports
- **CLI Interface**: Easy-to-use command-line interface

## Quick Start

### 1. List Available Sessions
```bash
python test_report_generation.py --list-sessions
```

### 2. Create a Test Session
```bash
# Create with default content
python test_report_generation.py --create-session my_test_session

# Create with custom HTML/CSS files
python test_report_generation.py --create-session my_test_session \
  --html-file path/to/my_ui.html \
  --css-file path/to/my_style.css \
  --template-name "My Custom Template" \
  --template-category "web-app"
```

### 3. Test Report Generation
```bash
# Test with default options
python test_report_generation.py --test-session my_test_session

# Test with custom report options
python test_report_generation.py --test-session my_test_session \
  --report-options '{"uiPreview": true, "uiCode": false, "changesMade": true}' \
  --project-info '{"template_name": "Custom Template", "author": "Test User"}'
```

### 4. Run Comprehensive Test
```bash
python test_report_generation.py --comprehensive-test test_config_example.json
```

### 5. Clean Up
```bash
python test_report_generation.py --cleanup-session my_test_session
```

## Command Line Options

### Action Arguments
- `--list-sessions`: List all available sessions
- `--create-session SESSION_ID`: Create a new test session
- `--test-session SESSION_ID`: Test report generation for a session
- `--comprehensive-test CONFIG_FILE`: Run comprehensive test from config file
- `--cleanup-session SESSION_ID`: Clean up a test session

### Content Arguments
- `--html-file PATH`: Path to HTML file for session content
- `--css-file PATH`: Path to CSS file for session content
- `--globals-css-file PATH`: Path to global CSS file
- `--screenshot PATH`: Path to screenshot file

### Metadata Arguments
- `--template-name NAME`: Template name for the session
- `--template-category CATEGORY`: Template category
- `--metadata JSON_STRING`: Custom metadata as JSON string

### Report Options
- `--generate`: Generate report after testing
- `--report-options JSON_STRING`: Report options as JSON string
- `--project-info JSON_STRING`: Project info as JSON string

### Utility Arguments
- `--session-info SESSION_ID`: Get detailed info about a session
- `--verbose, -v`: Enable verbose output

## Configuration File Format

The comprehensive test configuration file allows you to define all aspects of a test:

```json
{
  "session_id": "comprehensive_test_session",
  "template_name": "Advanced Test Template",
  "template_category": "e-commerce",
  
  "html_content": "<!DOCTYPE html>...",
  "css_content": ".app { ... }",
  "globals_css": "* { ... }",
  
  "metadata": {
    "author": "Test Developer",
    "version": "2.0.0",
    "description": "Test template description"
  },
  
  "history": [
    {
      "timestamp": "2025-01-15T10:00:00.000Z",
      "modification": "Initial creation",
      "user": "Test User"
    }
  ],
  
  "screenshot_path": "path/to/screenshot.png",
  
  "report_options": {
    "uiDescription": true,
    "uiTags": true,
    "uiPreview": true,
    "uiCode": true,
    "changesMade": true,
    "creationDate": true,
    "logoAnalysis": false
  },
  
  "project_info": {
    "template_name": "Template Name",
    "category": "Category",
    "description": "Description",
    "author": "Author"
  }
}
```

## Report Options

The following options control what appears in generated reports:

- **uiDescription**: Include UI description section
- **uiTags**: Include UI tags section
- **uiPreview**: Include UI preview/screenshot
- **uiCode**: Include HTML/CSS code sections
- **changesMade**: Include modification history
- **creationDate**: Include creation date information
- **logoAnalysis**: Include logo analysis (if available)

## Examples

### Example 1: Basic Testing
```bash
# Create a simple test session
python test_report_generation.py --create-session basic_test

# Test report generation
python test_report_generation.py --test-session basic_test

# Clean up
python test_report_generation.py --cleanup-session basic_test
```

### Example 2: Custom Content Testing
```bash
# Create session with custom files
python test_report_generation.py --create-session custom_test \
  --html-file my_ui.html \
  --css-file my_style.css \
  --template-name "My Custom UI" \
  --template-category "dashboard"

# Test with specific report options
python test_report_generation.py --test-session custom_test \
  --report-options '{"uiPreview": true, "uiCode": true, "changesMade": false}'
```

### Example 3: Comprehensive Testing
```bash
# Run comprehensive test from config
python test_report_generation.py --comprehensive-test my_test_config.json
```

### Example 4: JSON Parameters
```bash
# Test with custom metadata and project info
python test_report_generation.py --test-session test_session \
  --metadata '{"author": "John Doe", "priority": "high"}' \
  --project-info '{"client": "Test Corp", "budget": "$5000"}' \
  --report-options '{"uiPreview": true, "uiCode": false}'
```

## Session Information

### View Session Details
```bash
python test_report_generation.py --session-info my_session
```

### List All Sessions
```bash
python test_report_generation.py --list-sessions
```

## File Structure

The testing script creates and manages the following structure:

```
backend/
├── temp_ui_files/
│   └── {session_id}/
│       ├── index.html
│       ├── style.css
│       ├── globals.css
│       ├── metadata.json
│       └── history.json
├── temp_previews/
│   └── {session_id}/
│       └── screenshot_{timestamp}.png
└── reports/
    └── UI_Mockup_Report_{session_id}_{timestamp}.pdf
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the backend directory
2. **File Not Found**: Check that all referenced files exist
3. **JSON Parse Errors**: Validate JSON syntax in arguments
4. **Permission Errors**: Ensure write permissions for temp directories

### Verbose Mode
Use the `--verbose` flag for detailed error information:
```bash
python test_report_generation.py --verbose --test-session my_session
```

### Session Cleanup
If a test fails, clean up the session to avoid conflicts:
```bash
python test_report_generation.py --cleanup-session failed_session
```

## Advanced Usage

### Custom Test Scenarios
Create multiple test configurations for different scenarios:
```bash
# Test minimal report
python test_report_generation.py --test-session my_session \
  --report-options '{"uiPreview": true, "uiCode": false, "changesMade": false}'

# Test full report
python test_report_generation.py --test-session my_session \
  --report-options '{"uiPreview": true, "uiCode": true, "changesMade": true}'
```

### Batch Testing
Create a script to test multiple sessions:
```bash
#!/bin/bash
sessions=("session1" "session2" "session3")

for session in "${sessions[@]}"; do
    echo "Testing session: $session"
    python test_report_generation.py --test-session "$session"
done
```

### Integration with CI/CD
The script can be integrated into continuous integration pipelines:
```yaml
# Example GitHub Actions step
- name: Test Report Generation
  run: |
    cd backend
    python test_report_generation.py --comprehensive-test test_config.json
```

## Dependencies

The testing script requires:
- Python 3.7+
- Access to the report generation modules
- Write permissions for temp directories
- Valid session data structure

## Support

For issues or questions:
1. Check the verbose output with `--verbose`
2. Verify session data structure
3. Ensure all dependencies are available
4. Check file permissions and paths

