"""Data update coordinator for Thermacell LIV."""

from __future__ import annotations

import colorsys
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

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


def _convert_hsv_to_rgb(hue: int, brightness: int) -> Dict[str, int]:
    """Convert HSV values to RGB color dictionary.

    Args:
        hue: Hue value (0-360)
        brightness: Brightness value (0-100)

    Returns:
        Dictionary with r, g, b keys (0-255)
    """
    h_norm = hue / 360.0 if hue > 0 else 0
    s_norm = 1.0  # Assume full saturation
    v_norm = brightness / 100.0
    r, g, b = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
    return {
        "r": int(r * 255),
        "g": int(g * 255),
        "b": int(b * 255),
    }


def _map_system_status(system_status: int, enable_repellers: bool, error: int) -> str:
    """Map system status code to human-readable text.

    Args:
        system_status: System status code (1-3)
        enable_repellers: Whether repellers are enabled
        error: Error code (0 = no error)

    Returns:
        Status text: "Error", "Off", "Warming Up", "Protected", or "Unknown"
    """
    if error > 0:
        return "Error"
    if not enable_repellers:
        return "Off"
    if system_status == 1:
        return "Off"
    if system_status == 2:
        return "Warming Up"
    if system_status == 3:
        return "Protected"
    return "Unknown"


def _convert_brightness_to_ha(brightness: int) -> int:
    """Convert Thermacell brightness (0-100) to Home Assistant (0-255)."""
    return int((brightness / 100) * 255) if brightness > 0 else 0


