"""Data update coordinator for Thermacell LIV.

Platinum tier requirement: strict-typing, async-dependency
This module uses full type annotations and async operations for optimal performance.
"""

from __future__ import annotations

import colorsys
from datetime import datetime, timedelta
import logging
from typing import Any

from pythermacell import (
    AuthenticationError,
    ThermacellClient,
    ThermacellConnectionError,
    ThermacellDevice,
    ThermacellTimeoutError,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    BENIGN_ERROR_BITS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STATUS_ERROR,
    STATUS_NOT_CONNECTED,
    STATUS_OFF,
    STATUS_PROTECTED,
    STATUS_UNKNOWN,
    STATUS_WARMING_UP,
)
from .thermacell_types import DeviceParams, NodeData, RGBColor

_LOGGER = logging.getLogger(__name__)


def _convert_hsv_to_rgb(hue: int, saturation: int, brightness: int) -> RGBColor:
    """Convert HSV values to RGB color dictionary.

    Args:
        hue: Hue value (0-360)
        saturation: Saturation value (0-100)
        brightness: Brightness value (0-100)

    Returns:
        RGBColor TypedDict with r, g, b keys (0-255)
    """
    h_norm = hue / 360.0 if hue > 0 else 0
    s_norm = saturation / 100.0 if saturation > 0 else 1.0
    v_norm = brightness / 100.0
    r, g, b = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
    return RGBColor(
        r=int(r * 255),
        g=int(g * 255),
        b=int(b * 255),
    )


def has_hub_error(error: int) -> bool:
    """Return whether an error code represents a genuine hub fault.

    Args:
        error: Raw error code reported by the hub

    Returns:
        True if any non-benign error bit is set (see BENIGN_ERROR_BITS)
    """
    return bool(error & ~BENIGN_ERROR_BITS)


def _map_system_status(system_status: int, enable_repellers: bool, error: int) -> str:
    """Map system status code to human-readable text.

    Args:
        system_status: System status code (1-3; 0 when the hub reports none)
        enable_repellers: Whether repellers are enabled
        error: Error code (0 = no error; BENIGN_ERROR_BITS are ignored)

    Returns:
        Status text constant from const.py
    """
    if has_hub_error(error):
        return STATUS_ERROR
    if not enable_repellers:
        return STATUS_OFF
    if system_status == 1:
        return STATUS_OFF
    if system_status == 2:
        return STATUS_WARMING_UP
    if system_status == 3:
        return STATUS_PROTECTED
    return STATUS_UNKNOWN


def _convert_brightness_to_ha(brightness: int) -> int:
    """Convert Thermacell brightness (0-100) to Home Assistant (0-255)."""
    return int((brightness / 100) * 255) if brightness > 0 else 0


def _convert_brightness_to_thermacell(brightness: int) -> int:
    """Convert Home Assistant brightness (0-255) to Thermacell (0-100)."""
    return int((brightness / 255) * 100)


class ThermacellLivCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Thermacell LIV data from the API.

    Polling Strategy:
    - Default 60-second interval balances responsiveness with API conservation
    - Configurable via integration options (30-300 seconds)
    - Optimistic updates provide immediate UI feedback independent of polling
    """

    def __init__(
        self, hass: HomeAssistant, client: ThermacellClient, scan_interval: int = DEFAULT_SCAN_INTERVAL
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            client: pythermacell ThermacellClient instance
            scan_interval: Polling interval in seconds (default: 60, range: 30-300)
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.nodes: dict[str, dict[str, Any]] = {}
        self.last_update_success_time: datetime | None = None
        self._node_online_states: dict[str, bool] = {}  # Track online/offline transitions
        self._devices: dict[str, ThermacellDevice] = {}  # Cache ThermacellDevice objects

    def _device_to_node_data(self, device: ThermacellDevice) -> NodeData:
        """Convert a ThermacellDevice to our NodeData format.

        Args:
            device: ThermacellDevice from pythermacell

        Returns:
            NodeData TypedDict for internal use
        """
        # Get device state properties
        is_online = device.is_online
        is_powered = device.is_powered_on
        error = device.error or 0
        # Keep the raw code: a missing status must not masquerade as code 1 ("Off")
        system_status = device.system_status if device.system_status is not None else 0

        # Check if node is offline first - override all other status
        status_text = STATUS_NOT_CONNECTED if not is_online else _map_system_status(system_status, is_powered, error)

        # Get LED properties
        led_brightness = device.led_brightness or 0
        led_hue = device.led_hue or 0
        led_saturation = device.led_saturation or 100

        # Convert brightness and color
        ha_brightness = _convert_brightness_to_ha(led_brightness)
        led_color = _convert_hsv_to_rgb(led_hue, led_saturation, led_brightness)

        # Calculate LED power state
        led_power = is_powered and led_brightness > 0

        # Build device params
        device_params = DeviceParams(
            power=is_powered,
            led_power=led_power,
            led_brightness=ha_brightness,
            led_brightness_pct=led_brightness,
            led_color=led_color,
            refill_life=int(device.refill_life or 0),
            system_status=status_text,
            system_status_code=system_status,
            error_code=error,
            last_updated=0,  # Not available from device object
        )

        # Get device info
        model = device.model or "Thermacell LIV"
        if model == "thermacell-hub":
            model = "Thermacell LIV Hub"

        return NodeData(
            id=device.node_id,
            name=device.name,
            type="Thermacell LIV",
            fw_version=device.firmware_version or "Unknown",
            model=model,
            hub_serial=device.serial_number
            if device.serial_number and device.serial_number != "unknown"
            else device.node_id,
            system_runtime=device.system_runtime,
            online=is_online,
            devices={device.name: device_params},
        )

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get all devices from pythermacell client
            devices = await self.client.get_devices()

            if not devices:
                raise UpdateFailed("No devices found")

            updated_data: dict[str, Any] = {}
            previous_node_ids = set(self.nodes.keys()) if self.nodes else set()

            # Process each device
            for device in devices:
                node_id = device.node_id

                # Log new device discovery
                if node_id not in previous_node_ids:
                    _LOGGER.info(
                        "New Thermacell device discovered: %s (node_id: %s) - will be added automatically",
                        device.name,
                        node_id,
                    )

                # Cache the device object for later control operations
                self._devices[node_id] = device

                # Convert to our internal format
                node_data = self._device_to_node_data(device)
                updated_data[node_id] = node_data

                # Handle state transitions
                self._handle_node_state_change(node_id, device.name, device.is_online)

            self.nodes = updated_data
            self.last_update_success_time = dt_util.utcnow()
            _LOGGER.debug("Successfully updated data for %d device(s)", len(updated_data))
            return updated_data

        except AuthenticationError as err:
            _LOGGER.error("Authentication failed with Thermacell API: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except ThermacellConnectionError as err:
            _LOGGER.error("Connection error with Thermacell API: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err
        except ThermacellTimeoutError as err:
            _LOGGER.error("Timeout communicating with Thermacell API: %s", err)
            raise UpdateFailed(f"Timeout: {err}") from err
        except Exception as err:
            _LOGGER.error(
                "Error communicating with Thermacell API - integration unavailable: %s",
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def get_node_data(self, node_id: str) -> NodeData | None:
        """Get data for a specific node."""
        return self.data.get(node_id) if self.data else None

    def get_device_data(self, node_id: str, device_name: str) -> DeviceParams | None:
        """Get data for a specific device within a node."""
        node_data = self.get_node_data(node_id)
        if node_data:
            return node_data.get("devices", {}).get(device_name)
        return None

    def is_node_online(self, node_id: str) -> bool:
        """Check if a node is online."""
        node_data = self.get_node_data(node_id)
        return node_data.get("online", False) if node_data else False

    def _get_device(self, node_id: str) -> ThermacellDevice | None:
        """Get the ThermacellDevice object for a node."""
        return self._devices.get(node_id)

    def _get_device_data_safe(self, node_id: str, device_name: str) -> DeviceParams | None:
        """Safely get device data with null checks."""
        if not self.data or node_id not in self.data:
            return None
        devices = self.data[node_id].get("devices", {})
        return devices.get(device_name)

    async def async_set_device_power(self, node_id: str, device_name: str, power_on: bool) -> bool:
        """Set device power with optimistic update."""
        device = self._get_device(node_id)
        if not device:
            _LOGGER.warning("Device not found for node %s", node_id)
            return False

        # Apply optimistic update
        device_data = self._get_device_data_safe(node_id, device_name)
        original_power = device_data.get("power", False) if device_data else False

        if device_data:
            device_data["power"] = power_on
            brightness = device_data.get("led_brightness", 0)
            device_data["led_power"] = power_on and brightness > 0
            self.async_update_listeners()

        # Make API call
        try:
            await device.set_power(power_on)
            _LOGGER.debug("Successfully set power to %s for device %s", power_on, device_name)
            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to set power for device %s (node %s): %s - service unavailable",
                device_name,
                node_id,
                err,
            )
            # Revert optimistic update
            if device_data:
                device_data["power"] = original_power
                brightness = device_data.get("led_brightness", 0)
                device_data["led_power"] = original_power and brightness > 0
                self.async_update_listeners()
            return False

    async def async_set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Set device LED power with optimistic update."""
        device = self._get_device(node_id)
        if not device:
            _LOGGER.warning("Device not found for node %s", node_id)
            return False

        # Apply optimistic update
        device_data = self._get_device_data_safe(node_id, device_name)
        original_led_power = device_data.get("led_power", False) if device_data else False

        if device_data:
            hub_powered = device_data.get("power", False)
            brightness = device_data.get("led_brightness", 0)
            device_data["led_power"] = led_on and hub_powered and brightness > 0
            self.async_update_listeners()

        # Make API call
        try:
            await device.set_led_power(led_on)
            _LOGGER.debug("Successfully set LED power to %s for device %s", led_on, device_name)
            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to set LED power for device %s (node %s): %s - service unavailable",
                device_name,
                node_id,
                err,
            )
            # Revert optimistic update
            if device_data:
                device_data["led_power"] = original_led_power
                self.async_update_listeners()
            return False

    async def async_set_device_led_color(
        self, node_id: str, device_name: str, *, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color with optimistic update."""
        device = self._get_device(node_id)
        if not device:
            _LOGGER.warning("Device not found for node %s", node_id)
            return False

        # Convert RGB to HSV
        r_norm, g_norm, b_norm = red / 255.0, green / 255.0, blue / 255.0
        hue_val, _, brightness_val = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        hue = int(hue_val * 360)
        brightness = int(brightness_val * 100)

        # Apply optimistic update
        device_data = self._get_device_data_safe(node_id, device_name)
        original_color: RGBColor | None = None

        if device_data:
            original_color = device_data.get("led_color", RGBColor(r=255, g=255, b=255)).copy()
            device_data["led_color"] = RGBColor(r=red, g=green, b=blue)
            self.async_update_listeners()

        # Make API call
        try:
            await device.set_led_color(hue=hue, brightness=brightness)
            _LOGGER.debug(
                "Successfully set LED color to RGB(%d, %d, %d) for device %s",
                red,
                green,
                blue,
                device_name,
            )
            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to set LED color for device %s (node %s): %s - service unavailable",
                device_name,
                node_id,
                err,
            )
            # Revert optimistic update
            if device_data and original_color:
                device_data["led_color"] = original_color
                self.async_update_listeners()
            return False

    async def async_set_device_led_brightness(self, node_id: str, device_name: str, brightness: int) -> bool:
        """Set device LED brightness with optimistic update."""
        device = self._get_device(node_id)
        if not device:
            _LOGGER.warning("Device not found for node %s", node_id)
            return False

        # Convert HA brightness (0-255) to Thermacell (0-100)
        thermacell_brightness = _convert_brightness_to_thermacell(brightness)

        # Apply optimistic update
        device_data = self._get_device_data_safe(node_id, device_name)
        original_brightness: int | None = None
        original_brightness_pct: int | None = None
        original_led_power: bool | None = None

        if device_data:
            original_brightness = device_data.get("led_brightness", 255)
            original_brightness_pct = device_data.get("led_brightness_pct", 100)
            original_led_power = device_data.get("led_power", False)

            device_data["led_brightness"] = brightness
            device_data["led_brightness_pct"] = thermacell_brightness
            hub_powered = device_data.get("power", False)
            device_data["led_power"] = hub_powered and brightness > 0
            self.async_update_listeners()

        # Make API call
        try:
            await device.set_led_brightness(thermacell_brightness)
            _LOGGER.debug(
                "Successfully set LED brightness to %d for device %s",
                brightness,
                device_name,
            )
            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to set LED brightness for device %s (node %s): %s - service unavailable",
                device_name,
                node_id,
                err,
            )
            # Revert optimistic update
            if device_data and original_brightness is not None:
                device_data["led_brightness"] = original_brightness
                device_data["led_brightness_pct"] = original_brightness_pct  # type: ignore[typeddict-item]
                device_data["led_power"] = original_led_power  # type: ignore[typeddict-item]
                self.async_update_listeners()
            return False

    async def async_reset_refill_life(self, node_id: str, device_name: str) -> bool:
        """Reset refill life and update local data."""
        device = self._get_device(node_id)
        if not device:
            _LOGGER.warning("Device not found for node %s", node_id)
            return False

        try:
            await device.reset_refill()
            _LOGGER.info("Successfully reset refill life for device %s", device_name)

            # Update local cache immediately
            if self.data and node_id in self.data:
                device_data = self.data[node_id].get("devices", {}).get(device_name, {})
                device_data["refill_life"] = 100  # Assume 100% after reset
                self.async_update_listeners()

            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to reset refill life for device %s: %s - service unavailable",
                device_name,
                err,
            )
            return False
