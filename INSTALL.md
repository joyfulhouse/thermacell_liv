# Installing Thermacell LIV

## Prerequisites

- Home Assistant 2025.11.0 or newer.
- [HACS](https://hacs.xyz) installed (recommended), or filesystem access to your
  Home Assistant `config` directory (for manual installation).
- A Thermacell account with at least one registered LIV hub.

## Method 1 — HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/joyfulhouse/thermacell_liv` with category
   **Integration**.
4. Search for **Thermacell LIV** and click **Download**.
5. **Restart Home Assistant.**

Or use this one-click link:

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=joyfulhouse&repository=thermacell_liv&category=integration)

## Method 2 — Manual installation

1. Download the latest release from the
   [releases page](https://github.com/joyfulhouse/thermacell_liv/releases).
2. Copy the `custom_components/thermacell_liv` folder into your Home Assistant
   `config/custom_components/` directory. The result should be
   `config/custom_components/thermacell_liv/`.
3. **Restart Home Assistant.**

## Method 3 — Clone with git

```bash
cd /config/custom_components
git clone https://github.com/joyfulhouse/thermacell_liv.git
cp -r thermacell_liv/custom_components/thermacell_liv ./thermacell_liv-tmp
rm -rf thermacell_liv && mv thermacell_liv-tmp thermacell_liv
```

Then **restart Home Assistant**. (Manual and clone installs do not auto-update;
prefer HACS for updates.)

## Adding the Integration

1. Go to **Settings → Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **Thermacell LIV** and select it.
4. Enter your Thermacell account username/email and password and submit. The
   integration validates the credentials and discovers your hubs.

## Verifying

After setup, the integration's devices and entities appear under
**Settings → Devices & Services → Thermacell LIV**.

## Updating

- **HACS:** update from the HACS dashboard when a new version is available, then
  restart Home Assistant.
- **Manual:** replace the `custom_components/thermacell_liv` folder with the new
  release and restart.

## Troubleshooting

If the integration does not appear or fails to set up, see the **Troubleshooting**
section of the [README](README.md#troubleshooting) or
[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), and enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.thermacell_liv: debug
```
