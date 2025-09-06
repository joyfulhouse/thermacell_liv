# Debug and Investigation Scripts  

Development debugging tools and issue investigation scripts used during the development process.

## Files

### Runtime Investigation
- `investigate_runtime_status.py` - System runtime discrepancy investigation
- `investigate_extended_runtime.py` - Extended runtime data analysis
- `investigate_total_runtime.py` - Total runtime vs session runtime analysis

### API Analysis
- `analyze_api_response.py` - API response structure analysis
- `fix_api_client.py` - API client implementation fixes

### Issue Fixes
- `test_status_fix.py` - System status display fix validation
- `test_device_model_fix.py` - Device model branding fix testing

## Historical Context

These scripts were created during development to:

1. **Runtime Investigation**: Resolve discrepancy between mobile app (3d 3h 24m) and API (11h 55m) runtime values
2. **Status Mapping**: Fix system status to show "Protected" instead of "On" when operational  
3. **Device Branding**: Change "thermacell-hub" to "Thermacell LIV Hub" display name
4. **API Response Analysis**: Understand ESP Rainmaker API response structure

## Usage

```bash
cd tests/debug

# Investigate runtime discrepancies
python investigate_runtime_status.py

# Analyze API responses
python analyze_api_response.py  

# Test specific fixes
python test_status_fix.py
python test_device_model_fix.py
```

## Development Notes

- These scripts represent the debugging process and solutions found
- Many issues investigated here were resolved in the main codebase
- Files kept for reference and future debugging needs
- Some scripts may require specific device states or conditions

## Resolved Issues

✅ **System Status**: Fixed "On" → "Protected" display
✅ **Runtime Values**: Understood API session vs lifetime runtime  
✅ **Device Model**: Fixed branding display name
✅ **API Structure**: Mapped ESP Rainmaker response format

## Archive

Scripts that are no longer actively needed but kept for historical reference should be moved to `/tests/archive/`.