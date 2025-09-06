"""Platform for light integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    coordinator: ThermacellLivCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    lights = []
    
    # Create light entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            lights.append(
                ThermacellLivLight(coordinator, node_id, device_name)
            )
    
    async_add_entities(lights, update_before_add=True)


class ThermacellLivLight(CoordinatorEntity[ThermacellLivCoordinator], LightEntity):
    """Representation of a Thermacell LIV LED light."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_name = f"{node_name} {device_name} LED"
        self._attr_unique_id = f"{node_id}_{device_name}_light"
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        node_data = self.coordinator.get_node_data(self._node_id)
        return DeviceInfo(
            identifiers={(DOMAIN, self._node_id)},
            name=node_data.get("name", "Thermacell LIV"),
            manufacturer="Thermacell",
            model=node_data.get("model", "LIV"),
            sw_version=node_data.get("fw_version", "Unknown"),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.is_node_online(self._node_id)
        )

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("led_power", False) if device_data else False

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data and "led_color" in device_data:
            color = device_data["led_color"]
            return (color.get("r", 255), color.get("g", 255), color.get("b", 255))
        return (255, 255, 255)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            await self.coordinator.async_set_device_led_color(
                self._node_id, self._device_name, r, g, b
            )
        
        success = await self.coordinator.async_set_device_led_power(
            self._node_id, self._device_name, True
        )
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        success = await self.coordinator.async_set_device_led_power(
            self._node_id, self._device_name, False
        )
        if success:
            await self.coordinator.async_request_refresh()