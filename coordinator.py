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
                
                # Get current status and config for this node
                status_data = await self.api.get_node_status(node_id)
                config_data = await self.api.get_node_config(node_id)
                
                if status_data:
                    # Extract device information and current state
                    connectivity = status_data.get("connectivity", {})
                    
                    # Get firmware version and device details from config
                    fw_version = "Unknown"
                    model = "Thermacell LIV"
                    hub_serial = None
                    
                    if config_data and "info" in config_data:
                        info = config_data["info"]
                        fw_version = info.get("fw_version", "Unknown")
                        model = info.get("model", "thermacell-hub")
                    
                    # Get Hub ID (serial) and runtime from params if available
                    params = node.get("params", {})
                    hub_serial = None
                    system_runtime = None
                    
                    if "LIV Hub" in params:
                        device_params = params["LIV Hub"]
                        if isinstance(device_params, dict):
                            hub_serial = device_params.get("Hub ID")
                            system_runtime = device_params.get("System Runtime", 0)  # Runtime in minutes
                    
                    node_info = {
                        "id": node_id,
                        "name": node_name,
                        "type": node.get("type", "Thermacell LIV"),
                        "fw_version": fw_version,
                        "model": model,
                        "hub_serial": hub_serial,
                        "system_runtime": system_runtime,
                        "online": connectivity.get("connected", False),
                        "devices": {},
                    }
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
                            
                            # Convert Thermacell brightness (0-100) to Home Assistant (0-255)
                            ha_brightness = int((brightness / 100) * 255) if brightness > 0 else 0
                            
                            # LED should only be considered "on" if hub is powered AND brightness > 0
                            hub_powered = device_params.get("Enable Repellers", False)
                            led_power = hub_powered and brightness > 0
                            
                            node_info["devices"][device_name] = {
                                "power": hub_powered,
                                "led_power": led_power,
                                "led_brightness": ha_brightness,  # Home Assistant brightness (0-255)
                                "led_brightness_pct": brightness,  # Thermacell brightness (0-100)
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
                
                # Update LED power state based on hub power and brightness
                brightness = device_data.get("led_brightness", 0)
                device_data["led_power"] = power_on and brightness > 0
            
            # Trigger a refresh to update the UI state
            await self.async_request_refresh()
        return success

    async def async_set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Set device LED power and update local data."""
        success = await self.api.set_device_led_power(node_id, device_name, led_on)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                
                # LED should only be considered "on" if hub is powered AND brightness > 0
                hub_powered = device_data.get("power", False)
                brightness = device_data.get("led_brightness", 0)
                device_data["led_power"] = led_on and hub_powered and brightness > 0
            
            # Trigger a refresh to update the UI state
            await self.async_request_refresh()
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
            
            # Trigger a refresh to update the UI state
            await self.async_request_refresh()
        return success

    async def async_set_device_led_brightness(self, node_id: str, device_name: str, brightness: int) -> bool:
        """Set device LED brightness and update local data."""
        success = await self.api.set_device_led_brightness(node_id, device_name, brightness)
        if success:
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["led_brightness"] = brightness  # Already in HA format (0-255)
                device_data["led_brightness_pct"] = int((brightness / 255) * 100)  # Thermacell format
                
                # LED should only be considered "on" if hub is powered AND brightness > 0
                hub_powered = device_data.get("power", False)
                device_data["led_power"] = hub_powered and brightness > 0
            
            # Trigger a refresh to update the UI state
            await self.async_request_refresh()
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