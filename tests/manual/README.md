# Manual Tests

Interactive test scripts that require manual execution and observation of device behavior.

## Files

### LED Control Tests
- `test_led_brightness.py` - LED brightness control testing
- `test_brightness_simple.py` - Simple brightness adjustment test
- `test_brightness_final.py` - Comprehensive brightness testing
- `test_led_state_management.py` - LED power state logic testing

### Device Control Tests  
- `test_repeller_control.py` - Repeller on/off control testing
- `test_repeller_final.py` - Complete repeller functionality test
- `test_set_params_methods.py` - Parameter setting methods testing

### User Experience Tests
- `test_optimistic_updates.py` - Optimistic state updates demonstration
  - Shows 24x responsiveness improvement
  - Demonstrates instant UI feedback
  - Measures API call timing vs perceived response

## Requirements

Manual tests require:
1. Valid Thermacell credentials in `secrets.py`
2. Active Thermacell LIV device for testing
3. Physical observation of device LED changes
4. Network connectivity for API calls

## Usage

```bash
cd tests/manual

# Test optimistic updates (recommended first)
python test_optimistic_updates.py

# Test LED brightness control
python test_led_brightness.py

# Test device power control
python test_repeller_final.py
```

## Expected Behavior

### LED Tests
- Observe physical LED color and brightness changes
- Verify UI updates happen instantly (optimistic)
- Confirm API calls succeed in background

### Repeller Tests  
- Watch device power indicator changes
- Listen for operational sounds
- Check mobile app reflects same state

### Optimistic Updates Demo
- Shows timing comparison (before/after optimization)
- Demonstrates instant vs delayed UI feedback
- Measures performance improvements

⚠️ **Warning**: These tests will actively control your Thermacell device. Ensure you're comfortable with the device changing states during testing.