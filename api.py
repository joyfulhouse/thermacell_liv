"""Thermacell LIV API client based on ESP Rainmaker API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_API_BASE_URL

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
                        self.access_token = auth_data.get("accesstoken")
                        self.user_id = auth_data.get("user_id")
                        _LOGGER.debug("Authentication successful")
                        return True
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
        response = await self._make_request("GET", f"/user2/nodes?user_id={self.user_id}")
        if response:
            return response.get("node_details", [])
        return []

    async def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific node."""
        return await self._make_request("GET", f"/user2/nodes/status?nodeid={node_id}")

    async def set_node_params(self, node_id: str, params: Dict[str, Any]) -> bool:
        """Set node parameters."""
        data = {
            "node_id": node_id,
            "payload": params
        }
        response = await self._make_request("PUT", f"/user2/nodes/params", data)
        return response is not None

    async def set_device_power(self, node_id: str, device_name: str, power_on: bool) -> bool:
        """Turn device on or off."""
        params = {
            device_name: {
                "Power": power_on
            }
        }
        return await self.set_node_params(node_id, params)

    async def set_device_led_color(
        self, node_id: str, device_name: str, red: int, green: int, blue: int
    ) -> bool:
        """Set device LED color."""
        params = {
            device_name: {
                "LED": {
                    "R": red,
                    "G": green,
                    "B": blue
                }
            }
        }
        return await self.set_node_params(node_id, params)

    async def set_device_led_power(self, node_id: str, device_name: str, led_on: bool) -> bool:
        """Turn device LED on or off."""
        params = {
            device_name: {
                "LED": {
                    "Power": led_on
                }
            }
        }
        return await self.set_node_params(node_id, params)

    async def reset_refill_life(self, node_id: str, device_name: str) -> bool:
        """Reset the refill life counter."""
        params = {
            device_name: {
                "RefillReset": True
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