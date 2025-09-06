# Integration Tests

Tests that validate the integration with real Thermacell LIV devices and API endpoints.

## Files

### API Validation
- `test_real_api.py` - Basic API connectivity and authentication
- `test_fixed_api.py` - API client implementation validation
- `validate_api.py` - Comprehensive API endpoint testing  
- `final_api_validation.py` - Complete integration validation

### Device Information
- `test_device_info.py` - Device info parsing and display
- `test_device_info_complete.py` - Complete device information testing
- `test_detailed_status.py` - Device status and state testing
- `test_node_details.py` - Node discovery and details

### System Status
- `test_system_status.py` - System status mapping and display

## Requirements

All integration tests require:
1. Valid Thermacell account credentials in `secrets.py`:
   ```python
   THERMACELL_USERNAME = "your_email@example.com"
   THERMACELL_PASSWORD = "your_password"  
   THERMACELL_API_BASE_URL = "https://api.iot.thermacell.com"
   ```

2. Active Thermacell LIV device(s) associated with the account
3. Internet connectivity to reach Thermacell API servers

## Usage

```bash
cd tests/integration

# Test basic API connectivity
python test_real_api.py

# Validate all API endpoints
python validate_api.py

# Test device information parsing
python test_device_info_complete.py
```

⚠️ **Note**: These tests make real API calls and may affect your actual devices. Use with caution in production environments.