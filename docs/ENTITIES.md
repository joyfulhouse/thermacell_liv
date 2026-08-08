# Entities and Services

The complete catalog of devices, entities, and services exposed by Thermacell
LIV. For a summary, see the [README](../README.md#supported-equipment).

## Supported Devices

This integration supports all **Thermacell LIV** mosquito repeller hubs.

| Property | Detail |
|---|---|
| Model | Thermacell LIV Hub (`thermacell-hub`) |
| Indicator | RGB LED |
| Connectivity | Cloud (ESP RainMaker), 2.4 GHz Wi-Fi |
| Cartridge | Refillable |
| Tested firmware | 5.3.2 and later |
| Minimum firmware | Any version supporting ESP RainMaker API v1 |

**Regional availability** — sold in the United States, Canada, and other
regions; see [thermacell.com](https://www.thermacell.com/) for current
availability.

**Not supported** — Thermacell Patio Shield (non-Wi-Fi), E-Series (different
protocol), and Radius (different app/API).

## Entities

Each hub provides the following entities. Entity IDs use the device name, e.g.
`switch.thermacell_liv_patio`.

### Enabled by default

| Entity | Type | Description |
|---|---|---|
| `switch.thermacell_liv_{name}` | Switch | Turns the mosquito repeller on/off (optimistic) |
| `light.thermacell_liv_{name}_led` | Light | RGB color and brightness of the indicator LED |
| `sensor.thermacell_liv_{name}_refill_life` | Sensor | Remaining refill life (%) |
| `sensor.thermacell_liv_{name}_system_status` | Sensor | Off, Warming Up, Protected, Error |
| `button.thermacell_liv_{name}_reset_refill` | Button | Resets the refill-life counter to 100% |

### Diagnostic entities (disabled by default)

Enable them via **Settings → Devices & Services → Thermacell LIV → Entity
Settings**.

| Entity | Type | Description |
|---|---|---|
| `sensor.thermacell_liv_{name}_system_runtime` | Sensor | Current session runtime (days/hours/minutes) |
| `sensor.thermacell_liv_{name}_connectivity` | Sensor | Connected / Disconnected |
| `sensor.thermacell_liv_{name}_error_code` | Sensor | Numeric error code, with `has_error`/status attributes |
| `sensor.thermacell_liv_{name}_firmware_version` | Sensor | Current firmware version (e.g. 5.3.2) |
| `button.thermacell_liv_{name}_refresh` | Button | Forces an immediate data refresh from the API |

### Notes on behavior

- **LED state logic** — the LED light reports "on" only when the hub is powered
  **and** brightness is greater than 0. Brightness is converted between Home
  Assistant's 0-255 range and the device's 0-100 range.
- **System status** — derived from the hub's reported state: `Error` when a
  fault code is present, `Off` when repellers are disabled, `Warming Up` while
  heating, and `Protected` when operational. Some hubs constantly report error
  bit `0x01000000` (16777216) while working normally, so that bit alone does not
  count as a fault; the raw value is still shown by the error code sensor.
- **System runtime** — reflects the current session as reported by the API; this
  differs from the lifetime total shown in the mobile app.
- **Device info** — each hub reports model "Thermacell LIV Hub" and its firmware
  version.

## Services

The integration uses standard Home Assistant services; it provides no custom
services.

**Switch**

- `switch.turn_on` / `switch.turn_off` / `switch.toggle` — control the repeller.

**Light**

- `light.turn_on` — control the LED, with `rgb_color` (e.g. `[255, 100, 0]`) and
  `brightness` (0-255).
- `light.turn_off` — turn the LED off.

**Button**

- `button.press` — press a button (refill reset or refresh).

Example:

```yaml
service: light.turn_on
target:
  entity_id: light.thermacell_liv_patio_led
data:
  rgb_color: [255, 100, 0]
  brightness: 200
```

## API Reference

The integration communicates with the Thermacell IoT (ESP RainMaker) API via the
[pythermacell](https://github.com/joyfulhouse/pythermacell) library:

- **Base URL**: `https://api.iot.thermacell.com/`
- **Authentication**: username/password exchanged for JWT tokens
- **Protocol**: HTTPS REST

## Dependencies

- **pythermacell** — handles all API communication.
- Home Assistant core libraries (`aiohttp_client`, `update_coordinator`,
  `config_entries`). All dependencies are managed by Home Assistant; no manual
  installation is required.
