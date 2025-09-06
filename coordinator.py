"""Data update coordinator for Thermacell LIV."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ThermacellLivAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=60)  # Poll every 60 seconds


class ThermacellLivCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Thermacell LIV data from the API."""

    def __init__(self, hass: HomeAssistant, api: ThermacellLivAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.nodes: Dict[str, Dict[str, Any]] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get all nodes (devices) from the API
            nodes_data = await self.api.get_user_nodes()
            
            if not nodes_data:
                raise UpdateFailed("No nodes found")

            updated_data = {}
            
            # Process each node and get its current status
            for node in nodes_data:
                node_id = node.get("id")
                if not node_id:
                    continue
                
                node_name = node.get("node_name", f"Unknown Node {node_id}")
                
                # Get current status for this node
                status_data = await self.api.get_node_status(node_id)
                
                if status_data:
                    # Extract device information and current state
                    node_info = {
                        "id": node_id,
                        "name": node_name,
                        "type": node.get("type", "Thermacell LIV"),
                        "fw_version": node.get("fw_version", "Unknown"),
                        "model": node.get("model", "Thermacell LIV"),
                        "online": status_data.get("node_status", False),
                        "devices": {},
                    }
                    
                    # Process device parameters
                    if "param" in status_data:
                        for device_name, device_params in status_data["param"].items():
                            if isinstance(device_params, dict):
                                node_info["devices"][device_name] = {
                                    "power": device_params.get("Power", False),
                                    "led_power": device_params.get("LED", {}).get("Power", False),
                                    "led_color": {
                                        "r": device_params.get("LED", {}).get("R", 255),
                                        "g": device_params.get("LED", {}).get("G", 255),
                                        "b": device_params.get("LED", {}).get("B", 255),
                                    },
                                    "refill_life": device_params.get("RefillLife", 0),
                                    "last_updated": device_params.get("timestamp", 0),
                                }
                    
                    updated_data[node_id] = node_info
                    
            self.nodes = updated_data
            return updated_data

        except Exception as err:
            _LOGGER.error("Error communicating with Thermacell API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def get_node_data(self, node_id: str) -> Dict[str, Any] | None:
        """Get data for a specific node."""
        return self.data.get(node_id) if self.data else None

    def get_device_data(self, node_id: str, device_name: str) -> Dict[str, Any] | None:
        """Get data for a specific device within a node."""
        node_data = self.get_node_data(node_id)
        if node_data:
            return node_data.get("devices", {}).get(device_name)
        return None

    def is_node_online(self, node_id: str) -> bool:
        """Check if a node is online."""
        node_data = self.get_node_data(node_id)
        return node_data.get("online", False) if node_data else False

    async def async_set_device_power(self, node_id: str, device_name: str, power_on: bool) -> bool:
        """Set device power and update local data."""
        success = await self.api.set_device_power(node_id, device_name, power_on)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["power"] = power_on
        return success

    async def async_set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Set device LED power and update local data."""
        success = await self.api.set_device_led_power(node_id, device_name, led_on)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["led_power"] = led_on
        return success

    async def async_set_device_led_color(
        self, node_id: str, device_name: str, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color and update local data."""
        success = await self.api.set_device_led_color(node_id, device_name, red, green, blue)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["led_color"] = {"r": red, "g": green, "b": blue}
        return success

    async def async_reset_refill_life(self, node_id: str, device_name: str) -> bool:
        """Reset refill life and update local data."""
        success = await self.api.reset_refill_life(node_id, device_name)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["refill_life"] = 100  # Assume 100% after reset
        return success