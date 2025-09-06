"""Platform for button integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from .const import DOMAIN
    from .coordinator import ThermacellLivCoordinator
except ImportError:
    from const import DOMAIN
    from coordinator import ThermacellLivCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: ThermacellLivCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    buttons = []
    
    # Create button entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            buttons.append(
                ThermacellLivResetButton(coordinator, node_id, device_name)
            )
    
    async_add_entities(buttons, update_before_add=True)


class ThermacellLivResetButton(CoordinatorEntity[ThermacellLivCoordinator], ButtonEntity):
    """Representation of a Thermacell LIV refill reset button."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_reset_refill"
        self.entity_id = f"button.{DOMAIN}_{device_name}_reset_refill"
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        node_data = self.coordinator.get_node_data(self._node_id)
        device_info_dict = {
            "identifiers": {(DOMAIN, self._node_id)},
            "name": node_data.get("name", "Thermacell LIV"),
            "manufacturer": "Thermacell",
            "model": node_data.get("model", "LIV"),
            "sw_version": node_data.get("fw_version", "Unknown"),
        }
        
        # Add serial number if available
        hub_serial = node_data.get("hub_serial")
        if hub_serial:
            device_info_dict["serial_number"] = hub_serial
        
        return DeviceInfo(**device_info_dict)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.is_node_online(self._node_id)
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.async_reset_refill_life(
            self._node_id, self._device_name
        )
        if success:
            _LOGGER.info("Reset refill life for %s", self._attr_name)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to reset refill life for %s", self._attr_name)