"""Platform for light integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity

_LOGGER = logging.getLogger(__name__)

# Limit parallel updates to avoid overwhelming the API
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    coordinator: ThermacellLivCoordinator = config_entry.runtime_data

    lights = []

    # Create light entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            lights.append(ThermacellLivLight(coordinator, node_id, device_name))

    async_add_entities(lights, update_before_add=True)


class ThermacellLivLight(ThermacellLivEntity, LightEntity):
    """Representation of a Thermacell LIV LED light."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the light."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_has_entity_name = True
        self._attr_translation_key = "led"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_light"
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_supported_features = LightEntityFeature(0)

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("led_power", False) if device_data else False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            return device_data.get("led_brightness", 255)
        return 255

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
            await self.coordinator.async_set_device_led_color(self._node_id, self._device_name, red=r, green=g, blue=b)

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await self.coordinator.async_set_device_led_brightness(self._node_id, self._device_name, brightness)

        await self.coordinator.async_set_device_led_power(self._node_id, self._device_name, True)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.async_set_device_led_power(self._node_id, self._device_name, False)
