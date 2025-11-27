"""Base entity for Thermacell LIV integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import ThermacellLivCoordinator

T = TypeVar("T", bound="ThermacellLivEntity")


def create_entities_for_devices(
    config_entry: ConfigEntry,
    entity_factory: Callable[[ThermacellLivCoordinator, str, str], T],
) -> list[T]:
    """Create entities for all devices in coordinator.

    This helper extracts the common pattern used across all platforms.

    Args:
        config_entry: The config entry containing runtime_data
        entity_factory: Factory function that creates entities

    Returns:
        List of created entities
    """
    coordinator: ThermacellLivCoordinator = config_entry.runtime_data["coordinator"]
    entities: list[T] = []

    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            entities.append(entity_factory(coordinator, node_id, device_name))

    return entities


async def async_setup_platform_entities(
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    *entity_factories: Callable[[ThermacellLivCoordinator, str, str], ThermacellLivEntity],
) -> None:
    """Set up entities for a platform using factory functions.

    Args:
        config_entry: The config entry containing runtime_data
        async_add_entities: Callback to add entities
        entity_factories: One or more factory functions to create entities
    """
    coordinator: ThermacellLivCoordinator = config_entry.runtime_data["coordinator"]
    entities: list[ThermacellLivEntity] = []

    for node_id, node_data in coordinator.data.items():
        for device_name in node_data.get("devices", {}):
            for factory in entity_factories:
                entities.append(factory(coordinator, node_id, device_name))

    async_add_entities(entities, update_before_add=True)


class ThermacellLivEntity(CoordinatorEntity["ThermacellLivCoordinator"]):
    """Base entity for Thermacell LIV devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._device_name = device_name

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
        return self.coordinator.last_update_success and self.coordinator.is_node_online(self._node_id)
