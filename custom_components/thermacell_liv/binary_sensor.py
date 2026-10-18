"""Refill presence, low refill, and shutdown diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, setup_dynamic_entities

PARALLEL_UPDATES = 0


async def async_setup_entry(_hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up state-based diagnostic flags for each hub."""
    coordinator = entry.runtime_data["coordinator"]
    setup_dynamic_entities(
        entry,
        async_add_entities,
        lambda: [
            ThermacellDiagnosticFlag(coordinator, node_id, data.get("name", node_id), key)
            for node_id, data in coordinator.data.items()
            for key in ("missing_cartridge", "low_refill", "refill_drain", "power_mismatch")
        ],
    )


class ThermacellDiagnosticFlag(ThermacellLivEntity, BinarySensorEntity):
    """Expose unknown separately from a healthy or empty reading."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, name: str, key: str) -> None:
        super().__init__(coordinator, node_id, name)
        self.key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{key}"

    @property
    def is_on(self) -> bool | None:
        """Read current, polled evidence."""
        features = self.coordinator.features
        device = self.coordinator.get_device(self._node_id)
        if device is None:
            return None
        if self.key == "missing_cartridge":
            present = device.cartridge_present
            return not present if present is not None else None
        if self.key == "low_refill":
            return device.refill_life <= 10 if device.refill_life is not None else None
        if self.key == "refill_drain":
            return features.anomalies.get(self._node_id)
        if features.history.get(self._node_id, {}).get("shutdown_failed"):
            return True
        reported = features.reported.get(self._node_id)
        requested = features.audit.get(self._node_id, {}).get("requested_power")
        return requested != reported if requested is not None and reported is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Describe the alert threshold so it can be used in automations."""
        if self.key == "refill_drain":
            return {"minimum_off_minutes": 10, "minimum_drop_percentage_points": 2}
        if self.key == "low_refill":
            return {"threshold_percent": 10}
        return {}
