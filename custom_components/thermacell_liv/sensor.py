"""Platform for sensor integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONNECTIVITY_CONNECTED,
    CONNECTIVITY_DISCONNECTED,
    DOMAIN,
    STATUS_UNKNOWN,
)
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities

# Sensor platform doesn't make write operations, so parallel updates can be higher
PARALLEL_UPDATES = 0  # No limit on sensor updates


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    await async_setup_platform_entities(
        config_entry,
        async_add_entities,
        ThermacellLivRefillSensor,
        ThermacellLivSystemStatusSensor,
        ThermacellLivSystemRuntimeSensor,
        ThermacellLivConnectivitySensor,
        ThermacellLivErrorCodeSensor,
        ThermacellLivFirmwareSensor,
    )


class ThermacellLivRefillSensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV refill life sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "refill_life"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_refill_life"
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("refill_life", 0) if device_data else 0


class ThermacellLivSystemStatusSensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV system status sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "system_status"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_system_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:power"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            return device_data.get("system_status", STATUS_UNKNOWN)
        return STATUS_UNKNOWN

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            return {
                "system_status_code": device_data.get("system_status_code", 0),
                "error_code": device_data.get("error_code", 0),
                "enable_repellers": device_data.get("power", False),
            }
        return None


class ThermacellLivSystemRuntimeSensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV system runtime sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "system_runtime"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_system_runtime"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False  # Gold: entity-disabled-by-default
        self._attr_suggested_unit_of_measurement = UnitOfTime.HOURS
        self._attr_icon = "mdi:timer-outline"

    @property
    def native_value(self) -> int | None:
        """Return the runtime in minutes."""
        node_data = self.coordinator.get_node_data(self._node_id)
        if node_data:
            return node_data.get("system_runtime", 0)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
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


class ThermacellLivConnectivitySensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV connectivity sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "connectivity"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_connectivity"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False  # Gold: entity-disabled-by-default
        self._attr_icon = "mdi:wifi"

    @property
    def available(self) -> bool:
        """Return if entity is available (only requires coordinator success)."""
        # Connectivity sensor should always show status if coordinator updates succeed
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str | None:
        """Return the connectivity status."""
        node_data = self.coordinator.get_node_data(self._node_id)
        if node_data:
            return CONNECTIVITY_CONNECTED if node_data.get("online", False) else CONNECTIVITY_DISCONNECTED
        return STATUS_UNKNOWN


class ThermacellLivErrorCodeSensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV error code sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "error_code"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_error_code"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False  # Gold: entity-disabled-by-default
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def native_value(self) -> int | None:
        """Return the error code."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("error_code", 0) if device_data else 0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        if device_data:
            error_code = device_data.get("error_code", 0)
            return {
                "has_error": error_code > 0,
                "status": "Error" if error_code > 0 else "OK",
            }
        return None


class ThermacellLivFirmwareSensor(ThermacellLivEntity, SensorEntity):
    """Representation of a Thermacell LIV firmware version sensor."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_translation_key = "firmware_version"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_firmware"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False  # Gold: entity-disabled-by-default
        self._attr_icon = "mdi:chip"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        node_data = self.coordinator.get_node_data(self._node_id)
        return node_data.get("fw_version", "Unknown") if node_data else "Unknown"
