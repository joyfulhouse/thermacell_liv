# Architecture

How Thermacell LIV is structured and why.

## Overview

The integration is a thin Home Assistant layer over the
[pythermacell](https://github.com/joyfulhouse/pythermacell) library. The library
owns all communication with the Thermacell cloud (ESP RainMaker) API; the
integration owns Home Assistant concerns — config flow, the update coordinator,
entities, diagnostics, and repairs.

## Components

| Module | Responsibility |
|---|---|
| `__init__.py` | Sets up the config entry, creates the client and coordinator, loads platforms; stores `runtime_data` as `{"coordinator": ..., "client": ...}`. |
| `coordinator.py` | `DataUpdateCoordinator` subclass; polls devices, applies optimistic updates, logs availability transitions, raises repair issues. |
| `config_flow.py` | UI setup with live credential validation; reauthentication, reconfigure, and options (scan interval) flows. |
| `entity.py` | Base `ThermacellLivEntity` (sets `has_entity_name`, availability from coordinator + node status). |
| `switch.py` / `light.py` / `sensor.py` / `button.py` | Entity platforms. |
| `thermacell_types.py` | TypedDict definitions for strict typing. |
| `diagnostics.py` | Redacted config-entry diagnostics export. |
| `repairs.py` | Repair flows for auth failure and device-offline issues. |
| `const.py` | Domain, config keys, status constants, scan-interval bounds. |

## Data Flow

1. **Authentication** — the config flow validates the username/password by
   logging in through pythermacell, which exchanges them for JWT tokens.
2. **Discovery** — the coordinator fetches all nodes on the account and creates
   a device and entity set per hub; new hubs are added dynamically on later
   polls.
3. **Polling** — every scan interval (default 60 s) the coordinator refreshes
   node params, status, and config and pushes updates to entities.
4. **Control (optimistic)** — a user action updates entity state immediately,
   then issues the API call in the background; on failure the state reverts.

## Key Design Decisions

- **Library/integration split** — keeping the API client in `pythermacell` lets
  the integration stay focused on Home Assistant and lets the library be tested
  and reused independently.
- **Optimistic updates** — cloud round-trips average ~2.5 s, so the UI updates
  optimistically (~0.01 s perceived) and reverts on error, trading a brief
  chance of rollback for a responsive interface.
- **Cloud polling** — the API offers no local or push channel, so polling with a
  configurable interval is the only option; the AC-powered, slow-changing hubs
  make a 60 s default a good default.
- **LED state coupling** — the LED reports "on" only when the hub is powered and
  brightness > 0, matching how the hardware behaves.
- **Strict typing** — `py.typed`, TypedDicts, and mypy strict mode satisfy the
  Platinum quality tier and catch data-shape errors early.

See [QUALITY_SCALE.md](QUALITY_SCALE.md) for the full quality-scale breakdown.
