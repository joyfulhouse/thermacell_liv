"""Base entity for Thermacell LIV integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from .const import DOMAIN
    from .coordinator import ThermacellLivCoordinator
except ImportError:
    from const import DOMAIN
    from coordinator import ThermacellLivCoordinator


class ThermacellLivEntity(CoordinatorEntity[ThermacellLivCoordinator]):
    """Base entity for Thermacell LIV devices."""

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
