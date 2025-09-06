"""Thermacell LIV API client based on ESP Rainmaker API."""
from __future__ import annotations

import asyncio
import base64
import colorsys
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from .const import DEFAULT_API_BASE_URL
except ImportError:
    from const import DEFAULT_API_BASE_URL

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = 30
RETRY_ATTEMPTS = 3


class ThermacellLivAPI:
    """API client for Thermacell LIV devices using ESP Rainmaker API v1."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        base_url: str = DEFAULT_API_BASE_URL,
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.session: ClientSession = async_get_clientsession(hass)
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self._auth_lock = asyncio.Lock()

    async def authenticate(self) -> bool:
        """Authenticate with the ESP Rainmaker API."""
        async with self._auth_lock:
            try:
                # ESP Rainmaker login2 endpoint
                url = f"{self.base_url}/v1/login2"
                data = {
                    "user_name": self.username,
                    "password": self.password,
                }

                timeout = ClientTimeout(total=API_TIMEOUT)
                async with self.session.post(url, json=data, timeout=timeout) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        
                        # Extract access token
                        self.access_token = auth_data.get("accesstoken")
                        
                        # Extract user ID from ID token
                        id_token = auth_data.get("idtoken")
                        if id_token:
                            id_payload = self._decode_jwt_payload(id_token)
                            if id_payload:
                                self.user_id = id_payload.get("custom:user_id")
                        
                        _LOGGER.debug("Authentication successful")
                        return self.access_token is not None and self.user_id is not None
                    else:
                        _LOGGER.error(
                            "Authentication failed with status %s: %s",
                            response.status,
                            await response.text(),
                        )
                        return False

            except Exception as err:
                _LOGGER.error("Authentication error: %s", err)
                return False

    def _decode_jwt_payload(self, jwt_token: str) -> Dict[str, Any]:
        """Decode JWT token payload without verification."""
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return {}
            
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded_bytes = base64.urlsafe_b64decode(payload)
            return json.loads(decoded_bytes.decode('utf-8'))
        except Exception as e:
            _LOGGER.debug("Failed to decode JWT payload: %s", e)
            return {}

    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make an authenticated API request."""
        if not self.access_token:
            if not await self.authenticate():
                return None

        headers = {"Authorization": self.access_token}
        url = f"{self.base_url}/v1{endpoint}"

        for attempt in range(RETRY_ATTEMPTS):
            try:
                timeout = ClientTimeout(total=API_TIMEOUT)
                async with self.session.request(
                    method, url, json=data, headers=headers, timeout=timeout
                ) as response:
                    if response.status == 401:
                        # Token expired, try re-authentication
                        if await self.authenticate():
                            headers = {"Authorization": self.access_token}
                            continue
                        else:
                            return None

                    if response.status in (200, 201, 204):
                        if response.content_type == "application/json":
                            return await response.json()
                        return {}

                    _LOGGER.error(
                        "API request failed with status %s: %s",
                        response.status,
                        await response.text(),
                    )
                    return None

            except asyncio.TimeoutError:
                _LOGGER.warning("API request timeout (attempt %s/%s)", attempt + 1, RETRY_ATTEMPTS)
                if attempt == RETRY_ATTEMPTS - 1:
                    return None
            except Exception as err:
                _LOGGER.error("API request error: %s", err)
                return None

        return None

    async def get_user_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes (devices) for the authenticated user."""
        response = await self._make_request("GET", "/user/nodes")
        if response:
            # The response contains a list of node IDs, we need to get details for each
            node_ids = response.get("nodes", [])
            nodes = []
            for node_id in node_ids:
                # Get node parameters which contain the device details
                params_response = await self._make_request("GET", f"/user/nodes/params?nodeid={node_id}")
                if params_response:
                    # Extract device information from the LIV Hub parameters
                    liv_hub_params = params_response.get("LIV Hub", {})
                    node_data = {
                        "id": node_id,
                        "node_name": liv_hub_params.get("Name", f"Node {node_id}"),
                        "type": "LIV Hub",
                        "params": params_response
                    }
                    nodes.append(node_data)
            return nodes
        return []

    async def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific node."""
        return await self._make_request("GET", f"/user/nodes/status?nodeid={node_id}")

    async def set_node_params(self, node_id: str, params: Dict[str, Any]) -> bool:
        """Set node parameters."""
        # The correct API structure uses query parameter and direct payload
        response = await self._make_request("PUT", f"/user/nodes/params?nodeid={node_id}", params)
        return response is not None

    async def set_device_power(self, node_id: str, device_name: str, power_on: bool) -> bool:
        """Turn device on or off."""
        # Based on API validation, the device is "LIV Hub" and uses "Enable Repellers"
        params = {
            "LIV Hub": {
                "Enable Repellers": power_on
            }
        }
        return await self.set_node_params(node_id, params)

    async def set_device_led_color(
        self, node_id: str, device_name: str, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color."""
        # Convert RGB to HSV hue (0-360 range)
        r_norm, g_norm, b_norm = red / 255.0, green / 255.0, blue / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        hue = int(h * 360)
        brightness = int(v * 100)
        
        params = {
            "LIV Hub": {
                "LED Hue": hue,
                "LED Brightness": brightness
            }
        }
        return await self.set_node_params(node_id, params)

    async def set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Turn device LED on or off."""
        # Set brightness to 0 to turn off, or restore to default brightness
        brightness = 100 if led_on else 0
        params = {
            "LIV Hub": {
                "LED Brightness": brightness
            }
        }
        return await self.set_node_params(node_id, params)

    async def reset_refill_life(self, node_id: str, device_name: str) -> bool:
        """Reset the refill life counter."""
        params = {
            "LIV Hub": {
                "Refill Reset": 1  # Based on API, this is a counter, not boolean
            }
        }
        return await self.set_node_params(node_id, params)

    async def test_connection(self) -> bool:
        """Test if the API connection is working."""
        try:
            nodes = await self.get_user_nodes()
            return isinstance(nodes, list)
        except Exception:
            return False