# Release Notes

## Version 0.0.2 - Entity Naming & Display Improvements

### 🔧 Breaking Changes
- **Entity ID Format**: All entity IDs now include proper domain prefix
  - **Before**: `switch.adu_adu`, `light.adu_adu_led`
  - **After**: `switch.thermacell_liv_adu_switch`, `light.thermacell_liv_adu_led`
  - **Action Required**: You may need to update automations, scripts, and dashboards that reference the old entity IDs

### ✨ Improvements
- **Professional Display Names**: Entities now show clean, user-friendly names in the Home Assistant interface
  - Switch: "ADU" (main device entity)
  - Light: "ADU LED"
  - Sensors: "ADU Refill Life", "ADU System Status", "ADU System Runtime"
  - Button: "ADU Reset Refill"

- **Consistent Entity ID Structure**: All entities follow the standard Home Assistant naming convention
  - Format: `{platform}.{DOMAIN}_{device_name}_{entity_type}`
  - Examples:
    - `switch.thermacell_liv_adu_switch`
    - `light.thermacell_liv_adu_led`
    - `sensor.thermacell_liv_adu_refill_life`
    - `sensor.thermacell_liv_adu_system_status`
    - `sensor.thermacell_liv_adu_system_runtime`
    - `button.thermacell_liv_adu_reset_refill`

- **Home Assistant Naming Standards**: Implemented proper `has_entity_name` pattern for automatic friendly name generation

### 🔄 Migration Guide
If you're upgrading from version 0.0.1, you'll need to update any references to the old entity IDs:

**Old Entity IDs → New Entity IDs:**
```yaml
# Old automation example
- service: switch.turn_on
  target:
    entity_id: switch.adu_adu  # ❌ Old

# New automation example  
- service: switch.turn_on
  target:
    entity_id: switch.thermacell_liv_adu_switch  # ✅ New
```

**Dashboard Cards:**
- Update entity references in Lovelace cards
- Display names will automatically show the improved friendly names

### 📋 Complete Entity Reference
For a device named "ADU":

| Entity Type | Entity ID | Display Name |
|-------------|-----------|--------------|
| Switch | `switch.thermacell_liv_adu_switch` | "ADU" |
| Light | `light.thermacell_liv_adu_led` | "ADU LED" |
| Refill Sensor | `sensor.thermacell_liv_adu_refill_life` | "ADU Refill Life" |
| Status Sensor | `sensor.thermacell_liv_adu_system_status` | "ADU System Status" |
| Runtime Sensor | `sensor.thermacell_liv_adu_system_runtime` | "ADU System Runtime" |
| Reset Button | `button.thermacell_liv_adu_reset_refill` | "ADU Reset Refill" |

---

## Version 0.0.1 - Initial Release

### 🎉 Features
- **Production-ready** Home Assistant custom component for Thermacell LIV mosquito repellers
- **Optimistic state updates** for instant UI responsiveness (24x faster perceived response)
- **Multi-device support** - Single integration manages multiple hubs
- **Comprehensive control**:
  - Switch: On/off control for mosquito repeller
  - Light: RGB color and brightness control for LED
  - Sensors: Refill life monitoring, system status, runtime tracking
  - Button: Refill life reset functionality
- **Real-time monitoring** with 60-second polling intervals
- **HACS compatible** for easy installation
- **Robust error handling** with automatic re-authentication