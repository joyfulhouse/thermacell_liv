"""Discover RainMaker endpoints and pair them with authenticated hub metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pythermacell.local import SERVICE_TYPE
from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

from homeassistant.components.zeroconf import async_get_async_instance
from homeassistant.core import callback

if TYPE_CHECKING:
    from .coordinator import ThermacellLivCoordinator


class LocalDiscovery:
    """Use HA's shared zeroconf instance; never discover unrelated accounts."""

    def __init__(self, coordinator: ThermacellLivCoordinator) -> None:
        self.coordinator = coordinator
        self._browser: AsyncServiceBrowser | None = None
        self._names: dict[str, str] = {}
        self._generations: dict[str, int] = {}
        self._closed = False

    async def async_start(self) -> None:
        """Start mDNS browsing without blocking setup."""
        zeroconf = await async_get_async_instance(self.coordinator.hass)
        self._browser = AsyncServiceBrowser(zeroconf.zeroconf, SERVICE_TYPE, handlers=[self._changed])

    @callback
    def _changed(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        if self._closed:
            return
        generation = self._generations[name] = self._generations.get(name, 0) + 1
        if state_change is ServiceStateChange.Removed:
            node_id = self._names.pop(name, None)
            if node_id:
                self.coordinator.client.api.local_transports.pop(node_id, None)
            return
        self.coordinator.hass.async_create_task(self._resolve(zeroconf, service_type, name, generation))

    async def _resolve(self, zeroconf: Zeroconf, service_type: str, name: str, generation: int) -> None:
        info = AsyncServiceInfo(service_type, name)
        if not await info.async_request(zeroconf, 3000) or self._closed or self._generations.get(name) != generation:
            return
        raw_node = info.properties.get(b"node_id")
        if not raw_node:
            return
        node_id = raw_node.decode(errors="replace")
        device = self.coordinator.get_device(node_id)
        addresses = info.parsed_scoped_addresses()
        if device is None or not addresses or not info.port:
            return
        endpoint = device.services.local_endpoint(addresses[0], info.port)
        if endpoint:
            self.coordinator.client.api.configure_local(endpoint)
            self._names[name] = node_id

    async def async_stop(self) -> None:
        """Stop discovery and clear ephemeral transport credentials."""
        self._closed = True
        if self._browser:
            await self._browser.async_cancel()
        self.coordinator.client.api.local_transports.clear()
