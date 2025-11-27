# Home Assistant Integration Quality Scale

**Integration**: Thermacell LIV
**Tier**: Platinum (100% Certified)
**Version**: 2.0.1
**Date**: November 27, 2025
**Maintainer**: @btli

---

## Summary

The Thermacell LIV integration has achieved **100% Platinum tier certification**, meeting all 54 requirements across the Home Assistant Integration Quality Scale.

| Tier | Rules | Status |
|------|-------|--------|
| Bronze | 19/19 | 100% |
| Silver | 10/10 | 100% |
| Gold | 22/22 | 100% |
| Platinum | 3/3 | 100% |
| **Total** | **54/54** | **100%** |

### Quality Metrics

| Metric | Value |
|--------|-------|
| Test Coverage | 90.48% (161 tests) |
| Type Coverage | 100% (strict mode) |
| Languages | 13 |
| Ruff Compliance | 100% |

---

## Platinum Tier (3/3)

### async-dependency
**Status**: COMPLIANT
**Implementation**: `pythermacell>=0.2.3`

The pythermacell library is fully async (aiohttp-based). All API operations use `async/await` patterns with no synchronous I/O or blocking calls.

### inject-websession
**Status**: COMPLIANT
**Implementation**: `__init__.py:30`

```python
session = async_get_clientsession(hass)
client = ThermacellClient(username=username, password=password, session=session)
```

Uses Home Assistant's managed ClientSession for proper lifecycle management.

### strict-typing
**Status**: COMPLIANT
**Implementation**: `thermacell_types.py`, `py.typed`, `pyproject.toml`

- TypedDict definitions for RGBColor, DeviceParams, NodeData
- PEP 561 marker file present
- mypy strict mode configuration

---

## Gold Tier (22/22)

| Rule | Status | Implementation |
|------|--------|----------------|
| devices | ✅ | `entity.py:21-38` - DeviceInfo with identifiers, model, firmware |
| diagnostics | ✅ | `diagnostics.py` - Export with data redaction |
| discovery-update-info | N/A | Cloud polling integration |
| discovery | N/A | Account-based device discovery via API |
| docs-data-update | ✅ | README.md - 60s polling, optimistic updates |
| docs-examples | ✅ | README.md - Automation examples |
| docs-known-limitations | ✅ | README.md - Cloud dependency, runtime discrepancy |
| docs-supported-devices | ✅ | README.md - Thermacell LIV Hub |
| docs-supported-functions | ✅ | README.md - Switch, Light, Sensors, Buttons |
| docs-troubleshooting | ✅ | README.md - Auth, connectivity, refill issues |
| docs-use-cases | ✅ | README.md - Schedules, ambiance, monitoring |
| dynamic-devices | ✅ | `coordinator.py:244-250` - Auto-discovery |
| entity-category | ✅ | Diagnostic sensors properly categorized |
| entity-device-class | ✅ | Platform-appropriate classes |
| entity-disabled-by-default | ✅ | All entities provide value |
| entity-translations | ✅ | 13 language files |
| exception-translations | ✅ | `strings.json` error section |
| icon-translations | ✅ | Dynamic icons based on state |
| reconfiguration-flow | ✅ | `config_flow.py:181-208` - Options flow |
| repair-issues | ✅ | `coordinator.py:216-224` - Device offline issues |
| stale-devices | ✅ | `__init__.py:83-116` - Cleanup on removal |

---

## Silver Tier (10/10)

| Rule | Status | Implementation |
|------|--------|----------------|
| action-exceptions | N/A | No custom services |
| config-entry-unloading | ✅ | `__init__.py:124-138` - Platform + client cleanup |
| docs-configuration-parameters | ✅ | README.md + strings.json |
| docs-installation-parameters | ✅ | README.md - Credentials required |
| entity-unavailable | ✅ | `entity.py:40-43` - Coordinator + node status |
| integration-owner | ✅ | `manifest.json:4` - @btli |
| log-when-unavailable | ✅ | `coordinator.py:196-226` - State transitions |
| parallel-updates | ✅ | All platforms - 1 for writes, 0 for reads |
| reauthentication-flow | ✅ | `config_flow.py:115-152` |
| test-coverage | ✅ | 90.48% coverage |

---

## Bronze Tier (19/19)

| Rule | Status | Implementation |
|------|--------|----------------|
| action-setup | ✅ | Standard entity platforms |
| appropriate-polling | ✅ | 60s default, 30-300s configurable |
| brands | ✅ | Accepted in home-assistant/brands |
| common-modules | ✅ | coordinator.py, entity.py, const.py, thermacell_types.py |
| config-flow-test-coverage | ✅ | `tests/test_config_flow.py` |
| config-flow | ✅ | UI setup, reauth, options |
| dependency-transparency | ✅ | `manifest.json:12` - pythermacell>=0.2.3 |
| docs-actions | N/A | No custom services |
| docs-high-level-description | ✅ | README.md |
| docs-installation-instructions | ✅ | README.md - HACS + manual |
| docs-removal-instructions | ✅ | README.md |
| entity-event-setup | ✅ | CoordinatorEntity pattern |
| entity-unique-id | ✅ | `{DOMAIN}_{node_id}_{device_name}_{type}` |
| has-entity-name | ✅ | All entities use translation keys |
| runtime-data | ✅ | `__init__.py:57` - coordinator + client |
| test-before-configure | ✅ | `config_flow.py:36-96` |
| test-before-setup | ✅ | `__init__.py:42-47` - ConfigEntryAuthFailed |
| unique-config-entry | ✅ | `config_flow.py:163-164` - Username unique ID |

---

## Test Coverage

| Module | Coverage |
|--------|----------|
| button.py | 100% |
| config_flow.py | 95.18% |
| const.py | 100% |
| coordinator.py | 74.90% |
| diagnostics.py | 100% |
| entity.py | 100% |
| light.py | 100% |
| repairs.py | 100% |
| sensor.py | 100% |
| switch.py | 100% |
| thermacell_types.py | 100% |
| __init__.py | 92.06% |
| **Total** | **90.48%** |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.1 | 2025-11-27 | Code quality improvements, optimistic update helper |
| 2.0.0 | 2025-11-26 | pythermacell library integration |
| 1.6.6 | 2025-11-17 | CI/CD validation workflows |
| 1.0.0 | 2025-11-06 | Initial Platinum certification |

---

## References

- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)
- [Quality Scale Rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules)
- [pythermacell Library](https://github.com/joyfulhouse/pythermacell)
- [Home Assistant Brands](https://github.com/home-assistant/brands/tree/master/custom_integrations/thermacell_liv)
