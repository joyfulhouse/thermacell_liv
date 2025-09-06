"""Tests for Thermacell LIV API client."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import pytest

from homeassistant.core import HomeAssistant
from custom_components.thermacell_liv.api import ThermacellLivAPI


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_session():
    """Return a mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def api_client(hass, mock_session):
    """Return an API client with mocked session."""
    with patch('custom_components.thermacell_liv.api.async_get_clientsession', return_value=mock_session):
        client = ThermacellLivAPI(hass, "test_user", "test_pass", "https://api.test.com")
        return client


class TestThermacellLivAPI:
    """Test the ThermacellLivAPI class."""

    async def test_init(self, hass, mock_session):
        """Test API client initialization."""
        with patch('custom_components.thermacell_liv.api.async_get_clientsession', return_value=mock_session):
            api = ThermacellLivAPI(hass, "test_user", "test_pass", "https://api.test.com/")
            
            assert api.username == "test_user"
            assert api.password == "test_pass"
            assert api.base_url == "https://api.test.com"
            assert api.access_token is None
            assert api.user_id is None

    async def test_authenticate_success(self, api_client):
        """Test successful authentication."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "accesstoken": "test_token",
            "user_id": "test_user_id"
        }
        
        api_client.session.post.return_value.__aenter__.return_value = mock_response
        
        result = await api_client.authenticate()
        
        assert result is True
        assert api_client.access_token == "test_token"
        assert api_client.user_id == "test_user_id"
        
        api_client.session.post.assert_called_once()
        call_args = api_client.session.post.call_args
        assert call_args[0][0] == "https://api.test.com/v1/login"
        assert call_args[1]["json"] == {
            "user_name": "test_user",
            "password": "test_pass"
        }

    async def test_authenticate_failure(self, api_client):
        """Test failed authentication."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Unauthorized"
        
        api_client.session.post.return_value.__aenter__.return_value = mock_response
        
        result = await api_client.authenticate()
        
        assert result is False
        assert api_client.access_token is None
        assert api_client.user_id is None

    async def test_authenticate_exception(self, api_client):
        """Test authentication with network exception."""
        api_client.session.post.side_effect = aiohttp.ClientError("Network error")
        
        result = await api_client.authenticate()
        
        assert result is False
        assert api_client.access_token is None

    async def test_make_request_success(self, api_client):
        """Test successful API request."""
        # Set up authenticated state
        api_client.access_token = "test_token"
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json.return_value = {"status": "success"}
        
        api_client.session.request.return_value.__aenter__.return_value = mock_response
        
        result = await api_client._make_request("GET", "/test")
        
        assert result == {"status": "success"}
        api_client.session.request.assert_called_once_with(
            "GET",
            "https://api.test.com/v1/test",
            json=None,
            headers={"Authorization": "test_token"},
            timeout=api_client.session.request.call_args[1]["timeout"]
        )

    async def test_make_request_unauthenticated(self, api_client):
        """Test API request without authentication."""
        # Mock authenticate to succeed
        with patch.object(api_client, 'authenticate', return_value=True) as mock_auth:
            api_client.access_token = None
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json.return_value = {"status": "success"}
            
            api_client.session.request.return_value.__aenter__.return_value = mock_response
            
            result = await api_client._make_request("GET", "/test")
            
            mock_auth.assert_called_once()
            assert result == {"status": "success"}

    async def test_make_request_token_expired(self, api_client):
        """Test API request with expired token."""
        api_client.access_token = "expired_token"
        
        # First request returns 401, second succeeds
        responses = [
            AsyncMock(status=401),
            AsyncMock(status=200, content_type="application/json")
        ]
        responses[1].json.return_value = {"status": "success"}
        
        api_client.session.request.return_value.__aenter__.side_effect = responses
        
        with patch.object(api_client, 'authenticate', return_value=True) as mock_auth:
            api_client.access_token = "new_token"  # Set after re-auth
            
            result = await api_client._make_request("GET", "/test")
            
            mock_auth.assert_called_once()
            assert result == {"status": "success"}
            assert api_client.session.request.call_count == 2

    async def test_make_request_timeout_retry(self, api_client):
        """Test API request with timeout and retry."""
        api_client.access_token = "test_token"
        
        # First two requests timeout, third succeeds
        side_effects = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            AsyncMock(status=200, content_type="application/json")
        ]
        side_effects[2].__aenter__.return_value.json.return_value = {"status": "success"}
        
        api_client.session.request.side_effect = side_effects
        
        result = await api_client._make_request("GET", "/test")
        
        assert result == {"status": "success"}
        assert api_client.session.request.call_count == 3

    async def test_make_request_max_retries(self, api_client):
        """Test API request exceeding max retries."""
        api_client.access_token = "test_token"
        
        api_client.session.request.side_effect = asyncio.TimeoutError()
        
        result = await api_client._make_request("GET", "/test")
        
        assert result is None
        assert api_client.session.request.call_count == 3  # RETRY_ATTEMPTS

    async def test_get_user_nodes_success(self, api_client):
        """Test getting user nodes successfully."""
        expected_nodes = [
            {"node_id": "node1", "name": "Device 1"},
            {"node_id": "node2", "name": "Device 2"}
        ]
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {"node_details": expected_nodes}
            api_client.user_id = "test_user_id"
            
            result = await api_client.get_user_nodes()
            
            mock_request.assert_called_once_with("GET", "/user/nodes?user_id=test_user_id")
            assert result == expected_nodes

    async def test_get_user_nodes_failure(self, api_client):
        """Test getting user nodes with API failure."""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = None
            api_client.user_id = "test_user_id"
            
            result = await api_client.get_user_nodes()
            
            assert result == []

    async def test_get_node_status(self, api_client):
        """Test getting node status."""
        expected_status = {"online": True, "connected": True}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = expected_status
            
            result = await api_client.get_node_status("node123")
            
            mock_request.assert_called_once_with("GET", "/user/nodes/status?nodeid=node123")
            assert result == expected_status

    async def test_set_node_params(self, api_client):
        """Test setting node parameters."""
        params = {"Device1": {"Power": True}}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {"status": "success"}
            
            result = await api_client.set_node_params("node123", params)
            
            mock_request.assert_called_once_with(
                "PUT",
                "/user/nodes/params",
                {"node_id": "node123", "payload": params}
            )
            assert result is True

    async def test_set_node_params_failure(self, api_client):
        """Test setting node parameters with failure."""
        params = {"Device1": {"Power": True}}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = await api_client.set_node_params("node123", params)
            
            assert result is False

    async def test_set_device_power(self, api_client):
        """Test setting device power."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_power("node123", "Device1", True)
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"Device1": {"Power": True}}
            )
            assert result is True

    async def test_set_device_led_color(self, api_client):
        """Test setting device LED color."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_led_color("node123", "Device1", 255, 128, 0)
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"Device1": {"LED": {"R": 255, "G": 128, "B": 0}}}
            )
            assert result is True

    async def test_set_device_led_power(self, api_client):
        """Test setting device LED power."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_led_power("node123", "Device1", False)
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"Device1": {"LED": {"Power": False}}}
            )
            assert result is True

    async def test_reset_refill_life(self, api_client):
        """Test resetting refill life."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.reset_refill_life("node123", "Device1")
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"Device1": {"RefillReset": True}}
            )
            assert result is True

    async def test_test_connection_success(self, api_client):
        """Test successful connection test."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.return_value = [{"node_id": "node1"}]
            
            result = await api_client.test_connection()
            
            assert result is True

    async def test_test_connection_failure(self, api_client):
        """Test failed connection test."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.side_effect = Exception("Network error")
            
            result = await api_client.test_connection()
            
            assert result is False

    async def test_test_connection_invalid_response(self, api_client):
        """Test connection test with invalid response."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.return_value = "not a list"
            
            result = await api_client.test_connection()
            
            assert result is False