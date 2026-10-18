"""Discover RainMaker endpoints and pair them with authenticated hub metadata."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from ipaddress import ip_address
from typing import TYPE_CHECKING, Any

from pythermacell.local import SERVICE_TYPE, LocalEndpoint, LocalTransport
from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

from homeassistant.components.zeroconf import async_get_async_instance
from homeassistant.core import callback

if TYPE_CHECKING:
    from .coordinator import ThermacellLivCoordinator

MAX_SERVICES = 128
MAX_ADDRESSES = 8
MAX_RESOLVE_ATTEMPTS = 3


def _addresses(info: AsyncServiceInfo) -> list[str]:
    """Prefer IPv4, then non-link-local IPv6, then scoped link-local IPv6."""
    candidates = {}
    for address in info.parsed_scoped_addresses():
        try:
            parsed = ip_address(address)
        except ValueError:
            continue
        if parsed.is_unspecified or parsed.is_multicast or parsed.is_loopback:
            continue
        if parsed.version == 6 and parsed.is_link_local and "%" not in address:
            continue
        candidates[address] = (parsed.is_link_local, parsed.version != 4)
    return sorted(candidates, key=lambda address: candidates[address])[:MAX_ADDRESSES]


class ReadFailoverTransport(LocalTransport):
    """Keep library identity/security checks; only reads may try another address."""

    def __init__(self, transports: list[LocalTransport]) -> None:
        self._transports = transports
        self._selected = transports[0]
        self.endpoint = self._selected.endpoint

    async def read(self) -> tuple[dict[str, Any], dict[str, Any]]:
        ordered = [self._selected, *(item for item in self._transports if item is not self._selected)]
        for index, transport in enumerate(ordered):
            try:
                snapshot = await transport.read()
            except Exception:
                if index == len(ordered) - 1:
                    raise
            else:
                self._selected = transport
                self.endpoint = transport.endpoint
                return snapshot
        raise ConnectionError("No advertised local address is reachable")

    async def write(self, params: dict[str, Any]) -> None:
        await self._selected.write(params)


@dataclass
class _Service:
    zeroconf: Zeroconf
    service_type: str
    attempts: int = 0
    info: AsyncServiceInfo | None = None


class LocalDiscovery:
    """Use HA's shared zeroconf instance; never discover unrelated accounts."""

    def __init__(self, coordinator: ThermacellLivCoordinator) -> None:
        self.coordinator = coordinator
        self._browser: AsyncServiceBrowser | None = None
        self._generations: dict[str, int] = {}
        self._generation = 0
        self._services: dict[str, _Service] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._endpoints: dict[str, list[LocalEndpoint]] = {}
        self._closed = False

    async def async_start(self) -> None:
        """Start mDNS browsing without blocking setup."""
        zeroconf = await async_get_async_instance(self.coordinator.hass)
        self.coordinator.local_discovery = self
        self._browser = AsyncServiceBrowser(zeroconf.zeroconf, SERVICE_TYPE, handlers=[self._changed])

    @callback
    def _changed(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        if self._closed:
            return
        self._generation += 1
        generation = self._generation
        if state_change is ServiceStateChange.Removed:
            self._forget(name)
            self.reconcile()
            return
        if name not in self._services and len(self._services) >= MAX_SERVICES:
            self._forget(next(iter(self._services)))
        self._forget(name)
        self._generations[name] = generation
        self._services[name] = _Service(zeroconf, service_type)
        self._schedule(name)

    def _forget(self, name: str) -> None:
        self._services.pop(name, None)
        self._generations.pop(name, None)
        if task := self._tasks.pop(name, None):
            task.cancel()

    def _schedule(self, name: str) -> None:
        service = self._services[name]
        if name in self._tasks or service.attempts >= MAX_RESOLVE_ATTEMPTS:
            return
        service.attempts += 1
        self._tasks[name] = self.coordinator.hass.async_create_task(
            self._resolve(service.zeroconf, service.service_type, name, self._generations[name])
        )

    async def _resolve(self, zeroconf: Zeroconf, service_type: str, name: str, generation: int) -> None:
        info = AsyncServiceInfo(service_type, name)
        try:
            resolved = await info.async_request(zeroconf, 3000)
        finally:
            if self._generations.get(name) == generation:
                self._tasks.pop(name, None)
        if not resolved or self._closed or self._generations.get(name) != generation:
            return
        if name in self._services:
            self._services[name].info = info
        self._rebuild()

    @callback
    def reconcile(self) -> None:
        """Re-evaluate cached announcements after account/capability refresh."""
        if self._closed:
            return
        self._rebuild()
        for name, service in self._services.items():
            if service.info is None:
                self._schedule(name)

    def _rebuild(self) -> None:
        endpoints: dict[str, list[LocalEndpoint]] = {}
        for service in self._services.values():
            info = service.info
            if info is None or not info.port or not (raw_node := info.properties.get(b"node_id")):
                continue
            node_id = raw_node.decode(errors="replace")
            device = self.coordinator.get_device(node_id)
            if device is None:
                continue
            for address in _addresses(info):
                endpoint = device.services.local_endpoint(address, info.port)
                if endpoint:
                    candidates = endpoints.setdefault(node_id, [])
                    if endpoint not in candidates and len(candidates) < MAX_ADDRESSES:
                        candidates.append(endpoint)
        api = self.coordinator.client.api
        for node_id in set(api.local_transports) - endpoints.keys():
            api.local_transports.pop(node_id, None)
        for node_id, candidates in endpoints.items():
            if candidates == self._endpoints.get(node_id) and node_id in api.local_transports:
                continue
            transports = []
            for endpoint in candidates:
                api.configure_local(endpoint)
                if len(candidates) > 1:
                    transports.append(api.local_transports[node_id])
            if len(transports) > 1:
                api.local_transports[node_id] = ReadFailoverTransport(transports)
        self._endpoints = endpoints

    async def async_stop(self) -> None:
        """Stop discovery and clear ephemeral transport credentials."""
        self._closed = True
        self.coordinator.local_discovery = None
        if self._browser:
            await self._browser.async_cancel()
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._services.clear()
        self._generations.clear()
        self._endpoints.clear()
        self.coordinator.client.api.local_transports.clear()
