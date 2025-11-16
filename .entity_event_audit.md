# Entity Event Subscription Audit

**Date:** 2025-11-13
**Requirement:** Bronze tier - entity-event-setup
**Status:** ✅ COMPLIANT

## Audit Summary

All entities in the Thermacell LIV integration use the proper CoordinatorEntity pattern from Home Assistant core. No manual event subscriptions are used.

## Files Audited

### Entity Platforms
- `switch.py` - ✅ No manual event subscriptions
- `light.py` - ✅ No manual event subscriptions
- `sensor.py` - ✅ No manual event subscriptions
- `button.py` - ✅ No manual event subscriptions

### Core Integration
- `__init__.py` - ✅ No manual event subscriptions (uses entry.add_update_listener for options)
- `coordinator.py` - ✅ No manual event subscriptions
- `config_flow.py` - ✅ No manual event subscriptions

## Event Subscription Pattern

All entities inherit from `CoordinatorEntity[ThermacellLivCoordinator]` which:
1. Automatically subscribes to coordinator updates when entity is added
2. Automatically unsubscribes when entity is removed
3. Only triggers updates when coordinator data changes
4. No unnecessary event listeners or manual subscriptions

## Options Update Listener

The only event-like subscription is in `__init__.py`:
```python
entry.async_on_unload(entry.add_update_listener(async_reload_entry))
```

This is the **recommended Home Assistant pattern** for handling options flow updates and is properly cleaned up on unload.

## Conclusion

✅ **COMPLIANT** - No unnecessary event subscriptions found. All entities use the recommended CoordinatorEntity pattern.
