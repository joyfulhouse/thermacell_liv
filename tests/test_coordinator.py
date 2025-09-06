"""Tests for Thermacell LIV coordinator."""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.thermacell_liv.coordinator import ThermacellLivCoordinator
from custom_components.thermacell_liv.api import ThermacellLivAPI


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_api():
    """Return a mock API client."""
    api = AsyncMock(spec=ThermacellLivAPI)
    return api


@pytest.fixture
def coordinator(hass, mock_api):
    """Return a coordinator with mocked API."""
    return ThermacellLivCoordinator(hass, mock_api)


@pytest.fixture
def sample_nodes_data():
    """Return sample nodes data from API."""
    return [
        {
            "id": "node1",
            "node_name": "Living Room Thermacell",
            "type": "Thermacell LIV",
            "fw_version": "1.0.0",
            "model": "LIV"
        },
        {
            "id": "node2",
            "node_name": "Patio Thermacell",
            "type": "Thermacell LIV",
            "fw_version": "1.1.0",
            "model": "LIV"
        }
    ]


@pytest.fixture
def sample_status_data():
    """Return sample status data for a node."""
    return {
        "node_status": True,
        "param": {
            "Device1": {
                "Power": True,
                "LED": {
                    "Power": True,
                    "R": 255,
                    "G": 128,
                    "B": 0
                },
                "RefillLife": 75,
                "timestamp": 1234567890
            }
        }
    }


