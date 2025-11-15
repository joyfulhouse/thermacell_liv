"""Tests for Thermacell LIV entity classes."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import UTC

from button import ThermacellLivRefreshButton, ThermacellLivResetButton
from const import DOMAIN
from coordinator import ThermacellLivCoordinator
from light import ThermacellLivLight
from sensor import (
    ThermacellLivConnectivitySensor,
    ThermacellLivErrorCodeSensor,
    ThermacellLivFirmwareSensor,
    ThermacellLivHubIdSensor,
    ThermacellLivRefillSensor,
    ThermacellLivSystemRuntimeSensor,
    ThermacellLivSystemStatusSensor,
)
from switch import ThermacellLivSwitch


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def config_entry():
    """Return a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    return entry


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator."""
    from datetime import datetime, timezone

    coordinator = MagicMock(spec=ThermacellLivCoordinator)
    coordinator.last_update_success = True
    coordinator.last_update_success_time = datetime.now(UTC)  # Timezone-aware
    coordinator.data = {
        "node1": {
            "id": "node1",
            "name": "Test Node",
            "model": "Thermacell LIV Hub",
            "fw_version": "5.3.2",
            "hub_serial": "ABC123456",
            "system_runtime": 120,  # minutes
            "online": True,
            "devices": {
                "Device1": {
                    "power": True,
                    "led_power": True,
                    "led_color": {"r": 255, "g": 128, "b": 0},
                    "refill_life": 75,
                    "system_status": "Protected",
                    "system_status_code": 3,
                    "error_code": 0,
                    "last_updated": 1234567890,
                }
            },
        }
    }
    coordinator.get_node_data.return_value = coordinator.data["node1"]
    coordinator.get_device_data.return_value = coordinator.data["node1"]["devices"]["Device1"]
    coordinator.is_node_online.return_value = True
    return coordinator


class TestThermacellLivSwitch:
    """Test the ThermacellLivSwitch class."""

    def test_init(self, mock_coordinator):
        """Test switch initialization."""
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch._node_id == "node1"
        assert switch._device_name == "Device1"
        assert switch._attr_name is None  # Main device entity has no name
        assert switch._attr_unique_id == f"{DOMAIN}_node1_Device1_switch"
        # entity_id is set by HA entity registry, not during __init__
        assert switch.entity_id is None

    def test_device_info(self, mock_coordinator):
        """Test switch device info."""
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        device_info = switch.device_info

        assert device_info["identifiers"] == {(DOMAIN, "node1")}
        assert device_info["name"] == "Test Node"
        assert device_info["manufacturer"] == "Thermacell"
        assert device_info["model"] == "Thermacell LIV Hub"
        assert device_info["sw_version"] == "5.3.2"
        assert device_info["serial_number"] == "ABC123456"

    def test_available_true(self, mock_coordinator):
        """Test switch availability (true)."""
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.available is True

    def test_available_false_coordinator_failed(self, mock_coordinator):
        """Test switch availability (false due to coordinator failure)."""
        mock_coordinator.last_update_success = False
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.available is False

    def test_available_false_node_offline(self, mock_coordinator):
        """Test switch availability (false due to node offline)."""
        mock_coordinator.is_node_online.return_value = False
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.available is False

    def test_is_on_true(self, mock_coordinator):
        """Test switch is_on property (true)."""
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.is_on is True

    def test_is_on_false(self, mock_coordinator):
        """Test switch is_on property (false)."""
        mock_coordinator.get_device_data.return_value = {"power": False}
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.is_on is False

    def test_is_on_no_device_data(self, mock_coordinator):
        """Test switch is_on property (no device data)."""
        mock_coordinator.get_device_data.return_value = None
        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator):
        """Test turning switch on successfully."""
        mock_coordinator.async_set_device_power = AsyncMock(return_value=True)

        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        await switch.async_turn_on()

        mock_coordinator.async_set_device_power.assert_called_once_with("node1", "Device1", True)

    @pytest.mark.asyncio
    async def test_async_turn_on_failure(self, mock_coordinator):
        """Test turning switch on with failure."""
        mock_coordinator.async_set_device_power = AsyncMock(return_value=False)

        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        await switch.async_turn_on()

        mock_coordinator.async_set_device_power.assert_called_once_with("node1", "Device1", True)

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator):
        """Test turning switch off successfully."""
        mock_coordinator.async_set_device_power = AsyncMock(return_value=True)

        switch = ThermacellLivSwitch(mock_coordinator, "node1", "Device1")

        await switch.async_turn_off()

        mock_coordinator.async_set_device_power.assert_called_once_with("node1", "Device1", False)


class TestThermacellLivLight:
    """Test the ThermacellLivLight class."""

    def test_init(self, mock_coordinator):
        """Test light initialization."""
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light._node_id == "node1"
        assert light._device_name == "Device1"
        assert light._attr_name == "LED"
        assert light._attr_unique_id == f"{DOMAIN}_node1_Device1_light"
        # entity_id is set by HA entity registry, not during __init__
        assert light.entity_id is None

    def test_is_on_true(self, mock_coordinator):
        """Test light is_on property (true)."""
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.is_on is True

    def test_is_on_false(self, mock_coordinator):
        """Test light is_on property (false)."""
        mock_coordinator.get_device_data.return_value = {"led_power": False}
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.is_on is False

    def test_rgb_color(self, mock_coordinator):
        """Test light RGB color property."""
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.rgb_color == (255, 128, 0)

    def test_rgb_color_no_device_data(self, mock_coordinator):
        """Test light RGB color property with no device data."""
        mock_coordinator.get_device_data.return_value = None
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.rgb_color == (255, 255, 255)  # Default white

    def test_brightness(self, mock_coordinator):
        """Test light brightness property."""
        mock_coordinator.get_device_data.return_value = {"led_brightness": 150}
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.brightness == 150

    def test_brightness_no_device_data(self, mock_coordinator):
        """Test light brightness property with no device data."""
        mock_coordinator.get_device_data.return_value = None
        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        assert light.brightness == 255  # Default max brightness

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator):
        """Test turning light on successfully."""
        mock_coordinator.async_set_device_led_power = AsyncMock(return_value=True)

        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        await light.async_turn_on()

        mock_coordinator.async_set_device_led_power.assert_called_once_with("node1", "Device1", True)

    @pytest.mark.asyncio
    async def test_async_turn_on_with_color(self, mock_coordinator):
        """Test turning light on with color change."""
        mock_coordinator.async_set_device_led_power = AsyncMock(return_value=True)
        mock_coordinator.async_set_device_led_color = AsyncMock(return_value=True)

        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        await light.async_turn_on(rgb_color=(255, 0, 128))

        mock_coordinator.async_set_device_led_color.assert_called_once_with(
            "node1", "Device1", red=255, green=0, blue=128
        )
        mock_coordinator.async_set_device_led_power.assert_called_once_with("node1", "Device1", True)

    @pytest.mark.asyncio
    async def test_async_turn_on_with_brightness(self, mock_coordinator):
        """Test turning light on with brightness change."""
        mock_coordinator.async_set_device_led_power = AsyncMock(return_value=True)
        mock_coordinator.async_set_device_led_brightness = AsyncMock(return_value=True)

        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        await light.async_turn_on(brightness=128)

        mock_coordinator.async_set_device_led_brightness.assert_called_once_with("node1", "Device1", 128)
        mock_coordinator.async_set_device_led_power.assert_called_once_with("node1", "Device1", True)

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator):
        """Test turning light off successfully."""
        mock_coordinator.async_set_device_led_power = AsyncMock(return_value=True)

        light = ThermacellLivLight(mock_coordinator, "node1", "Device1")

        await light.async_turn_off()

        mock_coordinator.async_set_device_led_power.assert_called_once_with("node1", "Device1", False)


class TestThermacellLivRefillSensor:
    """Test the ThermacellLivRefillSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "Refill Life"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_refill_life"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_native_unit_of_measurement == "%"

    def test_native_value(self, mock_coordinator):
        """Test sensor native value."""
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 75

    def test_native_value_no_device_data(self, mock_coordinator):
        """Test sensor native value with no device data."""
        mock_coordinator.get_device_data.return_value = None
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 0

    def test_native_value_missing_refill_life(self, mock_coordinator):
        """Test sensor native value with missing refill_life."""
        mock_coordinator.get_device_data.return_value = {"power": True}  # Missing refill_life
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 0

    def test_icon(self, mock_coordinator):
        """Test sensor icon."""
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.icon == "mdi:battery"

    def test_device_info(self, mock_coordinator):
        """Test sensor device info."""
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        device_info = sensor.device_info
        assert device_info is not None
        assert (DOMAIN, "node1") in device_info["identifiers"]
        assert device_info["name"] == "Test Node"
        assert device_info["manufacturer"] == "Thermacell"

    def test_available_true(self, mock_coordinator):
        """Test sensor available when coordinator successful and node online."""
        mock_coordinator.last_update_success = True
        mock_coordinator.is_node_online.return_value = True
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.available is True

    def test_available_false_coordinator_failed(self, mock_coordinator):
        """Test sensor unavailable when coordinator failed."""
        mock_coordinator.last_update_success = False
        mock_coordinator.is_node_online.return_value = True
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.available is False

    def test_available_false_node_offline(self, mock_coordinator):
        """Test sensor unavailable when node offline."""
        mock_coordinator.last_update_success = True
        mock_coordinator.is_node_online.return_value = False
        sensor = ThermacellLivRefillSensor(mock_coordinator, "node1", "Device1")

        assert sensor.available is False


