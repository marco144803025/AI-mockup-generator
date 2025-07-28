# Testing Suite

This directory contains simple test scripts to verify the functionality of your AI Mockup system.

## Test Files

### Individual Tests

1. **`test_numpy.py`** - Tests if numpy and numpy.random work correctly
2. **`test_autogen_import.py`** - Tests if AutoGen can be imported without errors
3. **`test_base_agent.py`** - Tests if the base agent can be imported and initialized
4. **`test_claude_api.py`** - Tests if the Claude API key is available and accessible
5. **`test_fastapi_server.py`** - Tests if the FastAPI server can start and respond

### Master Test

- **`run_all_tests.py`** - Runs all individual tests and provides a summary

## How to Run Tests

### Run All Tests
```bash
cd tests
python run_all_tests.py
```

### Run Individual Tests
```bash
cd tests
python test_numpy.py
python test_autogen_import.py
python test_base_agent.py
python test_claude_api.py
python test_fastapi_server.py
```

### Run Tests from Project Root
```bash
python tests/run_all_tests.py
python tests/test_numpy.py
```

## Prerequisites

1. **Virtual Environment**: Make sure you're in the backend virtual environment
2. **Dependencies**: All required packages should be installed
3. **Environment Variables**: `.env` file should be configured with `CLAUDE_API_KEY`

## Test Results

- **✓** = Test passed
- **✗** = Test failed
- **⚠** = Warning (test couldn't run but system might still work)

## Troubleshooting

If tests fail:

1. **Activate virtual environment**: `cd backend && venv\Scripts\activate`
2. **Check dependencies**: `pip list`
3. **Verify environment variables**: Check `.env` file
4. **Check server status**: For FastAPI tests, ensure server is running

## Notes

- These are **simple diagnostic tests** - they don't test complex functionality
- Tests are designed to be **fast and non-destructive**
- Some tests require the server to be running (FastAPI tests)
- Tests will show helpful error messages to guide troubleshooting 