class TestThermacellLivCoordinator:
    """Test the ThermacellLivCoordinator class."""

    def test_init(self, hass, mock_api):
        """Test coordinator initialization."""
        coordinator = ThermacellLivCoordinator(hass, mock_api)
        
        assert coordinator.api is mock_api
        assert coordinator.nodes == {}
        assert coordinator.update_interval == timedelta(seconds=60)

    async def test_async_update_data_success(self, coordinator, sample_nodes_data, sample_status_data):
        """Test successful data update."""
        coordinator.api.get_user_nodes.return_value = sample_nodes_data
        coordinator.api.get_node_status.return_value = sample_status_data
        
        result = await coordinator._async_update_data()
        
        assert len(result) == 2
        assert "node1" in result
        assert "node2" in result
        
        # Check node1 data structure
        node1_data = result["node1"]
        assert node1_data["id"] == "node1"
        assert node1_data["name"] == "Living Room Thermacell"
        assert node1_data["online"] is True
        assert "Device1" in node1_data["devices"]
        
        # Check device data structure
        device1_data = node1_data["devices"]["Device1"]
        assert device1_data["power"] is True
        assert device1_data["led_power"] is True
        assert device1_data["led_color"] == {"r": 255, "g": 128, "b": 0}
        assert device1_data["refill_life"] == 75
        assert device1_data["last_updated"] == 1234567890
        
        # Verify API calls
        coordinator.api.get_user_nodes.assert_called_once()
        assert coordinator.api.get_node_status.call_count == 2

    async def test_async_update_data_no_nodes(self, coordinator):
        """Test update with no nodes returned."""
        coordinator.api.get_user_nodes.return_value = []
        
        with pytest.raises(UpdateFailed, match="No nodes found"):
            await coordinator._async_update_data()

    async def test_async_update_data_api_error(self, coordinator):
        """Test update with API error."""
        coordinator.api.get_user_nodes.side_effect = Exception("Network error")
        
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

    async def test_async_update_data_node_without_id(self, coordinator):
        """Test update with node missing ID."""
        nodes_data = [{"node_name": "Test Node"}]  # Missing 'id' field
        coordinator.api.get_user_nodes.return_value = nodes_data
        
        result = await coordinator._async_update_data()
        
        assert result == {}  # Should skip nodes without ID

    async def test_async_update_data_status_failure(self, coordinator, sample_nodes_data):
        """Test update when node status fetch fails."""
        coordinator.api.get_user_nodes.return_value = sample_nodes_data
        coordinator.api.get_node_status.return_value = None
        
        result = await coordinator._async_update_data()
        
        assert result == {}  # Should skip nodes without status

    async def test_async_update_data_empty_status(self, coordinator, sample_nodes_data):
        """Test update with empty status data."""
        coordinator.api.get_user_nodes.return_value = [sample_nodes_data[0]]  # Just one node
        coordinator.api.get_node_status.return_value = {"node_status": False}  # No params
        
        result = await coordinator._async_update_data()
        
        assert len(result) == 1
        node_data = result["node1"]
        assert node_data["online"] is False
        assert node_data["devices"] == {}

    def test_get_node_data_success(self, coordinator):
        """Test getting node data successfully."""
        coordinator.data = {
            "node1": {"name": "Test Node", "online": True}
        }
        
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
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"power": True, "refill_life": 50}
                }
            }
        }
        
        result = coordinator.get_device_data("node1", "Device1")
        
        assert result == {"power": True, "refill_life": 50}

    def test_get_device_data_device_not_found(self, coordinator):
        """Test getting device data for non-existent device."""
        coordinator.data = {
            "node1": {"devices": {}}
        }
        
        result = coordinator.get_device_data("node1", "Device1")
        
        assert result is None

    def test_get_device_data_node_not_found(self, coordinator):
        """Test getting device data for non-existent node."""
        coordinator.data = {}
        
        result = coordinator.get_device_data("node1", "Device1")
        
        assert result is None

    def test_is_node_online_true(self, coordinator):
        """Test checking if node is online (true)."""
        coordinator.data = {
            "node1": {"online": True}
        }
        
        result = coordinator.is_node_online("node1")
        
        assert result is True

    def test_is_node_online_false(self, coordinator):
        """Test checking if node is online (false)."""
        coordinator.data = {
            "node1": {"online": False}
        }
        
        result = coordinator.is_node_online("node1")
        
        assert result is False

    def test_is_node_online_not_found(self, coordinator):
        """Test checking if non-existent node is online."""
        coordinator.data = {}
        
        result = coordinator.is_node_online("node1")
        
        assert result is False

    async def test_async_set_device_power_success(self, coordinator):
        """Test setting device power successfully."""
        coordinator.api.set_device_power.return_value = True
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"power": False}
                }
            }
        }
        
        result = await coordinator.async_set_device_power("node1", "Device1", True)
        
        assert result is True
        assert coordinator.data["node1"]["devices"]["Device1"]["power"] is True
        coordinator.api.set_device_power.assert_called_once_with("node1", "Device1", True)

    async def test_async_set_device_power_failure(self, coordinator):
        """Test setting device power with API failure."""
        coordinator.api.set_device_power.return_value = False
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"power": False}
                }
            }
        }
        
        result = await coordinator.async_set_device_power("node1", "Device1", True)
        
        assert result is False
        assert coordinator.data["node1"]["devices"]["Device1"]["power"] is False  # Unchanged

    async def test_async_set_device_power_no_data(self, coordinator):
        """Test setting device power with no local data."""
        coordinator.api.set_device_power.return_value = True
        coordinator.data = None
        
        result = await coordinator.async_set_device_power("node1", "Device1", True)
        
        assert result is True  # API call succeeded, but no local update

    async def test_async_set_device_led_power_success(self, coordinator):
        """Test setting LED power successfully."""
        coordinator.api.set_device_led_power.return_value = True
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"led_power": False}
                }
            }
        }
        
        result = await coordinator.async_set_device_led_power("node1", "Device1", True)
        
        assert result is True
        assert coordinator.data["node1"]["devices"]["Device1"]["led_power"] is True

    async def test_async_set_device_led_color_success(self, coordinator):
        """Test setting LED color successfully."""
        coordinator.api.set_device_led_color.return_value = True
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"led_color": {"r": 0, "g": 0, "b": 0}}
                }
            }
        }
        
        result = await coordinator.async_set_device_led_color("node1", "Device1", 255, 128, 64)
        
        assert result is True
        assert coordinator.data["node1"]["devices"]["Device1"]["led_color"] == {
            "r": 255, "g": 128, "b": 64
        }
        coordinator.api.set_device_led_color.assert_called_once_with("node1", "Device1", 255, 128, 64)

    async def test_async_reset_refill_life_success(self, coordinator):
        """Test resetting refill life successfully."""
        coordinator.api.reset_refill_life.return_value = True
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"refill_life": 25}
                }
            }
        }
        
        result = await coordinator.async_reset_refill_life("node1", "Device1")
        
        assert result is True
        assert coordinator.data["node1"]["devices"]["Device1"]["refill_life"] == 100
        coordinator.api.reset_refill_life.assert_called_once_with("node1", "Device1")

    async def test_async_reset_refill_life_failure(self, coordinator):
        """Test resetting refill life with API failure."""
        coordinator.api.reset_refill_life.return_value = False
        coordinator.data = {
            "node1": {
                "devices": {
                    "Device1": {"refill_life": 25}
                }
            }
        }
        
        result = await coordinator.async_reset_refill_life("node1", "Device1")
        
        assert result is False
        assert coordinator.data["node1"]["devices"]["Device1"]["refill_life"] == 25  # Unchanged