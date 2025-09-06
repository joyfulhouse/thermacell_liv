# Thermacell LIV Tests

This directory contains all test files for the Thermacell LIV integration, organized by type and purpose.

## Directory Structure

### `/integration/` - Integration Tests
- API validation tests
- Real device integration tests  
- Device info and status tests
- Files that test actual API endpoints with real credentials

### `/manual/` - Manual Testing Scripts
- Interactive test scripts requiring manual execution
- LED control and brightness testing
- Repeller functionality tests
- Optimistic updates demonstration

### `/debug/` - Debug and Investigation Scripts
- Development debugging tools
- Issue investigation scripts
- Fix validation scripts
- Historical debugging sessions

### `/archive/` - Archived Tests
- Deprecated test files
- Old versions kept for reference
- Tests that are no longer actively used

### Root Level - Unit Tests
- `test_api.py` - API client unit tests
- `test_coordinator.py` - Data coordinator unit tests  
- `test_entities.py` - Entity implementation unit tests
- `__init__.py` - Test package initialization

## Running Tests

### Unit Tests (Automated)
```bash
# Run all unit tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=. tests/
```

### Integration Tests (Require Credentials)
```bash
# Run API integration tests (requires secrets.py)
cd tests/integration
python test_real_api.py
python validate_api.py
```

### Manual Tests (Interactive)
```bash
# Test LED controls
cd tests/manual  
python test_led_brightness.py
python test_optimistic_updates.py
```

### Debug Scripts
```bash
# Investigation and debugging
cd tests/debug
python investigate_runtime_status.py
python analyze_api_response.py
```

## Test Dependencies

- Unit tests: No external dependencies
- Integration tests: Require valid Thermacell credentials in `secrets.py`
- Manual tests: Require active Thermacell LIV device and network access
- Debug scripts: May require additional development tools