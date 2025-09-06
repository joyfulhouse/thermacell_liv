"""Platform for switch integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the switch platform."""
    coordinator: ThermacellLivCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    switches = []
    
    # Create switch entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            switches.append(
                ThermacellLivSwitch(coordinator, node_id, device_name)
            )
    
    async_add_entities(switches, update_before_add=True)


class ThermacellLivSwitch(CoordinatorEntity[ThermacellLivCoordinator], SwitchEntity):
    """Representation of a Thermacell LIV switch."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_name = f"{node_name} {device_name}"
        self._attr_unique_id = f"{node_id}_{device_name}_switch"

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
        """Return true if switch is on."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("power", False) if device_data else False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self.coordinator.async_set_device_power(
            self._node_id, self._device_name, True
        )
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self.coordinator.async_set_device_power(
            self._node_id, self._device_name, False
        )
        if success:
            await self.coordinator.async_request_refresh()