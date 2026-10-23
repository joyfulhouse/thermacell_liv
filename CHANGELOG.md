# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-10-23

First stable release of native controls. Consolidates 2.0.7-beta.1 and
2.1.0-beta.1 through beta.5: native shutdown timers and `run_for` /
`schedule_shutdown` actions, schedule and group switches, firmware updates,
reboot, timezone, verified power control, timed-shutdown reconciliation with
repairs, and refill/shutdown diagnostics.

### Changed
- Require pythermacell 0.3.1 (stable).
- LAN control is **experimental and opt-in**: "Prefer local network control"
  now defaults off because no tested firmware advertises local control and the
  path is simulator-validated only. Entries that explicitly enabled it keep it.

### Fixed
- Rejected credentials during a runtime refresh now start Home Assistant's
  reauthentication flow instead of only marking entities unavailable, and are
  never masked by cached membership when local transports exist.

### Validated
- Native 20-second timer expiry, verified timed run, and verified off passed
  3/3 repetitions on each of two live hubs (firmware 5.4.7) on 2026-10-23.

### Known Limitations
- Firmware 5.4.7 has intermittently reported Warming after native timer expiry
  while the enable flag is false (#30). HA detects this, makes one bounded
  verified-off attempt, then raises a repair and blocks new starts until Off is
  confirmed. Cloud reports cannot prove physical heater state.
- Offline restart is unsupported; setup and restart require the cloud.

## [2.1.0-beta.5] - 2026-10-20

### Changed
- Qualify the transport sensor as a route hint, unknown before route evidence
  exists and after its local transport is pruned, not proof of LAN success.
- Export diagnostics with stable anonymous node/device labels and retained
  firmware, LED, maintenance, command, and refill/shutdown support evidence;
  redact nested identifiers and known credentials, including list/tuple values.
- Document cloud setup/restart requirements, conditional LAN operation, measured
  firmware 5.4.7 capability limits, diagnostic availability, and leak response.

### Fixed
- Scrub historical credentials copied into arbitrary diagnostic fields and keys.
- Correct cached-membership behavior after failed cloud reauthentication.
- Prefer usable IPv4/local address candidates and fail over reads across bounded
  advertised addresses without retrying writes or replaying them through cloud.
- Re-evaluate late announcements after refresh, preserve live discovery aliases,
  prune removed account nodes, and release eagerly completed resolution tasks.
- Keep optional discovery failures from invalidating successful cloud refreshes.

## [2.1.0-beta.4] - 2026-10-19

### Changed
- Require pythermacell 0.3.0b4 for explicit operational Off confirmation.

### Fixed
- Reconcile native timer expiry even after the hub disables its schedule. Keep
  the deadline until operational Off is confirmed, try one bounded off command,
  and persist a repair and start lockout if shutdown remains unconfirmed (#30).
- Keep the power-mismatch diagnostic active for an unconfirmed timed shutdown.
  This mitigates a monitoring gap; the intermittent firmware/cloud failure is
  unresolved. No automatic reboot or final release promotion is included.

## [2.1.0-beta.3] - 2026-10-18

### Changed
- Require pythermacell 0.3.0b3 for HTTP 207 batch results and shutdown diagnostics.

### Fixed
- Describe failed power changes as failed or unconfirmed instead of assuming
  command rejection when a hub acknowledges off but keeps reporting Warming Up.
- Add a timed-run regression through the library confirmation path, preserving
  individual/group service errors and the native timer when shutdown is unconfirmed
  (#30). The underlying firmware behavior still requires hardware investigation.

## [2.1.0-beta.2] - 2026-10-18

### Fixed
- Use pythermacell 0.3.0b2 to resolve the protobuf 7 dependency conflict that
  prevented the native-control beta from loading on current Home Assistant.

## [2.0.7-beta.1] - 2026-10-18

### Added
- A restored per-hub refill type selector for 40-hour yellow, 100-hour blue,
  and 180-hour gray cartridges. The reset button applies the selected type.

### Fixed
- Require confirmed power changes using pythermacell 0.2.7; expose failed
  commands to Home Assistant instead of reporting success.
- Preserve active reported hub status when the control flag is already off.
- Revert optimistic state when the library rejects a command.
- Preserve requested LED brightness instead of overwriting it with 100%.

## [2.0.5] - 2026-03-05

### Changed

- Bumped `pythermacell` dependency from `>=0.2.3` to `>=0.2.4`.

### Fixed

- **System Runtime accuracy**: updated to pythermacell 0.2.4, which correctly
  converts API values from tenths of hours to minutes (×6 multiplier).
- **System Runtime None handling**: the sensor now handles `None` runtime values
  when the API does not report System Runtime.

## [2.0.4] - 2025-11-28

### Added

- **Reconfigure flow**: update credentials from the integration menu.
- **Integration title**: the config entry title now includes the username
  (e.g. "Thermacell LIV (user@example.com)"); existing entries update on the
  next restart.

### Removed

- **Hub ID sensor**: removed because the API does not provide meaningful serial
  number data.
- **Serial number**: removed from device info (the API returns "unknown").

## [2.0.3] - 2025-11-28

### Changed

- **Device naming**: device names now include the "Thermacell LIV" prefix
  (e.g. "Thermacell LIV ADU"); entity IDs are prefixed accordingly
  (`switch.thermacell_liv_adu`, `light.thermacell_liv_adu_led`).
- **Device model**: now displays "Thermacell LIV Hub" instead of generic "Hub".

## [2.0.2] - 2025-11-27

### Changed

- **CI consolidation**: merged four workflow files into two — `validate.yaml`
  (HassFest + HACS) and `ci.yaml` (lint, test, type check, quality-scale tiers).
- **Platform setup**: extracted a common `async_setup_platform_entities()`
  helper to reduce duplication.
- **Base entity**: moved `has_entity_name = True` to the base class.
- Consolidated Quality Scale compliance into a single `QUALITY_SCALE.md`.

### Removed

- Dead code in the coordinator (`_async_optimistic_update`,
  `_update_local_state`) and unused imports.
- Redundant `async_request_refresh` call in the button handler.
- Old workflow files (`hassfest.yaml`, `validate.yml`, `quality-tiers.yml`).

## [2.0.1] - 2025-11-26

### Changed

- Updated CI workflows to use Python 3.13.
- Updated CI to check for `pythermacell` instead of `aiohttp`.
- Code quality improvements and reduced duplication.

### Fixed

- CI workflow compatibility with the latest Home Assistant.

## [2.0.0] - 2025-11-25

### Added

- **pythermacell library integration**: migrated to the dedicated
  `pythermacell>=0.2.3` library.
- **Platinum Quality Scale**: achieved 54/54 rules compliance (Bronze 19/19,
  Silver 10/10, Gold 22/22, Platinum 3/3).
- **Full type safety**: complete type annotations with a `py.typed` marker and
  TypedDict definitions.
- **Diagnostics platform**: redacted sensitive-data export for troubleshooting.
- **Repair flows**: auto-recovery for authentication and device-offline issues.
- **Options flow**: configurable scan interval (30-300 seconds).

### Changed

- **Architecture**: clean separation between the API client (library) and the
  Home Assistant integration; the coordinator uses library methods directly.
- **Entity base**: consolidated common functionality in `ThermacellLivEntity`.
- **Error handling**: improved unavailability logging and state management.

[Unreleased]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.5...HEAD
[2.0.5]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.4...v2.0.5
[2.0.4]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.3...v2.0.4
[2.0.3]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.2...v2.0.3
[2.0.2]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/joyfulhouse/thermacell_liv/releases/tag/v2.0.0
