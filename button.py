"""Platform for button integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

try:
    from .const import DOMAIN
    from .coordinator import ThermacellLivCoordinator
    from .entity import ThermacellLivEntity
except ImportError:
    from const import DOMAIN
    from coordinator import ThermacellLivCoordinator
    from entity import ThermacellLivEntity

_LOGGER = logging.getLogger(__name__)


# Limit parallel button presses to avoid API conflicts
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: ThermacellLivCoordinator = config_entry.runtime_data

    buttons = []

    # Create button entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            buttons.append(ThermacellLivResetButton(coordinator, node_id, device_name))
            buttons.append(ThermacellLivRefreshButton(coordinator, node_id, device_name))

    async_add_entities(buttons, update_before_add=True)


class ThermacellLivResetButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refill reset button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_has_entity_name = True
        self._attr_name = "Reset Refill"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_reset_refill"
        self.entity_id = f"button.{DOMAIN}_{device_name}_reset_refill"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.async_reset_refill_life(self._node_id, self._device_name)
        if success:
            _LOGGER.info("Reset refill life for %s", self._attr_name)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to reset refill life for %s", self._attr_name)


class ThermacellLivRefreshButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refresh button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_has_entity_name = True
        self._attr_name = "Refresh"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_refresh"
        self.entity_id = f"button.{DOMAIN}_{device_name}_refresh"
        self._attr_icon = "mdi:refresh"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Refresh requested for %s", self._attr_name)
        await self.coordinator.async_request_refresh()
