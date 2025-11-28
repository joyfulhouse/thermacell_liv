"""Platform for switch integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities

# Limit parallel updates to avoid overwhelming the API
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    await async_setup_platform_entities(config_entry, async_add_entities, ThermacellLivSwitch)


class ThermacellLivSwitch(ThermacellLivEntity, SwitchEntity):
    """Representation of a Thermacell LIV switch."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_name = None  # Main entity uses device name only
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_switch"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("power", False) if device_data else False

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.async_set_device_power(self._node_id, self._device_name, True)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_set_device_power(self._node_id, self._device_name, False)
