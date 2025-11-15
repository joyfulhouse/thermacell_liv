"""Data update coordinator for Thermacell LIV."""

from __future__ import annotations

import colorsys
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

try:
    from .api import ThermacellLivAPI
    from .const import DOMAIN
except ImportError:
    from api import ThermacellLivAPI
    from const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default polling interval: 60 seconds
# Justification (appropriate-polling Bronze requirement):
# - Thermacell API has no published rate limits; conservative 60s avoids potential issues
# - AC-powered devices with infrequent state changes don't require aggressive polling
# - Optimistic updates provide instant UI feedback, making polling interval less critical
# - User-configurable via options flow (30-300s range) for flexibility
UPDATE_INTERVAL = timedelta(seconds=60)


class ThermacellLivCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Thermacell LIV data from the API.

    Polling Strategy:
    - Default 60-second interval balances responsiveness with API conservation
    - Configurable via integration options (30-300 seconds)
    - Optimistic updates provide immediate UI feedback independent of polling
    """

    def __init__(self, hass: HomeAssistant, api: ThermacellLivAPI, scan_interval: int = 60) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Thermacell API client
            scan_interval: Polling interval in seconds (default: 60, range: 30-300)
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.last_update_success_time: Optional[datetime] = None
        self._node_online_states: Dict[str, bool] = {}  # Track online/offline transitions

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get all nodes (devices) from the API
            nodes_data = await self.api.get_user_nodes()

            if not nodes_data:
                raise UpdateFailed("No nodes found")

            updated_data = {}
            previous_node_ids = set(self.nodes.keys()) if self.nodes else set()

            # Process each node and get its current status
            # Dynamic device support (Gold tier): New devices are automatically discovered
            for node in nodes_data:
                node_id = node.get("id")
                if not node_id:
                    continue

                node_name = node.get("node_name", f"Unknown Node {node_id}")

                # Log new device discovery (Gold tier: dynamic-devices)
                if node_id not in previous_node_ids:
                    _LOGGER.info(
                        "New Thermacell device discovered: %s (node_id: %s) - will be added automatically",
                        node_name,
                        node_id,
                    )

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
                        raw_model = info.get("model", "thermacell-hub")
                        # Convert technical model name to user-friendly display name
                        if raw_model == "thermacell-hub":
                            model = "Thermacell LIV Hub"
                        else:
                            model = raw_model

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

                            # Determine system operational status
                            if error > 0:
                                status_text = "Error"
                            elif not enable_repellers:
                                status_text = "Off"
                            elif system_status == 1:
                                status_text = "Off"
                            elif system_status == 2:
                                status_text = "Warming Up"
                            elif system_status == 3:
                                status_text = "Protected"
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

                    # Log online/offline transitions (log-when-unavailable requirement)
                    is_online = node_info.get("online", False)
                    previous_state = self._node_online_states.get(node_id)

                    if previous_state is not None and previous_state != is_online:
                        if is_online:
                            _LOGGER.info("Node %s (%s) is now online", node_name, node_id)
                            # Delete repair issue if device comes back online
                            ir.async_delete_issue(self.hass, DOMAIN, f"device_offline_{node_name}")
                        else:
                            _LOGGER.warning(
                                "Node %s (%s) is now offline - entities will become unavailable", node_name, node_id
                            )
                            # Create repair issue for offline device
                            ir.async_create_issue(
                                self.hass,
                                DOMAIN,
                                f"device_offline_{node_name}",
                                is_fixable=False,
                                severity=ir.IssueSeverity.WARNING,
                                translation_key="device_offline",
                                translation_placeholders={"device_name": node_name},
                            )

                    self._node_online_states[node_id] = is_online
                    updated_data[node_id] = node_info

            self.nodes = updated_data
            # Update the last successful update timestamp (timezone-aware)
            self.last_update_success_time = dt_util.utcnow()
            _LOGGER.debug("Successfully updated data for %d node(s)", len(updated_data))
            return updated_data

        except Exception as err:
            _LOGGER.error("Error communicating with Thermacell API - integration unavailable: %s", err, exc_info=True)
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
        """Set device power with optimistic update."""
        # Optimistic update - update UI immediately
        if self.data and node_id in self.data:
            devices = self.data[node_id].get("devices", {})
            if device_name in devices:
                device_data = devices[device_name]
                device_data["power"] = power_on

                # Update LED power state based on hub power and brightness
                brightness = device_data.get("led_brightness", 0)
                device_data["led_power"] = power_on and brightness > 0

                # Immediately notify UI of change
                self.async_update_listeners()

        # Make API call in background
        success = await self.api.set_device_power(node_id, device_name, power_on)

        if not success:
            # Log service failure (log-when-unavailable requirement)
            _LOGGER.warning(
                "Failed to set power to %s for device %s (node %s) - service unavailable",
                "on" if power_on else "off",
                device_name,
                node_id,
            )

            # Revert optimistic update on failure
            if self.data and node_id in self.data:
                devices = self.data[node_id].get("devices", {})
                if device_name in devices:
                    device_data = devices[device_name]
                    device_data["power"] = not power_on  # Revert

                    # Revert LED power state
                    brightness = device_data.get("led_brightness", 0)
                    device_data["led_power"] = (not power_on) and brightness > 0

                    # Notify UI of revert
                    self.async_update_listeners()
        else:
            _LOGGER.debug("Successfully set power to %s for device %s", "on" if power_on else "off", device_name)

        return success

    async def async_set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Set device LED power with optimistic update."""
        # Optimistic update - update UI immediately
        original_led_power = False
        if self.data and node_id in self.data:
            devices = self.data[node_id].get("devices", {})
            if device_name in devices:
                device_data = devices[device_name]

                # Store original state for potential revert
                original_led_power = device_data.get("led_power", False)

                # LED should only be considered "on" if hub is powered AND brightness > 0
                hub_powered = device_data.get("power", False)
                brightness = device_data.get("led_brightness", 0)
                device_data["led_power"] = led_on and hub_powered and brightness > 0

                # Immediately notify UI of change
                self.async_update_listeners()

        # Make API call in background
        success = await self.api.set_device_led_power(node_id, device_name, led_on)

        if not success:
            _LOGGER.warning(
                "Failed to set LED power to %s for device %s - service unavailable",
                "on" if led_on else "off",
                device_name,
            )

            # Revert optimistic update on failure
            if self.data and node_id in self.data:
                devices = self.data[node_id].get("devices", {})
                if device_name in devices:
                    device_data = devices[device_name]
                    device_data["led_power"] = original_led_power  # Revert to original state

                    # Notify UI of revert
                    self.async_update_listeners()
        else:
            _LOGGER.debug("Successfully set LED power to %s for device %s", "on" if led_on else "off", device_name)

        return success

    async def async_set_device_led_color(
        self, node_id: str, device_name: str, *, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color with optimistic update."""
        # Optimistic update - update UI immediately
        original_color = None
        if self.data and node_id in self.data:
            devices = self.data[node_id].get("devices", {})
            if device_name in devices:
                device_data = devices[device_name]

                # Store original color for potential revert
                original_color = device_data.get("led_color", {"r": 255, "g": 255, "b": 255}).copy()

                # Update color immediately
                device_data["led_color"] = {"r": red, "g": green, "b": blue}

                # Immediately notify UI of change
                self.async_update_listeners()

        # Make API call in background
        success = await self.api.set_device_led_color(node_id, device_name, red=red, green=green, blue=blue)

        if not success and original_color:
            # Revert optimistic update on failure
            if self.data and node_id in self.data:
                devices = self.data[node_id].get("devices", {})
                if device_name in devices:
                    device_data = devices[device_name]
                    device_data["led_color"] = original_color  # Revert to original color

                    # Notify UI of revert
                    self.async_update_listeners()

        return success

    async def async_set_device_led_brightness(self, node_id: str, device_name: str, brightness: int) -> bool:
        """Set device LED brightness with optimistic update."""
        # Optimistic update - update UI immediately
        original_brightness = None
        original_brightness_pct = None
        original_led_power = None

        if self.data and node_id in self.data:
            devices = self.data[node_id].get("devices", {})
            if device_name in devices:
                device_data = devices[device_name]

                # Store original values for potential revert
                original_brightness = device_data.get("led_brightness", 255)
                original_brightness_pct = device_data.get("led_brightness_pct", 100)
                original_led_power = device_data.get("led_power", False)

                # Update brightness immediately
                device_data["led_brightness"] = brightness  # Already in HA format (0-255)
                device_data["led_brightness_pct"] = int((brightness / 255) * 100)  # Thermacell format

                # LED should only be considered "on" if hub is powered AND brightness > 0
                hub_powered = device_data.get("power", False)
                device_data["led_power"] = hub_powered and brightness > 0

                # Immediately notify UI of change
                self.async_update_listeners()

        # Make API call in background
        success = await self.api.set_device_led_brightness(node_id, device_name, brightness)

        if not success and original_brightness is not None:
            _LOGGER.warning(
                "Failed to set LED brightness to %d for device %s - service unavailable", brightness, device_name
            )

            # Revert optimistic update on failure
            if self.data and node_id in self.data:
                devices = self.data[node_id].get("devices", {})
                if device_name in devices:
                    device_data = devices[device_name]
                    device_data["led_brightness"] = original_brightness
                    device_data["led_brightness_pct"] = original_brightness_pct
                    device_data["led_power"] = original_led_power

                    # Notify UI of revert
                    self.async_update_listeners()
        else:
            _LOGGER.debug("Successfully set LED brightness to %d for device %s", brightness, device_name)

        return success

    async def async_reset_refill_life(self, node_id: str, device_name: str) -> bool:
        """Reset refill life and update local data."""
        success = await self.api.reset_refill_life(node_id, device_name)
        if success:
            _LOGGER.info("Successfully reset refill life for device %s", device_name)
            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["refill_life"] = 100  # Assume 100% after reset
        else:
            _LOGGER.warning("Failed to reset refill life for device %s - service unavailable", device_name)
        return success
