"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from datetime import datetime
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
            # Refill life sensor
            sensors.append(
                ThermacellLivRefillSensor(coordinator, node_id, device_name)
            )
            # System status sensor
            sensors.append(
                ThermacellLivSystemStatusSensor(coordinator, node_id, device_name)
            )
            # System runtime sensor
            sensors.append(
                ThermacellLivSystemRuntimeSensor(coordinator, node_id, device_name)
            )
            # Connectivity status sensor
            sensors.append(
                ThermacellLivConnectivitySensor(coordinator, node_id, device_name)
            )
            # Last updated sensor
            sensors.append(
                ThermacellLivLastUpdatedSensor(coordinator, node_id, device_name)
            )
            # Error code sensor
            sensors.append(
                ThermacellLivErrorCodeSensor(coordinator, node_id, device_name)
            )
            # Hub ID (Serial) sensor
            sensors.append(
                ThermacellLivHubIdSensor(coordinator, node_id, device_name)
            )
            # Firmware version sensor
            sensors.append(
                ThermacellLivFirmwareSensor(coordinator, node_id, device_name)
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
        
        self._attr_has_entity_name = True
        self._attr_name = "Refill Life"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_refill_life"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_refill_life"
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"

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


class ThermacellLivSystemStatusSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV system status sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "System Status"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_system_status"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_system_status"
        self._attr_icon = "mdi:power"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            return device_data.get("system_status", "Unknown")
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return additional state attributes."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            return {
                "system_status_code": device_data.get("system_status_code", 0),
                "error_code": device_data.get("error_code", 0),
                "enable_repellers": device_data.get("power", False),
            }
        return None


class ThermacellLivSystemRuntimeSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV system runtime sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "System Runtime"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_system_runtime"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_system_runtime"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_suggested_unit_of_measurement = UnitOfTime.HOURS
        self._attr_icon = "mdi:timer-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
    def native_value(self) -> int | None:
        """Return the runtime in minutes."""
        node_data = self.coordinator.get_node_data(self._node_id)
        if node_data:
            return node_data.get("system_runtime", 0)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return additional state attributes with human-readable runtime."""
        node_data = self.coordinator.get_node_data(self._node_id)
        if node_data:
            runtime_minutes = node_data.get("system_runtime", 0)
            if runtime_minutes:
                # Convert minutes to days, hours, minutes format
                days = runtime_minutes // (24 * 60)
                hours = (runtime_minutes % (24 * 60)) // 60
                minutes = runtime_minutes % 60
                
                runtime_str = []
                if days > 0:
                    runtime_str.append(f"{days} day{'s' if days != 1 else ''}")
                if hours > 0:
                    runtime_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
                if minutes > 0:
                    runtime_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                
                formatted_runtime = ", ".join(runtime_str) if runtime_str else "0 minutes"
                
                return {
                    "formatted_runtime": formatted_runtime,
                    "total_minutes": runtime_minutes,
                    "total_hours": round(runtime_minutes / 60, 1),
                    "total_days": round(runtime_minutes / (24 * 60), 2),
                }
        return None


class ThermacellLivConnectivitySensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV connectivity sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "Connectivity"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_connectivity"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_connectivity"
        self._attr_icon = "mdi:wifi"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str | None:
        """Return the connectivity status."""
        node_data = self.coordinator.get_node_data(self._node_id)
        if node_data:
            return "Connected" if node_data.get("online", False) else "Disconnected"
        return "Unknown"


class ThermacellLivLastUpdatedSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV last polled sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "Last Polled"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_last_updated"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_last_updated"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
        # Always available since it shows coordinator-level timestamp, not device-specific data
        return True

    @property
    def native_value(self) -> datetime | None:
        """Return the last API poll/refresh timestamp."""
        if self.coordinator.last_update_success_time:
            return self.coordinator.last_update_success_time
        return None


class ThermacellLivErrorCodeSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV error code sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "Error Code"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_error_code"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_error_code"
        self._attr_icon = "mdi:alert-circle-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
    def native_value(self) -> int | None:
        """Return the error code."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("error_code", 0) if device_data else 0

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return additional state attributes."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            error_code = device_data.get("error_code", 0)
            return {
                "has_error": error_code > 0,
                "status": "Error" if error_code > 0 else "OK",
            }
        return None


class ThermacellLivHubIdSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV Hub ID (Serial) sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "Hub ID"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_hub_id"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_hub_id"
        self._attr_icon = "mdi:identifier"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
    def native_value(self) -> str | None:
        """Return the Hub ID (serial number)."""
        node_data = self.coordinator.get_node_data(self._node_id)
        return node_data.get("hub_serial") if node_data else None


class ThermacellLivFirmwareSensor(CoordinatorEntity[ThermacellLivCoordinator], SensorEntity):
    """Representation of a Thermacell LIV firmware version sensor."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name
        
        node_data = coordinator.get_node_data(node_id)
        node_name = node_data.get("name", "Unknown") if node_data else "Unknown"
        
        self._attr_has_entity_name = True
        self._attr_name = "Firmware Version"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_firmware"
        self.entity_id = f"sensor.{DOMAIN}_{device_name}_firmware"
        self._attr_icon = "mdi:chip"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
    def native_value(self) -> str | None:
        """Return the firmware version."""
        node_data = self.coordinator.get_node_data(self._node_id)
        return node_data.get("fw_version", "Unknown") if node_data else "Unknown"