"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    """Set up the sensor platform."""
    coordinator: ThermacellLivCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = []
    
    # Create sensor entities for each device in each node
    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            sensors.append(
                ThermacellLivRefillSensor(coordinator, node_id, device_name)
            )
    
    async_add_entities(sensors, update_before_add=True)


class ThermacellLivRefillSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV refill life sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_name = f"{node_name} {device_name} Refill Life"
        self._attr_unique_id = f"{node_id}_{device_name}_refill_life"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:timer-outline"

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
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("refill_life", 0) if device_data else 0