class TestThermacellLivResetButton:
    """Test the ThermacellLivResetButton class."""

    def test_init(self, mock_coordinator):
        """Test button initialization."""
        button = ThermacellLivResetButton(mock_coordinator, "node1", "Device1")

        assert button._node_id == "node1"
        assert button._device_name == "Device1"
        assert button._attr_name == "Reset Refill"
        assert button._attr_unique_id == f"{DOMAIN}_node1_Device1_reset_refill"
        # entity_id is set by HA entity registry, not during __init__
        assert button.entity_id is None
        assert button._attr_icon == "mdi:refresh"

    @pytest.mark.asyncio
    async def test_async_press_success(self, mock_coordinator):
        """Test button press successfully."""
        mock_coordinator.async_reset_refill_life = AsyncMock(return_value=True)
        mock_coordinator.async_request_refresh = AsyncMock()

        button = ThermacellLivResetButton(mock_coordinator, "node1", "Device1")

        await button.async_press()

        mock_coordinator.async_reset_refill_life.assert_called_once_with("node1", "Device1")
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_press_failure(self, mock_coordinator):
        """Test button press with failure."""
        mock_coordinator.async_reset_refill_life = AsyncMock(return_value=False)
        mock_coordinator.async_request_refresh = AsyncMock()

        button = ThermacellLivResetButton(mock_coordinator, "node1", "Device1")

        await button.async_press()

        mock_coordinator.async_reset_refill_life.assert_called_once_with("node1", "Device1")
        mock_coordinator.async_request_refresh.assert_not_called()


