# Changelog

All notable changes to the Thermacell LIV Home Assistant integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2024-11-27

### Changed
- **CI Consolidation**: Merged 4 workflow files into 2 clean workflows
  - `validate.yaml`: HassFest + HACS (run in parallel with summary)
  - `ci.yaml`: Lint, Test, Type Check, Quality Scale tiers (Bronze→Platinum)
- **Platform Setup**: Extracted common `async_setup_platform_entities()` helper to reduce duplication
- **Base Entity**: Moved `has_entity_name = True` to base class (removes 11 redundant lines)
- **Branch Protection**: Updated required checks to `Lint`, `Test`, `Platinum Tier`

### Removed
- Dead code in coordinator (`_async_optimistic_update`, `_update_local_state`)
- Unused imports (`Awaitable`, `Callable`, `TypeVar`)
- Redundant `async_request_refresh` call in button handler
- Old workflow files (`hassfest.yaml`, `validate.yml`, `quality-tiers.yml`)
- 200+ old workflow run history

### Documentation
- Consolidated Quality Scale compliance into single `QUALITY_SCALE.md`

## [2.0.1] - 2024-11-26

### Changed
- Updated CI workflows to use Python 3.13
- Code quality improvements and reduced duplication
- Updated CI to check for `pythermacell` instead of `aiohttp`

### Fixed
- CI workflow compatibility with latest Home Assistant

## [2.0.0] - 2024-11-25

### Added
- **pythermacell Library Integration**: Migrated to dedicated `pythermacell>=0.2.3` library
- **Platinum Quality Scale**: Achieved 54/54 rules compliance
- **Full Type Safety**: Complete type annotations with `py.typed` marker
- **TypedDict Definitions**: Strict typing for all data structures
- **Diagnostics Platform**: Redacted sensitive data export for troubleshooting
- **Repair Flows**: Auto-recovery for authentication and device offline issues
- **Options Flow**: Configurable scan interval (30-300 seconds)

### Changed
- **Architecture**: Clean separation between API client (library) and HA integration
- **Coordinator**: Simplified to use library methods directly
- **Entity Base**: Consolidated common functionality in `ThermacellLivEntity`
- **Error Handling**: Improved unavailability logging and state management

### Entities
- **Switch**: Main power control with optimistic updates
- **Light**: RGB LED control with brightness and color support
- **Sensors**: Refill life, system status, runtime, connectivity, error code, hub ID, firmware
- **Buttons**: Reset refill, manual refresh

### Quality Scale Compliance
- Bronze Tier: 19/19 requirements
- Silver Tier: 10/10 requirements
- Gold Tier: 22/22 requirements
- Platinum Tier: 3/3 requirements

[2.0.2]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/joyfulhouse/thermacell_liv/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/joyfulhouse/thermacell_liv/releases/tag/v2.0.0
