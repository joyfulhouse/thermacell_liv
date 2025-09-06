"""Data update coordinator for Thermacell LIV."""
from __future__ import annotations

import asyncio
import colorsys
from datetime import timedelta
import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

try:
    from .api import ThermacellLivAPI
    from .const import DOMAIN
except ImportError:
    from api import ThermacellLivAPI
    from const import DOMAIN

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
                    connectivity = status_data.get("connectivity", {})
                    node_info = {
                        "id": node_id,
                        "name": node_name,
                        "type": node.get("type", "Thermacell LIV"),
                        "fw_version": node.get("fw_version", "Unknown"),
                        "model": node.get("model", "Thermacell LIV"),
                        "online": connectivity.get("connected", False),
                        "devices": {},
                    }
                    
                    # Process device parameters from the node's params
                    params = node.get("params", {})
                    if "LIV Hub" in params:
                        device_params = params["LIV Hub"]
                        if isinstance(device_params, dict):
                            # Create a device entry for the LIV Hub
                            device_name = device_params.get("Name", "LIV Hub")
                            
                            # Convert LED Hue and Brightness to RGB for compatibility
                            hue = device_params.get("LED Hue", 0)
                            brightness = device_params.get("LED Brightness", 100)
                            
                            # Convert HSV to RGB
                            h_norm = hue / 360.0 if hue > 0 else 0
                            s_norm = 1.0  # Assume full saturation
                            v_norm = brightness / 100.0
                            r, g, b = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
                            
                            # Interpret system status
                            system_status = device_params.get("System Status", 1)
                            enable_repellers = device_params.get("Enable Repellers", False)
                            error = device_params.get("Error", 0)
                            
                            if error > 0:
                                status_text = "Error"
                            elif not enable_repellers:
                                status_text = "Off"
                            elif system_status == 1:
                                status_text = "Off"
                            elif system_status == 2:
                                status_text = "Warming Up"
                            elif system_status == 3:
                                status_text = "On"
                            else:
                                status_text = "Unknown"
                            
                            node_info["devices"][device_name] = {
                                "power": device_params.get("Enable Repellers", False),
                                "led_power": brightness > 0,
                                "led_color": {
                                    "r": int(r * 255),
                                    "g": int(g * 255),
                                    "b": int(b * 255),
                                },
                                "refill_life": device_params.get("Refill Life", 0),
                                "system_status": status_text,
                                "system_status_code": system_status,
                                "error_code": error,
                                "last_updated": connectivity.get("timestamp", 0) // 1000,  # Convert to seconds
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