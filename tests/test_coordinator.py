"""Tests for Thermacell LIV coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pythermacell import ThermacellClient, ThermacellDevice

from custom_components.thermacell_liv.coordinator import ThermacellLivCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_client():
    """Return a mock ThermacellClient."""
    client = AsyncMock(spec=ThermacellClient)
    return client


def create_mock_device(
    node_id: str = "node1",
    name: str = "Test Device",
    model: str = "thermacell-hub",
    firmware_version: str = "5.3.2",
    serial_number: str = "ABC123",
    is_online: bool = True,
    is_powered_on: bool = True,
    error: int = 0,
    system_status: int = 3,
    system_runtime: int | None = 120,
    led_brightness: int = 100,
    led_hue: int = 30,
    led_saturation: int = 100,
    refill_life: float = 75.0,
) -> MagicMock:
    """Create a mock ThermacellDevice."""
    device = MagicMock(spec=ThermacellDevice)
    device.node_id = node_id
    device.name = name
    device.model = model
    device.firmware_version = firmware_version
    device.serial_number = serial_number
    device.is_online = is_online
    device.is_powered_on = is_powered_on
    device.error = error
    device.system_status = system_status
    device.system_runtime = system_runtime
    device.led_brightness = led_brightness
    device.led_hue = led_hue
    device.led_saturation = led_saturation
    device.refill_life = refill_life

    # Make async methods return coroutines
    device.set_power = AsyncMock(return_value=None)
    device.set_led_power = AsyncMock(return_value=None)
    device.set_led_color = AsyncMock(return_value=None)
    device.set_led_brightness = AsyncMock(return_value=None)
    device.reset_refill = AsyncMock(return_value=None)
    device.refresh = AsyncMock(return_value=None)

    return device


@pytest.fixture
def coordinator(hass, mock_client):
    """Return a coordinator with mocked client."""
    return ThermacellLivCoordinator(hass, mock_client)


@pytest.fixture
def sample_devices():
    """Return sample ThermacellDevice mocks."""
    return [
        create_mock_device(
            node_id="node1",
            name="Living Room Thermacell",
            is_powered_on=True,
            system_status=3,
            refill_life=75.0,
            led_hue=30,
            led_brightness=100,
        ),
        create_mock_device(
            node_id="node2",
            name="Patio Thermacell",
            is_powered_on=False,
            system_status=1,
            refill_life=25.0,
            led_hue=120,
            led_brightness=50,
        ),
    ]


class TestThermacellLivCoordinator:
    """Test the ThermacellLivCoordinator class."""

    def test_init(self, hass, mock_client):
        """Test coordinator initialization."""
        coordinator = ThermacellLivCoordinator(hass, mock_client)

        assert coordinator.client is mock_client
        assert coordinator.nodes == {}
        assert coordinator.update_interval == timedelta(seconds=60)

    def test_init_custom_interval(self, hass, mock_client):
        """Test coordinator initialization with custom interval."""
        coordinator = ThermacellLivCoordinator(hass, mock_client, scan_interval=120)

        assert coordinator.update_interval == timedelta(seconds=120)

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator, sample_devices):
        """Test successful data update."""
        coordinator.client.get_devices.return_value = sample_devices

        result = await coordinator._async_update_data()

        assert len(result) == 2
        assert "node1" in result
        assert "node2" in result

        # Check node1 data structure
        node1_data = result["node1"]
        assert node1_data["id"] == "node1"
        assert node1_data["name"] == "Living Room Thermacell"
        assert node1_data["online"] is True
        assert "Living Room Thermacell" in node1_data["devices"]

        # Check device data structure
        device1_data = node1_data["devices"]["Living Room Thermacell"]
        assert device1_data["power"] is True
        assert device1_data["led_power"] is True
        assert device1_data["refill_life"] == 75
        assert device1_data["system_status"] == "Protected"  # Status code 3 = "Protected"
        assert device1_data["system_status_code"] == 3
        assert device1_data["error_code"] == 0

        # Verify client calls
        coordinator.client.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_update_data_no_devices(self, coordinator):
        """Test update with no devices returned."""
        coordinator.client.get_devices.return_value = []

        with pytest.raises(UpdateFailed, match="No devices found"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_api_error(self, coordinator):
        """Test update with API error."""
        coordinator.client.get_devices.side_effect = Exception("Network error")

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_offline_device(self, coordinator):
        """Test update with offline device."""
        device = create_mock_device(
            node_id="node1",
            name="Offline Device",
            is_online=False,
            is_powered_on=True,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        assert len(result) == 1
        node_data = result["node1"]
        assert node_data["online"] is False
        assert node_data["devices"]["Offline Device"]["system_status"] == "Not Connected"

    def test_get_node_data_success(self, coordinator):
        """Test getting node data successfully."""
        coordinator.data = {"node1": {"name": "Test Node", "online": True}}

        result = coordinator.get_node_data("node1")

        assert result == {"name": "Test Node", "online": True}

    def test_get_node_data_not_found(self, coordinator):
        """Test getting node data for non-existent node."""
        coordinator.data = {}

        result = coordinator.get_node_data("node1")

        assert result is None

    def test_get_node_data_no_data(self, coordinator):
        """Test getting node data when coordinator has no data."""
        coordinator.data = None

        result = coordinator.get_node_data("node1")

        assert result is None

    def test_get_device_data_success(self, coordinator):
        """Test getting device data successfully."""
        coordinator.data = {"node1": {"devices": {"Device1": {"power": True, "refill_life": 50}}}}

        result = coordinator.get_device_data("node1", "Device1")

        assert result == {"power": True, "refill_life": 50}

    def test_get_device_data_device_not_found(self, coordinator):
        """Test getting device data for non-existent device."""
        coordinator.data = {"node1": {"devices": {}}}

        result = coordinator.get_device_data("node1", "Device1")

        assert result is None

    def test_get_device_data_node_not_found(self, coordinator):
        """Test getting device data for non-existent node."""
        coordinator.data = {}

        result = coordinator.get_device_data("node1", "Device1")

        assert result is None

    def test_is_node_online_true(self, coordinator):
        """Test checking if node is online (true)."""
        coordinator.data = {"node1": {"online": True}}

        result = coordinator.is_node_online("node1")

        assert result is True

    def test_is_node_online_false(self, coordinator):
        """Test checking if node is online (false)."""
        coordinator.data = {"node1": {"online": False}}

        result = coordinator.is_node_online("node1")

        assert result is False

    def test_is_node_online_not_found(self, coordinator):
        """Test checking if non-existent node is online."""
        coordinator.data = {}

        result = coordinator.is_node_online("node1")

        assert result is False

    @pytest.mark.asyncio
    async def test_async_set_device_power_success(self, coordinator, sample_devices):
        """Test setting device power successfully."""
        device = sample_devices[0]
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "power": False,
                        "led_brightness": 100,
                        "led_power": False,
                    }
                }
            }
        }

        result = await coordinator.async_set_device_power("node1", "Living Room Thermacell", True)

        assert result is True
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["power"] is True
        device.set_power.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_async_set_device_power_failure(self, coordinator, sample_devices):
        """Test setting device power with API failure."""
        device = sample_devices[0]
        device.set_power.side_effect = Exception("API Error")
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "power": False,
                        "led_brightness": 100,
                        "led_power": False,
                    }
                }
            }
        }

        result = await coordinator.async_set_device_power("node1", "Living Room Thermacell", True)

        assert result is False
        # Should revert to original state
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["power"] is False

    @pytest.mark.asyncio
    async def test_async_set_device_power_device_not_found(self, coordinator):
        """Test setting device power when device not found."""
        coordinator._devices = {}
        coordinator.data = None

        result = await coordinator.async_set_device_power("node1", "Device1", True)

        assert result is False

    @pytest.mark.asyncio
    async def test_async_set_device_led_power_success(self, coordinator, sample_devices):
        """Test setting LED power successfully."""
        device = sample_devices[0]
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "led_power": False,
                        "power": True,
                        "led_brightness": 100,
                    }
                }
            }
        }

        result = await coordinator.async_set_device_led_power("node1", "Living Room Thermacell", True)

        assert result is True
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["led_power"] is True
        device.set_led_power.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_async_set_device_led_color_success(self, coordinator, sample_devices):
        """Test setting LED color successfully."""
        device = sample_devices[0]
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "led_color": {"r": 0, "g": 0, "b": 0},
                    }
                }
            }
        }

        result = await coordinator.async_set_device_led_color(
            "node1", "Living Room Thermacell", red=255, green=128, blue=64
        )

        assert result is True
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["led_color"] == {
            "r": 255,
            "g": 128,
            "b": 64,
        }
        device.set_led_color.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_device_led_brightness_success(self, coordinator, sample_devices):
        """Test setting LED brightness successfully."""
        device = sample_devices[0]
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "led_brightness": 100,
                        "led_brightness_pct": 50,
                        "led_power": True,
                        "power": True,
                    }
                }
            }
        }

        result = await coordinator.async_set_device_led_brightness("node1", "Living Room Thermacell", 200)

        assert result is True
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["led_brightness"] == 200
        device.set_led_brightness.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_reset_refill_life_success(self, coordinator, sample_devices):
        """Test resetting refill life successfully."""
        device = sample_devices[0]
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "refill_life": 25,
                    }
                }
            }
        }

        result = await coordinator.async_reset_refill_life("node1", "Living Room Thermacell")

        assert result is True
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["refill_life"] == 100
        device.reset_refill.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_reset_refill_life_failure(self, coordinator, sample_devices):
        """Test resetting refill life with API failure."""
        device = sample_devices[0]
        device.reset_refill.side_effect = Exception("API Error")
        coordinator._devices = {"node1": device}
        coordinator.data = {
            "node1": {
                "devices": {
                    "Living Room Thermacell": {
                        "refill_life": 25,
                    }
                }
            }
        }

        result = await coordinator.async_reset_refill_life("node1", "Living Room Thermacell")

        assert result is False
        # Refill life should remain unchanged
        assert coordinator.data["node1"]["devices"]["Living Room Thermacell"]["refill_life"] == 25

    @pytest.mark.asyncio
    async def test_system_status_mapping_protected(self, coordinator):
        """Test system status mapping for Protected state."""
        device = create_mock_device(
            is_powered_on=True,
            system_status=3,
            error=0,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Protected"

    @pytest.mark.asyncio
    async def test_system_status_mapping_warming_up(self, coordinator):
        """Test system status mapping for Warming Up state."""
        device = create_mock_device(
            is_powered_on=True,
            system_status=2,
            error=0,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Warming Up"

    @pytest.mark.asyncio
    async def test_system_status_mapping_off(self, coordinator):
        """Test system status mapping for Off state."""
        device = create_mock_device(
            is_powered_on=False,
            system_status=1,
            error=0,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Off"

    @pytest.mark.asyncio
    async def test_system_status_mapping_error(self, coordinator):
        """Test that a genuine error code takes precedence over a valid status."""
        device = create_mock_device(
            is_powered_on=True,
            system_status=3,
            error=1,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Error"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("is_powered_on", "system_status", "expected"),
        [
            (False, 1, "Off"),
            (True, 2, "Warming Up"),
            (True, 3, "Protected"),
        ],
    )
    async def test_system_status_benign_error_bit_ignored(self, coordinator, is_powered_on, system_status, expected):
        """Regression test for issue #17: benign error bit must not mask real status.

        Some hubs report a constant error value of 16777216 (0x01000000) while
        fully functional. The status sensor must reflect the valid system_status
        code instead of being stuck on "Error".
        """
        device = create_mock_device(
            is_powered_on=is_powered_on,
            system_status=system_status,
            error=16777216,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == expected

    @pytest.mark.asyncio
    async def test_system_status_real_error_alongside_benign_bit(self, coordinator):
        """A genuine error bit combined with the benign bit still reports Error."""
        device = create_mock_device(
            is_powered_on=True,
            system_status=3,
            error=16777216 | 1,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Error"

    @pytest.mark.asyncio
    async def test_system_status_unknown_code_without_error(self, coordinator):
        """An unrecognized status code with no error reports Unknown."""
        device = create_mock_device(
            is_powered_on=True,
            system_status=99,
            error=0,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Unknown"

    @pytest.mark.asyncio
    async def test_system_status_missing_code_is_not_reported_as_off(self, coordinator):
        """A hub that reports no status code must not be shown as 'Off'.

        The raw code is preserved rather than defaulted to 1, so a powered hub
        with an unknown status reports Unknown instead of a fabricated "Off".
        """
        device = create_mock_device(
            is_powered_on=True,
            system_status=None,
            error=0,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["system_status"] == "Unknown"
        assert device_data["system_status_code"] == 0

    @pytest.mark.asyncio
    async def test_model_name_conversion(self, coordinator):
        """Test that 'thermacell-hub' model is converted to user-friendly name."""
        device = create_mock_device(model="thermacell-hub")
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        assert result["node1"]["model"] == "Thermacell LIV Hub"

    @pytest.mark.asyncio
    async def test_led_power_state_logic(self, coordinator):
        """Test LED power state is correctly calculated."""
        # LED should only be on when hub is powered AND brightness > 0
        device = create_mock_device(
            is_powered_on=True,
            led_brightness=100,
        )
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["led_power"] is True

        # Now test with hub off
        device.is_powered_on = False
        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["led_power"] is False

        # Now test with brightness 0
        device.is_powered_on = True
        device.led_brightness = 0
        result = await coordinator._async_update_data()

        device_data = result["node1"]["devices"]["Test Device"]
        assert device_data["led_power"] is False

    @pytest.mark.asyncio
    async def test_system_runtime_none_passthrough(self, coordinator):
        """Test that None system_runtime from library is preserved."""
        device = create_mock_device(system_runtime=None)
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        assert result["node1"]["system_runtime"] is None

    @pytest.mark.asyncio
    async def test_system_runtime_value_passthrough(self, coordinator):
        """Test that system_runtime value from library is passed through unchanged."""
        device = create_mock_device(system_runtime=720)
        coordinator.client.get_devices.return_value = [device]

        result = await coordinator._async_update_data()

        assert result["node1"]["system_runtime"] == 720