def _convert_brightness_to_thermacell(brightness: int) -> int:
    """Convert Home Assistant brightness (0-255) to Thermacell (0-100)."""
    return int((brightness / 255) * 100)


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

    def _extract_device_info(self, config_data: Optional[Dict[str, Any]]) -> tuple[str, str]:
        """Extract firmware version and model from config data.

        Returns:
            Tuple of (firmware_version, model_name)
        """
        fw_version = "Unknown"
        model = "Thermacell LIV"

        if config_data and "info" in config_data:
            info = config_data["info"]
            fw_version = info.get("fw_version", "Unknown")
            raw_model = info.get("model", "thermacell-hub")
            # Convert technical model name to user-friendly display name
            model = "Thermacell LIV Hub" if raw_model == "thermacell-hub" else raw_model

        return fw_version, model

    def _parse_device_params(
        self, device_params: Dict[str, Any], connectivity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse device parameters into standardized format.

        Args:
            device_params: Raw device parameters from API
            connectivity: Connectivity data for timestamp

        Returns:
            Standardized device data dictionary
        """
        # Extract parameters
        hue = device_params.get("LED Hue", 0)
        brightness = device_params.get("LED Brightness", 100)
        system_status = device_params.get("System Status", 1)
        enable_repellers = device_params.get("Enable Repellers", False)
        error = device_params.get("Error", 0)

        # Convert color space
        led_color = _convert_hsv_to_rgb(hue, brightness)

        # Map status
        status_text = _map_system_status(system_status, enable_repellers, error)

        # Convert brightness
        ha_brightness = _convert_brightness_to_ha(brightness)

        # Calculate LED power state
        led_power = enable_repellers and brightness > 0

        return {
            "power": enable_repellers,
            "led_power": led_power,
            "led_brightness": ha_brightness,
            "led_brightness_pct": brightness,
            "led_color": led_color,
            "refill_life": device_params.get("Refill Life", 0),
            "system_status": status_text,
            "system_status_code": system_status,
            "error_code": error,
            "last_updated": connectivity.get("timestamp", 0) // 1000,
        }

    def _handle_node_state_change(self, node_id: str, node_name: str, is_online: bool) -> None:
        """Handle node online/offline state transitions.

        Args:
            node_id: Node identifier
            node_name: Node display name
            is_online: Current online status
        """
        previous_state = self._node_online_states.get(node_id)

        if previous_state is not None and previous_state != is_online:
            if is_online:
                _LOGGER.info("Node %s (%s) is now online", node_name, node_id)
                ir.async_delete_issue(self.hass, DOMAIN, f"device_offline_{node_name}")
            else:
                _LOGGER.warning(
                    "Node %s (%s) is now offline - entities will become unavailable",
                    node_name,
                    node_id,
                )
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

    async def _process_node(
        self, node: Dict[str, Any], previous_node_ids: set[str]
    ) -> Optional[Dict[str, Any]]:
        """Process a single node and return its data.

        Args:
            node: Raw node data from API
            previous_node_ids: Set of previously known node IDs

        Returns:
            Processed node data or None if processing failed
        """
        node_id = node.get("id")
        if not node_id:
            return None

        node_name = node.get("node_name", f"Unknown Node {node_id}")

        # Log new device discovery
        if node_id not in previous_node_ids:
            _LOGGER.info(
                "New Thermacell device discovered: %s (node_id: %s) - will be added automatically",
                node_name,
                node_id,
            )

        # Fetch node status and config
        status_data = await self.api.get_node_status(node_id)
        config_data = await self.api.get_node_config(node_id)

        if not status_data:
            return None

        # Extract basic info
        connectivity = status_data.get("connectivity", {})
        fw_version, model = self._extract_device_info(config_data)

        # Extract hub metadata from params
        params = node.get("params", {})
        hub_serial = None
        system_runtime = None

        if "LIV Hub" in params:
            device_params = params["LIV Hub"]
            if isinstance(device_params, dict):
                hub_serial = device_params.get("Hub ID")
                system_runtime = device_params.get("System Runtime", 0)

        # Build node info
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

        # Parse device parameters
        if "LIV Hub" in params:
            device_params = params["LIV Hub"]
            if isinstance(device_params, dict):
                device_name = device_params.get("Name", "LIV Hub")
                node_info["devices"][device_name] = self._parse_device_params(
                    device_params, connectivity
                )

        # Handle state transitions
        self._handle_node_state_change(node_id, node_name, node_info["online"])

        return node_info

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get all nodes from API
            nodes_data = await self.api.get_user_nodes()

            if not nodes_data:
                raise UpdateFailed("No nodes found")

            updated_data = {}
            previous_node_ids = set(self.nodes.keys()) if self.nodes else set()

            # Process each node
            for node in nodes_data:
                node_info = await self._process_node(node, previous_node_ids)
                if node_info:
                    updated_data[node_info["id"]] = node_info

            self.nodes = updated_data
            self.last_update_success_time = dt_util.utcnow()
            _LOGGER.debug("Successfully updated data for %d node(s)", len(updated_data))
            return updated_data

        except Exception as err:
            _LOGGER.error(
                "Error communicating with Thermacell API - integration unavailable: %s",
                err,
                exc_info=True,
            )
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

    def _get_device_data_safe(self, node_id: str, device_name: str) -> Optional[Dict[str, Any]]:
        """Safely get device data with null checks."""
        if not self.data or node_id not in self.data:
            return None
        devices = self.data[node_id].get("devices", {})
        return devices.get(device_name)

    async def _optimistic_update(
        self,
        node_id: str,
        device_name: str,
        update_fn: Callable[[Dict[str, Any]], None],
        api_call: Callable[[], Awaitable[bool]],
        revert_fn: Callable[[Dict[str, Any]], None],
        operation_name: str,
    ) -> bool:
        """Generic optimistic update handler.

        Args:
            node_id: Node identifier
            device_name: Device name
            update_fn: Function to apply optimistic update to device_data dict
            api_call: Async function to call API
            revert_fn: Function to revert changes on failure
            operation_name: Human-readable operation name for logging

        Returns:
            True if API call succeeded, False otherwise
        """
        # Apply optimistic update
        device_data = self._get_device_data_safe(node_id, device_name)
        if device_data:
            update_fn(device_data)
            self.async_update_listeners()

        # Make API call
        success = await api_call()

        # Revert on failure
        if not success:
            _LOGGER.warning(
                "Failed to %s for device %s (node %s) - service unavailable",
                operation_name,
                device_name,
                node_id,
            )
            device_data = self._get_device_data_safe(node_id, device_name)
            if device_data:
                revert_fn(device_data)
                self.async_update_listeners()
        else:
            _LOGGER.debug("Successfully %s for device %s", operation_name, device_name)

        return success

    async def async_set_device_power(self, node_id: str, device_name: str, power_on: bool) -> bool:
        """Set device power with optimistic update."""

        def update(data: Dict[str, Any]) -> None:
            data["power"] = power_on
            brightness = data.get("led_brightness", 0)
            data["led_power"] = power_on and brightness > 0

        def revert(data: Dict[str, Any]) -> None:
            data["power"] = not power_on
            brightness = data.get("led_brightness", 0)
            data["led_power"] = (not power_on) and brightness > 0

        return await self._optimistic_update(
            node_id,
            device_name,
            update,
            lambda: self.api.set_device_power(node_id, device_name, power_on),
            revert,
            f"set power to {'on' if power_on else 'off'}",
        )

    async def async_set_device_led_power(
        self, node_id: str, device_name: str, led_on: bool
    ) -> bool:
        """Set device LED power with optimistic update."""
        original_led_power = False

        def update(data: Dict[str, Any]) -> None:
            nonlocal original_led_power
            original_led_power = data.get("led_power", False)
            hub_powered = data.get("power", False)
            brightness = data.get("led_brightness", 0)
            data["led_power"] = led_on and hub_powered and brightness > 0

        def revert(data: Dict[str, Any]) -> None:
            data["led_power"] = original_led_power

        return await self._optimistic_update(
            node_id,
            device_name,
            update,
            lambda: self.api.set_device_led_power(node_id, device_name, led_on),
            revert,
            f"set LED power to {'on' if led_on else 'off'}",
        )

    async def async_set_device_led_color(
        self, node_id: str, device_name: str, *, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color with optimistic update."""
        original_color = None

        def update(data: Dict[str, Any]) -> None:
            nonlocal original_color
            original_color = data.get("led_color", {"r": 255, "g": 255, "b": 255}).copy()
            data["led_color"] = {"r": red, "g": green, "b": blue}

        def revert(data: Dict[str, Any]) -> None:
            if original_color:
                data["led_color"] = original_color

        return await self._optimistic_update(
            node_id,
            device_name,
            update,
            lambda: self.api.set_device_led_color(
                node_id, device_name, red=red, green=green, blue=blue
            ),
            revert,
            f"set LED color to RGB({red}, {green}, {blue})",
        )

    async def async_set_device_led_brightness(
        self, node_id: str, device_name: str, brightness: int
    ) -> bool:
        """Set device LED brightness with optimistic update."""
        original_brightness = None
        original_brightness_pct = None
        original_led_power = None

        def update(data: Dict[str, Any]) -> None:
            nonlocal original_brightness, original_brightness_pct, original_led_power
            original_brightness = data.get("led_brightness", 255)
            original_brightness_pct = data.get("led_brightness_pct", 100)
            original_led_power = data.get("led_power", False)

            data["led_brightness"] = brightness
            data["led_brightness_pct"] = _convert_brightness_to_thermacell(brightness)
            hub_powered = data.get("power", False)
            data["led_power"] = hub_powered and brightness > 0

        def revert(data: Dict[str, Any]) -> None:
            if original_brightness is not None:
                data["led_brightness"] = original_brightness
                data["led_brightness_pct"] = original_brightness_pct
                data["led_power"] = original_led_power

        return await self._optimistic_update(
            node_id,
            device_name,
            update,
            lambda: self.api.set_device_led_brightness(node_id, device_name, brightness),
            revert,
            f"set LED brightness to {brightness}",
        )

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
            _LOGGER.warning(
                "Failed to reset refill life for device %s - service unavailable",
                device_name
            )
        return success