class TestEntityPlatformSetup:
    """Test entity platform setup functions."""

    @pytest.fixture
    def mock_add_entities(self):
        """Return a mock add entities callback."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_switch_setup_entry(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test switch platform setup."""
        from switch import async_setup_entry

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        switches = mock_add_entities.call_args[0][0]
        assert len(switches) == 1
        assert isinstance(switches[0], ThermacellLivSwitch)

    @pytest.mark.asyncio
    async def test_light_setup_entry(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test light platform setup."""
        from light import async_setup_entry

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        lights = mock_add_entities.call_args[0][0]
        assert len(lights) == 1
        assert isinstance(lights[0], ThermacellLivLight)

    @pytest.mark.asyncio
    async def test_sensor_setup_entry(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test sensor platform setup."""
        from sensor import async_setup_entry

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        sensors = mock_add_entities.call_args[0][0]
        assert len(sensors) == 7  # All sensor types
        # Check we have all sensor types
        sensor_types = [type(sensor) for sensor in sensors]
        assert ThermacellLivRefillSensor in sensor_types
        assert ThermacellLivSystemStatusSensor in sensor_types
        assert ThermacellLivSystemRuntimeSensor in sensor_types
        assert ThermacellLivConnectivitySensor in sensor_types
        assert ThermacellLivErrorCodeSensor in sensor_types
        assert ThermacellLivHubIdSensor in sensor_types
        assert ThermacellLivFirmwareSensor in sensor_types

    @pytest.mark.asyncio
    async def test_button_setup_entry(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test button platform setup."""
        from button import async_setup_entry

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        buttons = mock_add_entities.call_args[0][0]
        assert len(buttons) == 2  # Reset refill + Refresh buttons
        button_types = [type(button) for button in buttons]
        assert ThermacellLivResetButton in button_types
        assert ThermacellLivRefreshButton in button_types

    @pytest.mark.asyncio
    async def test_setup_entry_multiple_devices(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test platform setup with multiple devices."""
        from switch import async_setup_entry

        # Add another device to the coordinator data
        mock_coordinator.data["node1"]["devices"]["Device2"] = {
            "power": False,
            "led_power": False,
            "led_color": {"r": 0, "g": 255, "b": 0},
            "refill_life": 50,
        }

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        switches = mock_add_entities.call_args[0][0]
        assert len(switches) == 2

    @pytest.mark.asyncio
    async def test_setup_entry_multiple_nodes(self, hass, config_entry, mock_coordinator, mock_add_entities):
        """Test platform setup with multiple nodes."""
        from switch import async_setup_entry

        # Add another node to the coordinator data
        mock_coordinator.data["node2"] = {
            "id": "node2",
            "name": "Patio Node",
            "devices": {"Device1": {"power": False, "refill_life": 25}},
        }

        config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, config_entry, mock_add_entities)

        switches = mock_add_entities.call_args[0][0]
        assert len(switches) == 2  # One device per node


class TestThermacellLivSystemStatusSensor:
    """Test the ThermacellLivSystemStatusSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor._node_id == "test_node"
        assert sensor._device_name == "test_device"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_node_test_device_system_status"
        assert sensor._attr_name == "System Status"

    def test_native_value_protected(self, mock_coordinator):
        """Test sensor value when system is protected (operational)."""
        mock_coordinator.get_device_data.return_value = {
            "power": True,
            "system_status": "Protected",
            "system_status_code": 3,
            "error_code": 0,
        }

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.native_value == "Protected"

    def test_native_value_warming_up(self, mock_coordinator):
        """Test sensor value when system is warming up."""
        mock_coordinator.get_device_data.return_value = {
            "power": True,
            "system_status": "Warming Up",
            "system_status_code": 2,
            "error_code": 0,
        }

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.native_value == "Warming Up"

    def test_native_value_off(self, mock_coordinator):
        """Test sensor value when system is off."""
        mock_coordinator.get_device_data.return_value = {
            "power": False,
            "system_status": "Off",
            "system_status_code": 1,
            "error_code": 0,
        }

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.native_value == "Off"

    def test_native_value_error(self, mock_coordinator):
        """Test sensor value when system has error."""
        mock_coordinator.get_device_data.return_value = {
            "power": True,
            "system_status": "Error",
            "system_status_code": 2,
            "error_code": 5,
        }

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.native_value == "Error"

    def test_native_value_no_device_data(self, mock_coordinator):
        """Test sensor value when no device data is available."""
        mock_coordinator.get_device_data.return_value = None

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.native_value == "Unknown"

    def test_extra_state_attributes(self, mock_coordinator):
        """Test extra state attributes."""
        mock_coordinator.get_device_data.return_value = {
            "power": True,
            "system_status": "On",
            "system_status_code": 3,
            "error_code": 0,
        }

        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        attributes = sensor.extra_state_attributes
        assert attributes == {
            "system_status_code": 3,
            "error_code": 0,
            "enable_repellers": True,
        }

    def test_icon(self, mock_coordinator):
        """Test sensor icon."""
        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "test_node", "test_device")

        assert sensor.icon == "mdi:power"

    def test_device_info(self, mock_coordinator):
        """Test sensor device info."""
        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "node1", "Device1")

        device_info = sensor.device_info
        assert device_info is not None
        assert (DOMAIN, "node1") in device_info["identifiers"]
        assert device_info["name"] == "Test Node"
        assert device_info["manufacturer"] == "Thermacell"

    def test_available(self, mock_coordinator):
        """Test sensor available."""
        mock_coordinator.last_update_success = True
        mock_coordinator.is_node_online.return_value = True
        sensor = ThermacellLivSystemStatusSensor(mock_coordinator, "node1", "Device1")

        assert sensor.available is True


class TestThermacellLivSystemRuntimeSensor:
    """Test the ThermacellLivSystemRuntimeSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "System Runtime"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_system_runtime"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_device_class == "duration"
        assert sensor._attr_native_unit_of_measurement == "min"

    def test_native_value(self, mock_coordinator):
        """Test sensor native value."""
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 120  # From mock data

    def test_native_value_no_node_data(self, mock_coordinator):
        """Test sensor native value with no node data."""
        mock_coordinator.get_node_data.return_value = None
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 0

    def test_extra_state_attributes_with_runtime(self, mock_coordinator):
        """Test extra state attributes with runtime data."""
        # Test with 2 days, 3 hours, 45 minutes = 2925 minutes
        mock_coordinator.get_node_data.return_value = {"system_runtime": 2925}
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["formatted_runtime"] == "2 days, 3 hours, 45 minutes"
        assert attrs["total_minutes"] == 2925
        assert attrs["total_hours"] == 48.8
        assert attrs["total_days"] == 2.03

    def test_extra_state_attributes_single_units(self, mock_coordinator):
        """Test extra state attributes with singular units."""
        # Test with 1 day, 1 hour, 1 minute = 1501 minutes
        mock_coordinator.get_node_data.return_value = {"system_runtime": 1501}
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["formatted_runtime"] == "1 day, 1 hour, 1 minute"

    def test_extra_state_attributes_zero_runtime(self, mock_coordinator):
        """Test extra state attributes with zero runtime."""
        mock_coordinator.get_node_data.return_value = {"system_runtime": 0}
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["formatted_runtime"] == "0 minutes"
        assert attrs["total_minutes"] == 0

    def test_extra_state_attributes_no_node_data(self, mock_coordinator):
        """Test extra state attributes with no node data."""
        mock_coordinator.get_node_data.return_value = None
        sensor = ThermacellLivSystemRuntimeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is None


class TestThermacellLivConnectivitySensor:
    """Test the ThermacellLivConnectivitySensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivConnectivitySensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "Connectivity"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_connectivity"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_entity_category == "diagnostic"

    def test_native_value_online(self, mock_coordinator):
        """Test sensor value when online."""
        sensor = ThermacellLivConnectivitySensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == "Connected"

    def test_native_value_offline(self, mock_coordinator):
        """Test sensor value when offline."""
        mock_coordinator.get_node_data.return_value = {"online": False}
        sensor = ThermacellLivConnectivitySensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == "Disconnected"


class TestThermacellLivErrorCodeSensor:
    """Test the ThermacellLivErrorCodeSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "Error Code"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_error_code"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_entity_category == "diagnostic"

    def test_native_value_no_error(self, mock_coordinator):
        """Test sensor value with no error."""
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 0

    def test_native_value_with_error(self, mock_coordinator):
        """Test sensor value with error."""
        mock_coordinator.get_device_data.return_value = {"error_code": 5}
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 5

    def test_native_value_no_device_data(self, mock_coordinator):
        """Test sensor value with no device data."""
        mock_coordinator.get_device_data.return_value = None
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == 0

    def test_extra_state_attributes_no_error(self, mock_coordinator):
        """Test extra state attributes with no error."""
        mock_coordinator.get_device_data.return_value = {"error_code": 0}
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["has_error"] is False
        assert attrs["status"] == "OK"

    def test_extra_state_attributes_with_error(self, mock_coordinator):
        """Test extra state attributes with error."""
        mock_coordinator.get_device_data.return_value = {"error_code": 5}
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["has_error"] is True
        assert attrs["status"] == "Error"

    def test_extra_state_attributes_no_device_data(self, mock_coordinator):
        """Test extra state attributes with no device data."""
        mock_coordinator.get_device_data.return_value = None
        sensor = ThermacellLivErrorCodeSensor(mock_coordinator, "node1", "Device1")

        attrs = sensor.extra_state_attributes
        assert attrs is None


class TestThermacellLivHubIdSensor:
    """Test the ThermacellLivHubIdSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivHubIdSensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "Hub ID"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_hub_id"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_entity_category == "diagnostic"

    def test_native_value(self, mock_coordinator):
        """Test sensor native value."""
        sensor = ThermacellLivHubIdSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == "ABC123456"

    def test_native_value_no_node_data(self, mock_coordinator):
        """Test sensor native value with no node data."""
        mock_coordinator.get_node_data.return_value = None
        sensor = ThermacellLivHubIdSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value is None


class TestThermacellLivFirmwareSensor:
    """Test the ThermacellLivFirmwareSensor class."""

    def test_init(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = ThermacellLivFirmwareSensor(mock_coordinator, "node1", "Device1")

        assert sensor._node_id == "node1"
        assert sensor._device_name == "Device1"
        assert sensor._attr_name == "Firmware Version"
        assert sensor._attr_unique_id == f"{DOMAIN}_node1_Device1_firmware"
        # entity_id is set by HA entity registry, not during __init__
        assert sensor.entity_id is None
        assert sensor._attr_entity_category == "diagnostic"

    def test_native_value(self, mock_coordinator):
        """Test sensor native value."""
        sensor = ThermacellLivFirmwareSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == "5.3.2"

    def test_native_value_no_node_data(self, mock_coordinator):
        """Test sensor native value with no node data."""
        mock_coordinator.get_node_data.return_value = None
        sensor = ThermacellLivFirmwareSensor(mock_coordinator, "node1", "Device1")

        assert sensor.native_value == "Unknown"


class TestThermacellLivRefreshButton:
    """Test the ThermacellLivRefreshButton class."""

    def test_init(self, mock_coordinator):
        """Test button initialization."""
        button = ThermacellLivRefreshButton(mock_coordinator, "node1", "Device1")

        assert button._node_id == "node1"
        assert button._device_name == "Device1"
        assert button._attr_name == "Refresh"
        assert button._attr_unique_id == f"{DOMAIN}_node1_Device1_refresh"
        # entity_id is set by HA entity registry, not during __init__
        assert button.entity_id is None
        assert button._attr_icon == "mdi:refresh"
        assert button._attr_entity_category == "diagnostic"

    @pytest.mark.asyncio
    async def test_async_press(self, mock_coordinator):
        """Test button press."""
        mock_coordinator.async_request_refresh = AsyncMock()

        button = ThermacellLivRefreshButton(mock_coordinator, "node1", "Device1")

        await button.async_press()

        mock_coordinator.async_request_refresh.assert_called_once()
