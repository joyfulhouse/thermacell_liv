# Configuration

Full configuration reference for Thermacell LIV. For a quick overview, see the
[README](../README.md#configuration).

## Adding the Integration

1. Go to **Settings → Devices & Services**.
2. Click **+ Add Integration** and search for **Thermacell LIV**.
3. Enter your credentials:
   - **Username/Email** — your Thermacell account login (the same email used by
     the mobile app), a valid email address (e.g. `user@example.com`).
   - **Password** — your Thermacell account password. It is stored encrypted in
     Home Assistant's secure storage.
4. Click **Submit**. The integration authenticates against the API, discovers
   every hub on the account, and creates their devices and entities.

### Prerequisites

1. **Active Thermacell account** — create one at
   [thermacell.com](https://www.thermacell.com/) and verify your email.
2. **Registered LIV device** — set the hub up in the Thermacell mobile app
   (iOS/Android) and connect it to 2.4 GHz Wi-Fi. Confirm it appears in the app.
3. **Network** — Home Assistant needs outbound HTTPS internet access. No inbound
   firewall configuration is required.

## Configuration Options

Open **Settings → Devices & Services → Thermacell LIV → Configure**.

| Option | Default | Range | Description |
|---|---|---|---|
| Scan interval | 60 s | 30-300 s | How often device status is polled from the API |

### Automatic parameters

These are fixed and not user-configurable:

- **API base URL**: `https://api.iot.thermacell.com/` (ESP RainMaker platform,
  HTTPS/TLS).
- **Parallel updates**: switch, light, and button platforms use 1 concurrent
  operation to avoid API conflicts; sensors are read-only and unlimited.

### Choosing a scan interval

The 60-second default balances responsiveness against API load:

- LIV hubs are AC-powered and change state infrequently, so frequent polling
  adds little value.
- It stays conservative with respect to Thermacell cloud rate limits (no
  published limits; a respectful default is used).
- Optimistic updates already give instant UI feedback for your own actions,
  independent of the poll interval.

Set 30 s for near real-time status (more API calls) or 300 s to minimize calls.

## Reconfiguration and Reauthentication

### Reauthentication

If credentials change or expire, Home Assistant prompts you to reauthenticate.
You can also trigger it manually:

1. **Settings → Devices & Services**.
2. Find **Thermacell LIV** and follow the **Reconfigure**/reauth prompt.
3. Enter the new username and password and submit. The integration reloads with
   the updated credentials.

## Data Updates and Polling

The integration uses **cloud polling** with optimistic updates:

1. **Initial connection** — on startup it fetches all device data from the API.
2. **Periodic polling** — device status refreshes every scan interval
   (default 60 s).
3. **Optimistic updates** — when you control a device, the UI updates
   immediately (~0.01 s) while the API call runs in the background (~2.5 s
   average); the change reverts if the API call fails.
4. **Manual refresh** — the diagnostic refresh button forces an immediate
   update.

Data freshness:

- Device states refresh every poll interval.
- Refill life, system status, and connectivity update on each poll; offline
  devices are detected promptly.

## Removing Devices

### Remove a specific device

1. **Settings → Devices & Services → Thermacell LIV**.
2. Open the device, click the gear icon, then **Delete** and confirm.

A device that is still on your Thermacell account is re-added on the next update.
To remove it permanently, remove it from your Thermacell account in the mobile
app, or remove the whole integration.

### Remove the integration

1. **Settings → Devices & Services**.
2. On the **Thermacell LIV** card, open the **⋮** menu → **Delete** and confirm.

This removes all entities, devices, and stored credentials. Historical data in
the recorder database is preserved by default; clear it from **Developer Tools →
Statistics** if desired. Removing the integration does not affect your
Thermacell account or hardware.

## Known Limitations

**API and connectivity**

- Requires constant internet access; cannot function if the Thermacell API is
  down. There is no local API.
- Status updates are limited by the polling interval (the integration polls; it
  does not receive device push notifications).
- Excessive API calls may be temporarily throttled.

**Device**

- Each integration instance supports a single Thermacell account.
- LIV hubs require 2.4 GHz Wi-Fi (5 GHz is not supported by the hardware).
- Runtime tracking reports the current session, not lifetime usage. Refill life
  is an estimate, not a measurement.

**Features**

- LED control is basic RGB — no effects or patterns (hardware limitation).
- No device-side scheduling (use Home Assistant automations) and no built-in
  zone grouping; each hub is independent.
- Hubs are AC-powered, so there is no battery monitoring.
