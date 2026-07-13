# <img src="logo_2025.webp" alt="" width="200" height="60"> Thermacell LIV

Local-account control and monitoring of Thermacell LIV mosquito repellers in Home Assistant.

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![HACS][hacs-shield]][hacs]
[![CI][ci-shield]][ci]
[![Quality Scale][quality-shield]][quality]
[![Project Maintenance][maintenance-shield]][maintenance]
[![GitHub Sponsors][sponsors-shield]][sponsors]
[![Ko-fi][kofi-shield]][kofi]

## What It Does

Thermacell LIV is a Home Assistant integration for controlling and monitoring
[Thermacell LIV](https://www.thermacell.com/) smart mosquito repeller hubs
through the Thermacell cloud (ESP RainMaker) API. It exposes each hub as a
switch, an RGB LED light, refill-life and status sensors, and maintenance
buttons, with optimistic updates for instant UI feedback. A single integration
instance manages every hub on your Thermacell account.

## Features

- Turn mosquito repellers on and off.
- Control the indicator LED color and brightness.
- Monitor remaining refill life and reset the counter when replacing cartridges.
- Track system status (Off, Warming Up, Protected, Error) and session runtime.
- Manage multiple LIV hubs from one integration instance, with automatic
  device discovery.
- Diagnostic sensors for connectivity, error codes, and firmware version
  (disabled by default).
- Configurable polling interval (30-300 seconds) and credential
  reauthentication without removing the integration.
- Repair flows and redacted diagnostics for troubleshooting.

## Prerequisites

- Home Assistant 2025.11.0 or newer.
- A Thermacell account with at least one registered LIV hub (set up via the
  Thermacell mobile app, connected to 2.4 GHz Wi-Fi).
- Outbound internet access from Home Assistant (the integration is cloud-based;
  no local API exists).

## Installation

See **[INSTALL.md](INSTALL.md)** for the complete guide.

**Quick version (HACS):** add this repository as a custom repository in HACS,
install **Thermacell LIV**, restart Home Assistant, then add the integration
from **Settings → Devices & Services**.

[![Open in HACS][hacs-repo-shield]][hacs-repo]

## Configuration

Add the integration from **Settings → Devices & Services → Add Integration →
Thermacell LIV** and enter the username/email and password for your Thermacell
account (the same credentials used by the mobile app). The integration
validates them against the API, then discovers and adds every hub on the
account.

After setup you can change the polling interval (default 60 s, range
30-300 s) via **Configure**, and update credentials at any time through the
reauthentication or reconfigure flow. For the full reference — every option,
reconfiguration, device removal behavior, and polling internals — see
**[docs/CONFIGURATION.md](docs/CONFIGURATION.md)**.

## Supported Equipment

| Item | Detail |
|---|---|
| Device | Thermacell LIV Hub (model `thermacell-hub`) |
| Connectivity | Cloud (ESP RainMaker), 2.4 GHz Wi-Fi |
| Firmware | ESP RainMaker API v1 (tested 5.3.2+) |
| Not supported | Patio Shield, E-Series, Radius (different protocols) |

Each hub exposes a switch, an LED light, refill-life and system-status
sensors, and a refill-reset button by default, plus diagnostic sensors and a
refresh button that are disabled by default. The full entity catalog is in
**[docs/ENTITIES.md](docs/ENTITIES.md)**.

## Automation Examples

Turn the repeller on at sunset:

```yaml
automation:
  - alias: "Thermacell on at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
```

Notify when refill life runs low:

```yaml
automation:
  - alias: "Thermacell low refill alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.thermacell_liv_patio_refill_life
        below: 20
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: >-
            Thermacell refill at
            {{ states('sensor.thermacell_liv_patio_refill_life') }}%.
```

More recipes — presence-based protection, LED status indicators, event/night
scripts, and dashboard cards — are in **[docs/AUTOMATIONS.md](docs/AUTOMATIONS.md)**.

## Troubleshooting

Most issues fall into a few buckets:

- **Authentication failed** — verify the credentials work in the mobile app;
  use the reauthentication flow if they changed.
- **No devices found** — confirm hubs are powered on, online in the app, and on
  2.4 GHz Wi-Fi; reload the integration.
- **Connection timeouts** — check Home Assistant's internet access and the
  Thermacell API status.

Enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.thermacell_liv: debug
```

Full symptom/fix tables and diagnostics steps are in
**[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

## Development

This integration is built on the
[pythermacell](https://github.com/joyfulhouse/pythermacell) Python library. See
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) to set up a development environment,
and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the integration is
structured.

## Support

- Join the [JoyfulHouse Discord](https://discord.gg/gc4eTPwxjJ) for support and discussion across all JoyfulHouse Home Assistant integrations and libraries.
- **Issues:** <https://github.com/joyfulhouse/thermacell_liv/issues>
- **Discussions / questions:** open an issue with the `question` label.

## Support Development

If this project is useful to you, please consider supporting its development:

- [GitHub Sponsors][sponsors]
- [Ko-fi][kofi]

## License

This project is licensed under the **MIT** License — see [LICENSE](LICENSE) for
details.

## Credits

Built and maintained by [JoyfulHouse](https://github.com/joyfulhouse) with the
[pythermacell](https://github.com/joyfulhouse/pythermacell) library.

Thermacell® and LIV® are trademarks of Thermacell Repellents, Inc. This is an
unofficial integration and is not affiliated with or endorsed by Thermacell.

<!-- Badge links -->
[releases-shield]: https://img.shields.io/github/release/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[releases]: https://github.com/joyfulhouse/thermacell_liv/releases
[license-shield]: https://img.shields.io/github/license/joyfulhouse/thermacell_liv.svg?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacs-repo-shield]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-repo]: https://my.home-assistant.io/redirect/hacs_repository/?owner=joyfulhouse&repository=thermacell_liv&category=integration
[ci-shield]: https://img.shields.io/github/actions/workflow/status/joyfulhouse/thermacell_liv/ci.yaml?style=for-the-badge&label=CI
[ci]: https://github.com/joyfulhouse/thermacell_liv/actions
[quality-shield]: https://img.shields.io/badge/Quality%20Scale-Platinum-5c2d91.svg?style=for-the-badge
[quality]: https://developers.home-assistant.io/docs/core/integration-quality-scale/
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40btli-blue.svg?style=for-the-badge
[maintenance]: https://github.com/btli
[sponsors-shield]: https://img.shields.io/badge/sponsor-GitHub-EA4AAA.svg?style=for-the-badge&logo=githubsponsors&logoColor=white
[sponsors]: https://github.com/sponsors/btli
[kofi-shield]: https://img.shields.io/badge/Ko--fi-donate-FF5E5B.svg?style=for-the-badge&logo=ko-fi&logoColor=white
[kofi]: https://ko-fi.com/bryanli
