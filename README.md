# 🦟 Thermacell LIV Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![HACS][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

A powerful 🏠 Home Assistant integration for controlling and monitoring 🦟 Thermacell LIV mosquito repellers through their cloud API.

## ✨ Features

- 🎛️ **Control mosquito repellers**: Turn your Thermacell LIV devices on and off
- 💡 **LED color control**: Customize the LED color and brightness on your devices  
- ⏱️ **Monitor refill life**: Track remaining refill life in hours
- 🔄 **Refill reset**: Reset the refill life counter when replacing cartridges
- 🏘️ **Multi-device support**: Manage multiple Thermacell LIV hubs from a single integration
- 📡 **Real-time status**: Monitor device connectivity and online status
- ⏰ **System runtime**: Track how long your devices have been running
- 📊 **System status**: Monitor current state (On, Off, Warming Up)
- 🔧 **Device information**: View firmware version, serial number, and model details

## 🏠 Supported Entities

Each Thermacell LIV hub provides the following Home Assistant entities:

- 🔌 **Switch**: `switch.thermacell_liv_{device_name}` - Controls the mosquito repeller on/off
- 💡 **Light**: `light.thermacell_liv_{device_name}_led` - Controls LED color and brightness  
- ⏱️ **Refill Life Sensor**: `sensor.thermacell_liv_{device_name}_refill_life` - Monitors refill life remaining (hours)
- 📊 **System Status Sensor**: `sensor.thermacell_liv_{device_name}_system_status` - Current device status (On, Off, Warming Up)
- ⏰ **System Runtime Sensor**: `sensor.thermacell_liv_{device_name}_system_runtime` - Total runtime (formatted as days/hours/minutes)
- 🔄 **Reset Button**: `button.thermacell_liv_{device_name}_reset_refill` - Resets refill life counter

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
   - 🌐 **API Base URL**: `https://api.iot.thermacell.com/` (default)

### 🔐 Authentication Setup

You'll need a Thermacell account with registered LIV devices. The integration uses the same credentials you use for the 📱 Thermacell mobile app.

1. 📝 **Create an account** at [🌐 Thermacell's website](https://www.thermacell.com/) if you don't have one
2. 📱 **Register your LIV devices** using the Thermacell mobile app  
3. 🏠 **Use the same credentials** in Home Assistant

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

## 🔧 Troubleshooting

### ❗ Common Issues

**🔐 Authentication Failed**:
- Verify your username/password are correct
- Ensure your Thermacell account is active
- Check that your devices are registered in the Thermacell mobile app

**📱 No devices found**:
- Make sure your LIV devices are online and connected to WiFi
- Verify devices are registered in your Thermacell account
- Try refreshing the integration: Settings → Devices & Services → Thermacell LIV → "Reload"

**🌐 Connection timeout**:
- Check your internet connection
- Verify the API base URL is correct: `https://api.iot.thermacell.com/`
- Check Home Assistant logs for detailed error messages

### 🐛 Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.thermacell_liv: debug
```

### 📊 API Rate Limiting

The integration polls the Thermacell API every 60 seconds by default. If you experience rate limiting:

- Reduce polling frequency in the coordinator configuration
- Avoid making too many manual API calls through automations

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

- **Home Assistant**: 2023.1.0 or newer
- **Python**: 3.10 or newer
- **Dependencies**: 
  - `aiohttp` (included with Home Assistant)
  - `homeassistant` core

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
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40joyfulhouse-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[releases]: https://github.com/joyfulhouse/thermacell_liv/releases
[user_profile]: https://github.com/joyfulhouse
