# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
