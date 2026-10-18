"""Configure the hub's IANA timezone through its advertised time service."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, setup_dynamic_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(_hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Expose timezone configuration only when writable."""
    coordinator = entry.runtime_data["coordinator"]
    setup_dynamic_entities(
        entry,
        async_add_entities,
        lambda: [
            ThermacellTimezone(coordinator, node_id, device.name)
            for node_id in coordinator.data
            if (device := coordinator.get_device(node_id))
            and device.services.supports("esp.service.time", "esp.param.tz") is True
        ],
    )


class ThermacellTimezone(ThermacellLivEntity, TextEntity):
    """Display the hub timezone and validate IANA names before writing."""

    _attr_translation_key = "timezone"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min = 1
    _attr_native_max = 255

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, name: str) -> None:
        super().__init__(coordinator, node_id, name)
        self._attr_unique_id = f"{DOMAIN}_{node_id}_timezone"

    @property
    def native_value(self) -> str | None:
        """Read the hub's current timezone."""
        device = self.coordinator.get_device(self._node_id)
        return device.services.timezone if device else None

    async def async_set_value(self, value: str) -> None:
        """Change the hub timezone."""
        await self.coordinator.features.command(self._node_id, "timezone", value)
