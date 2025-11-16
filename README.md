# <img src="logo_2025.webp" alt="Thermacell" width="200" height="60"> LIV Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![HACS][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

![Quality Scale](https://img.shields.io/badge/Quality%20Scale-Silver%20100%25-success?style=flat-square)
![Quality Scale](https://img.shields.io/badge/Overall-71%25%20(39%2F55)-blue?style=flat-square)

A powerful 🏠 Home Assistant integration for controlling and monitoring 🦟 Thermacell LIV mosquito repellers through their cloud API.

### 🏆 Quality Scale Achievement

This integration adheres to [Home Assistant's Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/):
- ✅ **Silver Tier**: 100% COMPLETE (10/10 rules) - Production ready
- 🟡 **Bronze Tier**: 84% (16/19 rules) - Strong foundation
- 🟡 **Gold Tier**: 57% (13/23 rules) - Advanced features implemented
- 🟡 **Platinum Tier**: 67% (2/3 rules) - Type-safe with strict typing
- 📊 **Overall Compliance**: 71% (39/55 rules)

**Key Quality Features:**
- Type-safe codebase with mypy strict mode
- Comprehensive repair flows for common issues
- Full diagnostic data export with sensitive data redaction
- Reauthentication without integration removal
- Runtime-configurable polling interval (30-300s)
- Optimistic updates for instant UI responsiveness

## 🎉 Version 1.0.0 - Production Ready!

This release marks the first stable production version with significant improvements:
- ✅ **Optimized Performance**: Removed excessive Last Polled sensor entries from logbook
- ✅ **Enhanced Code Quality**: Pylint score improved to 9.56/10 with professional standards
- ✅ **Production Stability**: All critical bugs resolved and comprehensive testing completed
- ✅ **Clean Codebase**: Proper formatting, linting compliance, and documentation

## ✨ Features

- 🎛️ **Control mosquito repellers**: Turn your Thermacell LIV devices on and off
- 💡 **LED color control**: Customize the LED color and brightness on your devices
- ⏱️ **Monitor refill life**: Track remaining refill life in hours
- 🔄 **Refill reset**: Reset the refill life counter when replacing cartridges
- 🏘️ **Multi-device support**: Manage multiple Thermacell LIV hubs from a single integration
- 📡 **Real-time status**: Monitor device connectivity and online status
- ⏰ **System runtime**: Track how long your devices have been running
- 📊 **System status**: Monitor current state (On, Off, Warming Up, Protected)
- 🔧 **Device information**: View firmware version, serial number, and model details
- 🔄 **Reauthentication**: Update credentials without removing integration
- ⚙️ **Configurable polling**: Adjust update interval (30-300 seconds)
- 🩺 **Diagnostics**: Comprehensive debug data for troubleshooting

## 🏠 Supported Entities

Each Thermacell LIV hub provides the following Home Assistant entities:

### Primary Entities (Enabled by Default)
- 🔌 **Switch**: `switch.thermacell_liv_{device_name}` - Controls the mosquito repeller on/off
- 💡 **Light**: `light.thermacell_liv_{device_name}_led` - Controls LED color and brightness
- ⏱️ **Refill Life Sensor**: `sensor.thermacell_liv_{device_name}_refill_life` - Monitors refill life remaining (%)
- 📊 **System Status Sensor**: `sensor.thermacell_liv_{device_name}_system_status` - Current device status
- 🔄 **Reset Button**: `button.thermacell_liv_{device_name}_reset_refill` - Resets refill life counter

### Diagnostic Entities (Disabled by Default)
These can be enabled via Settings → Devices & Services → Thermacell LIV → Entity Settings:
- ⏰ **System Runtime Sensor**: Total runtime (formatted as days/hours/minutes)
- 📡 **Connectivity Sensor**: Connection status (Connected/Disconnected)
- ⚠️ **Error Code Sensor**: Numeric error codes with status attributes
- 🆔 **Hub ID Sensor**: Device serial number for identification
- 💾 **Firmware Version Sensor**: Current firmware version
- 🔄 **Refresh Button**: Manual data refresh from API

## 🦟 Supported Devices

This integration supports all **Thermacell LIV** mosquito repeller hubs with the following specifications:

### Compatible Models
- ✅ **Thermacell LIV Hub** (Model: thermacell-hub)
  - Cloud-connected mosquito repeller
  - RGB LED indicator
  - WiFi connectivity (2.4GHz)
  - Refillable cartridge system

### Firmware Compatibility
- ✅ **Tested Versions**: 5.3.2 and later
- ✅ **Minimum Version**: Any firmware supporting ESP Rainmaker API v1
- ⚠️ **Note**: Older firmware may lack some features

### Regional Availability
- 🌍 Available in regions where Thermacell LIV is sold
- 🇺🇸 United States
- 🇨🇦 Canada
- 🌐 Check [Thermacell's website](https://www.thermacell.com/) for current availability

### Incompatible Devices
- ❌ Thermacell Patio Shield (non-WiFi model)
- ❌ Thermacell E-Series (different protocol)
- ❌ Thermacell Radius (different app/API)

## 🎯 Use Cases

### 🏡 Home & Patio
- **Outdoor dining**: Automatically enable repeller at sunset for mosquito-free meals
- **Evening relaxation**: Schedule protection during peak mosquito hours (dusk to dawn)
- **Party mode**: Link LED color to scene changes for ambiance

### 🏕️ Events & Gatherings
- **Outdoor parties**: Coordinate multiple hubs for large area coverage
- **Camping**: Remote monitoring and control from inside
- **BBQ automation**: Trigger with outdoor cooking automations

### 🏠 Smart Home Integration
- **Presence detection**: Auto-enable when outdoor motion detected
- **Weather integration**: Disable during rain, enable when weather clears
- **Solar automation**: Enable at sunset, disable at sunrise
- **Energy management**: Monitor runtime for refill planning

### 🔧 Maintenance
- **Refill tracking**: Get notifications when refill life is low
- **Usage analytics**: Track runtime patterns to optimize placement
- **Diagnostics**: Troubleshoot connectivity issues with diagnostic sensors

## 📦 Installation

### Method 1: 🛒 HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=joyfulhouse&repository=thermacell_liv&category=integration)

1. 🎯 **Open HACS** in your Home Assistant instance
2. 📚 Go to **Integrations** 
3. 🎛️ Click the **three dots menu** (⋮) in the top right corner
4. 🔗 Select **Custom repositories**
5. 📝 Add repository URL: `https://github.com/joyfulhouse/thermacell_liv`
6. 📂 Select **Integration** as the category  
7. ➕ Click **Add**
8. 🔍 Search for "Thermacell LIV" and install
9. 🔄 **Restart Home Assistant**

### Method 2: 📁 Manual Installation

1. 📥 **Download the integration files**:
   ```bash
   cd /config/custom_components
   git clone https://github.com/joyfulhouse/thermacell_liv.git
   ```

2. 📁 **Create the custom_components directory** (if it doesn't exist):
   ```bash
   mkdir -p /config/custom_components
   ```

3. 📋 **Copy integration files**:
   ```bash
   cp -r thermacell_liv /config/custom_components/
   ```

4. 🔄 **Restart Home Assistant**

### Method 3: 📦 Direct Download

1. 📥 **Download the latest release** from [🏷️ GitHub Releases](https://github.com/joyfulhouse/thermacell_liv/releases)
2. 📂 **Extract the files** to your Home Assistant config directory:
   ```
   config/
   └── custom_components/
       └── thermacell_liv/
           ├── __init__.py
           ├── api.py
           ├── button.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── light.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           └── switch.py
   ```
3. 🔄 **Restart Home Assistant**

## ⚙️ Configuration

### 🔧 Adding the Integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=thermacell_liv)

1. 🎛️ **Go to Settings** → **Devices & Services**
2. ➕ **Click "Add Integration"**
3. 🔍 **Search for "Thermacell LIV"**
4. 🔐 **Enter your credentials**:
   - 👤 **Username**: Your Thermacell account username/email
   - 🔑 **Password**: Your Thermacell account password

### 📝 Configuration Parameters

#### Required Parameters

- **Username/Email** (string, required)
  - Your Thermacell account login credentials
  - The same email address you use for the Thermacell mobile app
  - Format: Valid email address (e.g., user@example.com)
  - Used for: API authentication and device discovery

- **Password** (string, required)
  - Your Thermacell account password
  - The same password you use for the Thermacell mobile app
  - Security: Stored encrypted in Home Assistant's secure storage
  - Used for: API authentication

#### Automatic Parameters

- **API Base URL**: `https://api.iot.thermacell.com/` (automatic)
  - ESP Rainmaker platform endpoint
  - Cannot be changed (hardcoded for reliability)
  - Protocol: HTTPS with TLS encryption

- **Polling Interval**: 60 seconds (configurable)
  - **Default**: 60 seconds - optimal balance for most use cases
  - **Configurable Range**: 30-300 seconds via Options
  - **Justification for 60s default**:
    - ✅ Responsive enough for typical mosquito repeller usage patterns
    - ✅ Respects Thermacell cloud API rate limits (no published limits, conservative approach)
    - ✅ Reduces unnecessary API calls (devices are AC-powered, state changes infrequent)
    - ✅ Optimistic updates provide instant UI feedback regardless of polling interval
  - **To change**: Settings → Devices & Services → Thermacell LIV → Configure → Scan Interval

- **Parallel Updates**: Platform-specific (automatic)
  - Switch/Light/Button: 1 concurrent operation (prevents API conflicts)
  - Sensors: Unlimited (read-only operations)
  - Purpose: Prevents overwhelming the Thermacell API

### 🔐 Authentication Setup

You'll need a Thermacell account with registered LIV devices. The integration uses the same credentials you use for the 📱 Thermacell mobile app.

#### Prerequisites

1. **Active Thermacell account**
   - 📝 Create at [Thermacell's website](https://www.thermacell.com/)
   - ✅ Verify your email address
   - 🔑 Remember your password

2. **Registered LIV device**
   - 📱 Download the Thermacell mobile app (iOS/Android)
   - 🔗 Follow the in-app setup wizard
   - 📡 Connect your LIV hub to WiFi
   - ✅ Verify device appears in the app

3. **Network requirements**
   - 🌐 Home Assistant must have internet access
   - 🔓 No firewall configuration needed (outbound HTTPS only)
   - ⚡ Stable internet connection recommended

#### Setup Steps

1. 📝 **Create an account** at [🌐 Thermacell's website](https://www.thermacell.com/) if you don't have one
2. 📱 **Register your LIV devices** using the Thermacell mobile app
3. 🏠 **Use the same credentials** in Home Assistant

### 🔄 Reauthentication

If your credentials change or expire:

1. Go to **Settings** → **Devices & Services**
2. Find **Thermacell LIV** integration
3. Click **Configure** (or notification prompt)
4. Enter your new username and password
5. Click **Submit** to update credentials

The integration will automatically reload with new credentials.

### 🗑️ Removing Devices

#### Remove a Specific Device
If you want to remove a specific Thermacell LIV device from Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Click on **Thermacell LIV** integration
3. Click on the **device** you want to remove (e.g., "Patio")
4. Click the **gear icon** (⚙️) in the top right
5. Click **Delete** and confirm

**Note:** The device will be automatically re-added on the next update if it's still in your Thermacell account. To permanently remove it, you must:
- Remove the device from your Thermacell account via the mobile app, OR
- Remove the entire integration (see below)

#### Remove the Integration
To completely remove the Thermacell LIV integration and all devices:

1. Go to **Settings** → **Devices & Services**
2. Find **Thermacell LIV** integration
3. Click the **three dots** (⋮) menu
4. Click **Delete**
5. Confirm the removal

All entities, devices, and configuration will be removed. You can re-add the integration anytime by following the installation steps.

#### What Gets Removed
When you delete the integration:
- ✅ All entities (switches, lights, sensors, buttons)
- ✅ All devices from the Devices page
- ✅ Integration configuration (credentials)
- ✅ Entity history (if you've enabled cleanup)
- ❌ Historical data in the database (preserved by default)

**To remove historical data:** Use the **Developer Tools** → **Statistics** page to delete entity statistics if needed.

## 🚀 Usage Examples

### 🤖 Automation Examples

**🌅 Turn on repellers at sunset**:
```yaml
automation:
  - alias: "Turn on Thermacell at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: switch.turn_on
      target:
        entity_id: switch.thermacell_liv_patio
```

**🌈 Change LED color based on time**:
```yaml
automation:
  - alias: "Thermacell LED Evening Color"
    trigger:
      platform: time
      at: "20:00:00"
    action:
      service: light.turn_on
      target:
        entity_id: light.thermacell_liv_patio_led
      data:
        rgb_color: [255, 100, 0]  # Orange
        brightness: 128
```

**⚠️ Low refill notification**:
```yaml
automation:
  - alias: "Thermacell Low Refill Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.thermacell_liv_patio_refill_life
      below: 24  # Less than 24 hours remaining
    action:
      service: notify.mobile_app_your_phone
      data:
        message: "Thermacell refill is running low ({{ states('sensor.thermacell_liv_patio_refill_life') }} hours remaining)"
```

### 📊 Lovelace Card Example

```yaml
type: entities
title: Thermacell LIV Control
entities:
  - entity: switch.thermacell_liv_patio
    name: Patio Repeller
  - entity: light.thermacell_liv_patio_led
    name: Patio LED
  - entity: sensor.thermacell_liv_patio_refill_life
    name: Refill Life
  - entity: button.thermacell_liv_patio_reset_refill
    name: Reset Refill
```

## 🔄 Data Updates & Polling

### How Data Refresh Works

The integration uses a **cloud polling** mechanism with intelligent optimistic updates:

1. **Initial Connection**: On startup, fetches all device data from Thermacell API
2. **Periodic Polling**: Updates device status every 60 seconds (configurable 30-300s)
3. **Optimistic Updates**: When you control a device:
   - UI updates instantly (0.01s response time)
   - API call happens in background (2.5s average)
   - Reverts if API call fails
4. **Manual Refresh**: Use the refresh button for immediate updates

### Update Intervals

- **Default**: 60 seconds (balanced performance)
- **Configurable**: 30-300 seconds via integration options
- **Faster updates**: Set to 30s for near real-time (may impact API limits)
- **Slower updates**: Set to 300s for reduced API calls

### Data Freshness

- **Device states**: Updated every poll interval
- **Refill life**: Real-time tracking
- **System status**: Live status (Protected, Warming Up, Off, Error)
- **Connectivity**: Immediate detection of offline devices

## ⚠️ Known Limitations

### API & Connectivity

- **Internet Required**: Integration requires constant internet access to Thermacell cloud
- **Cloud Dependency**: Cannot function if Thermacell API is down or unavailable
- **No Local Control**: Devices must communicate through Thermacell cloud (no local API)
- **Polling Delay**: Status updates limited by polling interval (default 60s)

### Device Limitations

- **Single Account**: Each integration instance supports one Thermacell account
- **2.4GHz WiFi Only**: LIV hubs require 2.4GHz WiFi (5GHz not supported by hardware)
- **Runtime Tracking**: Shows current session runtime, not lifetime usage
- **Refill Accuracy**: Refill life is estimated, not measured

### Platform Limitations

- **No Push Notifications**: Integration polls API, doesn't receive device push updates
- **Rate Limiting**: Excessive API calls may result in temporary throttling
- **Geofencing**: No automatic location-based control
- **Historical Data**: No built-in historical tracking (use HA recorder/history)

### Feature Limitations

- **LED Control**: Basic RGB, no effects or patterns (hardware limitation)
- **Scheduling**: No device-side schedules (use HA automations instead)
- **Multiple Zones**: Each hub is independent (no built-in zone grouping)
- **Battery Status**: LIV hub is AC-powered (no battery monitoring)

## 🔧 Troubleshooting

### ❗ Common Issues

**🔐 Authentication Failed**:
- ✅ Verify username/password are correct (same as mobile app)
- ✅ Ensure Thermacell account is active and verified
- ✅ Check that devices are registered in Thermacell mobile app
- ✅ Try reauthentication: Settings → Devices & Services → Thermacell LIV → Configure
- ❌ If persists: Reset password via Thermacell website, then reauth

**📱 No devices found**:
- ✅ Ensure LIV devices are powered on and LED is lit
- ✅ Verify devices are online in Thermacell mobile app
- ✅ Check WiFi connection (2.4GHz network required)
- ✅ Try manual refresh button
- ✅ Reload integration: Settings → Devices & Services → Thermacell LIV → "⋮" → Reload
- ❌ If persists: Remove and re-add integration

**🌐 Connection timeout**:
- ✅ Test internet connectivity from Home Assistant
- ✅ Verify API URL: `https://api.iot.thermacell.com/`
- ✅ Check firewall isn't blocking outbound HTTPS
- ✅ Review Home Assistant logs for detailed error messages
- ❌ If persists: Check Thermacell API status

**💡 LED not responding**:
- ✅ Verify hub is powered on (LED should be lit)
- ✅ Check if hub is online (connectivity sensor)
- ✅ Try controlling via mobile app (hardware test)
- ✅ Ensure brightness > 0 (LED off if brightness = 0)
- ❌ If hardware issue: Contact Thermacell support

**⏱️ Slow response times**:
- ✅ Check your internet speed and latency
- ✅ Increase polling interval if API seems slow
- ✅ Verify not hitting API rate limits (check logs)
- ✅ Optimistic updates provide instant UI feedback

**🔄 Entities unavailable**:
- ✅ Check device connectivity sensor status
- ✅ Verify device is online in mobile app
- ✅ Check Home Assistant logs for API errors
- ✅ Try manual refresh or reload integration
- ✅ Check credentials haven't expired (reauth if needed)

### 🐛 Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.thermacell_liv: debug
    custom_components.thermacell_liv.coordinator: debug
    custom_components.thermacell_liv.api: debug
```

This will log:
- API requests and responses
- Authentication attempts
- Node online/offline transitions
- Service call successes/failures
- Optimistic update operations

### 📊 Diagnostics

Download diagnostic data for support:

1. Go to **Settings** → **Devices & Services**
2. Click **Thermacell LIV** integration
3. Click **"⋮"** (three dots) → **Download Diagnostics**
4. Share the file when reporting issues (sensitive data is auto-redacted)

### 🆘 Getting Help

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/joyfulhouse/thermacell_liv/issues)
- **Discussions**: [Ask questions and share tips](https://github.com/joyfulhouse/thermacell_liv/discussions)
- **Logs**: Always include debug logs when reporting issues
- **Diagnostics**: Attach diagnostic file for faster troubleshooting

## 📝 Configuration Examples

### UI Configuration

#### Initial Setup
1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Thermacell LIV"
3. Enter your credentials:
   - **Username**: Your Thermacell account email
   - **Password**: Your Thermacell account password
4. Click **Submit**

#### Adjusting Polling Interval
1. Go to **Settings** → **Devices & Services**
2. Find **Thermacell LIV** integration
3. Click **Configure**
4. Adjust **Scan Interval** (30-300 seconds)
5. Click **Submit**

### Automation Examples

#### Automatic Patio Protection at Sunset

```yaml
automation:
  - alias: "Patio Protection - Start at Sunset"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"  # 30 minutes before sunset
    condition:
      - condition: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 60  # Only when warm enough for mosquitoes
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 128
          rgb_color: [255, 200, 100]  # Warm amber

  - alias: "Patio Protection - Stop at Midnight"
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.thermacell_liv_patio
```

#### Low Refill Alert

```yaml
automation:
  - alias: "Thermacell - Low Refill Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.thermacell_liv_patio_refill_life
        below: 20  # Alert at 20% remaining
    action:
      - service: notify.mobile_app
        data:
          title: "Thermacell Refill Low"
          message: "Patio Thermacell refill at {{ states('sensor.thermacell_liv_patio_refill_life') }}%. Order replacement soon."
          data:
            priority: high
```

#### Presence-Based Protection

```yaml
automation:
  - alias: "Thermacell - Auto Start When Home"
    trigger:
      - platform: state
        entity_id: person.family_member
        to: "home"
    condition:
      - condition: sun
        after: sunset
        before: sunrise
      - condition: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 65
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - delay:
          seconds: 30  # Wait for warming up
      - service: notify.mobile_app
        data:
          message: "Patio mosquito protection activated!"
```

#### LED Color Based on Protection Status

```yaml
automation:
  - alias: "Thermacell LED - Visual Status Indicator"
    trigger:
      - platform: state
        entity_id: sensor.thermacell_liv_patio_system_status
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Protected"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [0, 255, 0]  # Green = Protected
                  brightness: 255
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Warming Up"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [255, 165, 0]  # Orange = Warming
                  brightness: 200
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Error"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [255, 0, 0]  # Red = Error
                  brightness: 255
```

### Lovelace Dashboard Card Example

```yaml
type: entities
title: Patio Mosquito Protection
entities:
  - entity: switch.thermacell_liv_patio
    name: Protection
    icon: mdi:shield-bug
  - entity: sensor.thermacell_liv_patio_system_status
    name: Status
  - entity: sensor.thermacell_liv_patio_refill_life
    name: Refill Life
  - entity: sensor.thermacell_liv_patio_system_runtime
    name: Runtime
  - entity: light.thermacell_liv_patio_led
    name: LED Light
  - type: button
    name: Reset Refill
    action_name: Reset
    tap_action:
      action: call-service
      service: button.press
      service_data:
        entity_id: button.thermacell_liv_patio_reset_refill
```

### Script Examples

#### Outdoor Event Mode

```yaml
script:
  thermacell_event_mode:
    alias: "Thermacell - Outdoor Event Mode"
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 200
          rgb_color: [255, 255, 255]  # Bright white for visibility
      - service: notify.mobile_app
        data:
          message: "Outdoor event mode activated - mosquito protection on!"
```

#### Night Mode (Dim LED)

```yaml
script:
  thermacell_night_mode:
    alias: "Thermacell - Night Mode"
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 50  # Dim for nighttime
          rgb_color: [255, 50, 0]  # Deep red (night vision friendly)
```

## 🛠️ Development

### 🧪 Running Tests

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=custom_components.thermacell_liv
```

### 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** and add tests
4. **Run the test suite** to ensure everything passes
5. **Submit a pull request**

## 🔌 API Information

This integration uses the Thermacell IoT API (ESP Rainmaker platform):
- **Base URL**: `https://api.iot.thermacell.com/`
- **Authentication**: Username/Password with JWT tokens
- **Protocol**: HTTPS REST API
- **Rate Limiting**: Respectful polling every 60 seconds

## 📋 Requirements

- **Home Assistant**: 2023.1.0 or newer (2024.x+ recommended for best compatibility)
- **Python**: 3.10 or newer
- **Network**: Internet connection required for cloud API access
- **Account**: Active Thermacell account with registered LIV devices

### 📦 Dependencies

This integration requires the following Python packages:

- **aiohttp** (>= 3.8.0): Async HTTP client for API communication
  - Included with Home Assistant core
  - Used for all API requests to Thermacell cloud services
  - Handles authentication, device control, and status polling

- **homeassistant** core libraries:
  - `homeassistant.helpers.aiohttp_client`: For managed HTTP sessions
  - `homeassistant.helpers.update_coordinator`: For coordinated data updates
  - `homeassistant.config_entries`: For configuration flow management

All dependencies are automatically managed by Home Assistant. No manual installation required.

## 🗑️ Uninstallation

### Removing the Integration

To completely remove the Thermacell LIV integration from your Home Assistant:

1. **Remove the Integration Instance**:
   - Go to **Settings** → **Devices & Services**
   - Find **Thermacell LIV** in the list
   - Click the **three dots menu** (⋮) on the integration card
   - Select **Delete**
   - Confirm the deletion

2. **Remove Integration Files** (if desired):

   **For HACS installations**:
   - Open HACS in your Home Assistant instance
   - Go to **Integrations**
   - Find **Thermacell LIV**
   - Click **Remove**
   - Restart Home Assistant

   **For manual installations**:
   ```bash
   # Remove the integration directory
   rm -rf /config/custom_components/thermacell_liv
   ```

3. **Clean up (optional)**:
   - Remove any automations using Thermacell entities
   - Remove any Lovelace cards displaying Thermacell data
   - Clear any related notification templates

4. **Restart Home Assistant**:
   - Settings → System → Restart → **Restart Home Assistant**

### What Gets Removed

When you delete the integration:
- ✅ All entities (switches, lights, sensors, buttons)
- ✅ All device entries
- ✅ Configuration data (username/password)
- ✅ Historical data in the database (after retention period)
- ❌ Integration files remain (unless manually removed or via HACS)

**Note**: Deleting the integration does not affect your Thermacell account or devices. You can re-add the integration at any time.

## 🔧 Available Services

This integration uses standard Home Assistant services. No custom services are provided.

### Switch Services

- `switch.turn_on`: Enable mosquito repeller
- `switch.turn_off`: Disable mosquito repeller
- `switch.toggle`: Toggle repeller state

### Light Services

- `light.turn_on`: Control LED power, color, and brightness
  - Parameters:
    - `rgb_color`: RGB color tuple (e.g., [255, 100, 0])
    - `brightness`: Brightness value 0-255
- `light.turn_off`: Turn off LED

### Button Services

- `button.press`: Press button (refill reset or refresh)

**Example Service Call**:
```yaml
service: light.turn_on
target:
  entity_id: light.thermacell_liv_patio_led
data:
  rgb_color: [255, 100, 0]  # Orange
  brightness: 200            # ~78% brightness
```

For more information on using these services, see the [Home Assistant Services Documentation](https://www.home-assistant.io/docs/scripts/service-calls/).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Issues**: Report bugs and feature requests on [GitHub Issues](https://github.com/joyfulhouse/thermacell_liv/issues)
- **Discussions**: Join the conversation on [GitHub Discussions](https://github.com/joyfulhouse/thermacell_liv/discussions)
- **Home Assistant Community**: [Home Assistant Community Forum](https://community.home-assistant.io/)

## 🙏 Acknowledgments

- Thanks to the Home Assistant community for their excellent documentation and examples
- Anthropic Claude for development assistance and code generation
- ESP Rainmaker platform for the underlying IoT infrastructure
- Thermacell LIV device owners who helped with API reverse engineering and testing

---

**⚠️ Disclaimer**: This is an unofficial integration. Thermacell® and LIV® are trademarks of Thermacell Repellents, Inc.

<!-- Links -->
[buymecoffee]: https://buymeacoffee.com/btli
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[commits]: https://github.com/joyfulhouse/thermacell_liv/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40joyfulhouse-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/joyfulhouse/thermacell_liv?style=for-the-badge
[releases]: https://github.com/joyfulhouse/thermacell_liv/releases
[user_profile]: https://github.com/joyfulhouse
