"""Tests for Thermacell LIV API client."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import pytest

from homeassistant.core import HomeAssistant
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from api import ThermacellLivAPI


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
    with patch('api.async_get_clientsession', return_value=mock_session):
        client = ThermacellLivAPI(hass, "test_user", "test_pass", "https://api.test.com")
        return client


class TestThermacellLivAPI:
    """Test the ThermacellLivAPI class."""

    @pytest.mark.asyncio
    async def test_init(self, hass, mock_session):
        """Test API client initialization."""
        with patch('api.async_get_clientsession', return_value=mock_session):
            api = ThermacellLivAPI(hass, "test_user", "test_pass", "https://api.test.com/")
            
            assert api.username == "test_user"
            assert api.password == "test_pass"
            assert api.base_url == "https://api.test.com"
            assert api.access_token is None
            assert api.user_id is None

    @pytest.mark.asyncio
    async def test_authenticate_success(self, api_client):
        """Test successful authentication."""
        # Create a mock JWT token with user_id in payload
        import base64
        import json
        
        payload = {"custom:user_id": "test_user_id"}
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        mock_id_token = f"header.{encoded_payload}.signature"
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "accesstoken": "test_token",
            "idtoken": mock_id_token
        }
        
        api_client.session.post.return_value.__aenter__.return_value = mock_response
        
        result = await api_client.authenticate()
        
        assert result is True
        assert api_client.access_token == "test_token"
        assert api_client.user_id == "test_user_id"
        
        api_client.session.post.assert_called_once()
        call_args = api_client.session.post.call_args
        assert call_args[0][0] == "https://api.test.com/v1/login2"
        assert call_args[1]["json"] == {
            "user_name": "test_user",
            "password": "test_pass"
        }

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_authenticate_exception(self, api_client):
        """Test authentication with network exception."""
        api_client.session.post.side_effect = aiohttp.ClientError("Network error")
        
        result = await api_client.authenticate()
        
        assert result is False
        assert api_client.access_token is None

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_make_request_timeout_retry(self, api_client):
        """Test API request with timeout and retry."""
        api_client.access_token = "test_token"
        
        # First two requests timeout, third succeeds
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json.return_value = {"status": "success"}
        
        side_effects = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            mock_response
        ]
        
        api_client.session.request.return_value.__aenter__.side_effect = side_effects
        
        result = await api_client._make_request("GET", "/test")
        
        assert result == {"status": "success"}
        assert api_client.session.request.call_count == 3

    @pytest.mark.asyncio
    async def test_make_request_max_retries(self, api_client):
        """Test API request exceeding max retries."""
        api_client.access_token = "test_token"
        
        api_client.session.request.side_effect = asyncio.TimeoutError()
        
        result = await api_client._make_request("GET", "/test")
        
        assert result is None
        assert api_client.session.request.call_count == 3  # RETRY_ATTEMPTS

    @pytest.mark.asyncio
    async def test_get_user_nodes_success(self, api_client):
        """Test getting user nodes successfully."""
        # Mock the two-step process: first get node list, then get params for each
        nodes_response = {"nodes": ["node1", "node2"]}
        node1_params = {"LIV Hub": {"Name": "Device 1"}}
        node2_params = {"LIV Hub": {"Name": "Device 2"}}
        
        with patch.object(api_client, '_make_request') as mock_request:
            # Return different responses for different calls
            mock_request.side_effect = [
                nodes_response,  # First call: get nodes list
                node1_params,    # Second call: get node1 params
                node2_params     # Third call: get node2 params
            ]
            api_client.user_id = "test_user_id"
            
            result = await api_client.get_user_nodes()
            
            # Should make 3 calls: one for nodes list, two for params
            assert mock_request.call_count == 3
            mock_request.assert_any_call("GET", "/user/nodes")
            mock_request.assert_any_call("GET", "/user/nodes/params?nodeid=node1")
            mock_request.assert_any_call("GET", "/user/nodes/params?nodeid=node2")
            
            # Check result structure
            assert len(result) == 2
            assert result[0]["id"] == "node1"
            assert result[0]["node_name"] == "Device 1"
            assert result[0]["type"] == "LIV Hub"
            assert result[1]["id"] == "node2"
            assert result[1]["node_name"] == "Device 2"

    @pytest.mark.asyncio
    async def test_get_user_nodes_failure(self, api_client):
        """Test getting user nodes with API failure."""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = None
            api_client.user_id = "test_user_id"
            
            result = await api_client.get_user_nodes()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_node_status(self, api_client):
        """Test getting node status."""
        expected_status = {"online": True, "connected": True}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = expected_status
            
            result = await api_client.get_node_status("node123")
            
            mock_request.assert_called_once_with("GET", "/user/nodes/status?nodeid=node123")
            assert result == expected_status

    @pytest.mark.asyncio
    async def test_set_node_params(self, api_client):
        """Test setting node parameters."""
        params = {"LIV Hub": {"Enable Repellers": True}}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {"status": "success"}
            
            result = await api_client.set_node_params("node123", params)
            
            mock_request.assert_called_once_with(
                "PUT",
                "/user/nodes/params?nodeid=node123",
                params
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_set_node_params_failure(self, api_client):
        """Test setting node parameters with failure."""
        params = {"LIV Hub": {"Enable Repellers": True}}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = await api_client.set_node_params("node123", params)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_set_device_power(self, api_client):
        """Test setting device power."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_power("node123", "LIV Hub", True)
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"LIV Hub": {"Enable Repellers": True}}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_set_device_led_color(self, api_client):
        """Test setting device LED color."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_led_color("node123", "LIV Hub", 255, 128, 0)
            
            # The API converts RGB to HSV, so we expect LED Hue and LED Brightness
            mock_set_params.assert_called_once_with(
                "node123",
                {"LIV Hub": {"LED Hue": 30, "LED Brightness": 100}}  # Orange color
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_set_device_led_power(self, api_client):
        """Test setting device LED power."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.set_device_led_power("node123", "LIV Hub", False)
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"LIV Hub": {"LED Brightness": 0}}  # LED off = brightness 0
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_reset_refill_life(self, api_client):
        """Test resetting refill life."""
        with patch.object(api_client, 'set_node_params') as mock_set_params:
            mock_set_params.return_value = True
            
            result = await api_client.reset_refill_life("node123", "LIV Hub")
            
            mock_set_params.assert_called_once_with(
                "node123",
                {"LIV Hub": {"Refill Reset": 1}}  # Counter, not boolean
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_success(self, api_client):
        """Test successful connection test."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.return_value = [{"node_id": "node1"}]
            
            result = await api_client.test_connection()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, api_client):
        """Test failed connection test."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.side_effect = Exception("Network error")
            
            result = await api_client.test_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_invalid_response(self, api_client):
        """Test connection test with invalid response."""
        with patch.object(api_client, 'get_user_nodes') as mock_get_nodes:
            mock_get_nodes.return_value = "not a list"
            
            result = await api_client.test_connection()
            
            assert result is False