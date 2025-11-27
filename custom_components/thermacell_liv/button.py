"""Platform for button integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities

_LOGGER = logging.getLogger(__name__)


# Limit parallel button presses to avoid API conflicts
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    await async_setup_platform_entities(
        config_entry, async_add_entities, ThermacellLivResetButton, ThermacellLivRefreshButton
    )


class ThermacellLivResetButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refill reset button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_translation_key = "reset_refill"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_reset_refill"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.async_reset_refill_life(self._node_id, self._device_name)
        if not success:
            _LOGGER.error("Failed to reset refill life for %s %s", self._node_id, self._device_name)


class ThermacellLivRefreshButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refresh button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_translation_key = "refresh"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_refresh"
        self._attr_icon = "mdi:refresh"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Refresh requested for %s %s", self._node_id, self._device_name)
        await self.coordinator.async_request_refresh()
