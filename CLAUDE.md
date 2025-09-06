# Thermacell LIV Home Assistant Custom Component

## Overview
This is a Home Assistant custom component for integrating Thermacell LIV mosquito repellers. The integration provides control and monitoring capabilities for multiple Thermacell LIV devices through their cloud API.

## Component Structure

### Domain: `thermacell_liv`

### API Configuration
- **Base URL**: `https://api.iot.thermacell.com/`
- **Authentication**: Username/Password
- **Communication**: Cloud polling (iot_class: cloud_polling)

### Supported Platforms
Each Thermacell LIV hub supports the following entities:

1. **Switch** (`switch.py`)
   - Controls the on/off state of the mosquito repeller
   - Entity ID format: `switch.thermacell_liv_{device_name}`

2. **Light** (`light.py`) 
   - Controls the color LED on the device
   - Supports RGB color control
   - Entity ID format: `light.thermacell_liv_{device_name}_led`

3. **Sensor** (`sensor.py`)
   - Monitors refill life remaining (in hours)
   - Device class: Duration
   - Unit: hours
   - Entity ID format: `sensor.thermacell_liv_{device_name}_refill_life`

4. **Button** (`button.py`)
   - Resets the refill life counter
   - Entity ID format: `button.thermacell_liv_{device_name}_reset_refill`

### Multi-Device Support
- Single integration instance can manage multiple Thermacell LIV hubs
- Each hub creates its own set of entities (switch, light, sensor, button)
- Entities are uniquely identified by device ID

### Files Structure
```
thermacell_liv/
├── __init__.py           # Component setup and platform loading
├── config_flow.py        # Configuration flow for setup
├── const.py             # Constants and configuration keys
├── switch.py            # Switch platform for on/off control
├── light.py             # Light platform for LED control
├── sensor.py            # Sensor platform for refill monitoring
├── button.py            # Button platform for refill reset
├── manifest.json        # Component metadata
└── CLAUDE.md           # This specification file
```

## Development Tasks

### ✅ Completed Tasks
1. **API Client Implementation** ✅
   - ✅ Created `api.py` with ThermacellLivAPI class
   - ✅ Implemented ESP Rainmaker authentication flow
   - ✅ Added device discovery via `/user/nodes` endpoint
   - ✅ Implemented retry logic and error handling

2. **Data Coordinator** ✅
   - ✅ Created `coordinator.py` with ThermacellLivCoordinator
   - ✅ Implemented efficient polling with 60-second intervals
   - ✅ Added support for multiple devices per integration
   - ✅ Included local cache updates for immediate UI feedback

3. **Entity Implementation** ✅
   - ✅ Completed all entity classes with API integration
   - ✅ Added proper device info and entity grouping
   - ✅ Implemented CoordinatorEntity pattern
   - ✅ Added availability checks based on node status

4. **Configuration** ✅
   - ✅ Enhanced config flow with real authentication validation
   - ✅ Implemented connection testing
   - ✅ Updated manifest.json with aiohttp dependency

### Remaining Tasks

### Testing Requirements
- Unit tests for all entity types
- Integration tests with mock API  
- Configuration flow testing
- Multi-device scenarios
- ESP Rainmaker API endpoint validation

### Next Development Phase
1. **API Endpoint Validation**
   - Test actual ESP Rainmaker API endpoints with Thermacell devices
   - Validate parameter names and data structures
   - Confirm authentication flow with real credentials

2. **Enhanced Features**
   - Add options flow for polling interval configuration
   - Implement device offline detection and recovery
   - Add diagnostic sensors (signal strength, battery level)

3. **Production Readiness**
   - Add comprehensive error handling for network issues
   - Implement proper logging levels
   - Add user-friendly error messages

## API Integration Notes
- The component uses the Thermacell IoT API at `https://api.iot.thermacell.com/`
- Authentication uses username/password credentials
- Device communication is cloud-based (requires internet connectivity)
- Polling interval should be configurable but default to reasonable rate limits

## Code Owner
- **@btli** - Primary maintainer and code owner