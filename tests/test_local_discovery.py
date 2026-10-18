"""Discovery lifecycle, account scoping, and removal races."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from zeroconf import ServiceStateChange

from custom_components.thermacell_liv.local import LocalDiscovery


async def test_discovery_pairs_only_account_nodes_and_stops():
    coordinator = MagicMock()
    coordinator.client.api.local_transports = {}
    coordinator.hass.async_create_task.side_effect = asyncio.create_task
    discovery = LocalDiscovery(coordinator)
    info = MagicMock()
    info.async_request = AsyncMock(return_value=True)
    info.properties = {b"node_id": b"account-node"}
    info.parsed_scoped_addresses.return_value = ["192.0.2.1"]
    info.port = 8080
    browser = MagicMock(async_cancel=AsyncMock())
    with (
        patch("custom_components.thermacell_liv.local.async_get_async_instance", AsyncMock()) as get_zc,
        patch("custom_components.thermacell_liv.local.AsyncServiceBrowser", return_value=browser),
        patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info),
    ):
        await discovery.async_start()
        get_zc.assert_awaited_once()
        discovery._changed(MagicMock(), "service", "name", ServiceStateChange.Added)
        await asyncio.sleep(0)
        coordinator.get_device.assert_called_with("account-node")
        coordinator.client.api.configure_local.assert_called_once()
        coordinator.get_device.return_value.services.local_endpoint.assert_called_once_with("192.0.2.1", 8080)
        coordinator.client.api.local_transports["account-node"] = MagicMock()
        discovery._changed(MagicMock(), "service", "name", ServiceStateChange.Removed)
        assert not coordinator.client.api.local_transports
        coordinator.client.api.configure_local.reset_mock()
        coordinator.get_device.return_value = None
        discovery._changed(MagicMock(), "service", "another", ServiceStateChange.Added)
        await asyncio.sleep(0)
        coordinator.client.api.configure_local.assert_not_called()
        await discovery.async_stop()
        browser.async_cancel.assert_awaited_once()
        discovery._changed(MagicMock(), "service", "late", ServiceStateChange.Added)
        assert "late" not in discovery._generations


async def test_removed_service_cannot_be_resurrected_by_pending_resolution():
    coordinator = MagicMock()
    coordinator.client.api.local_transports = {}
    coordinator.hass.async_create_task.side_effect = asyncio.create_task
    discovery = LocalDiscovery(coordinator)
    gate = asyncio.Event()
    info = MagicMock()
    info.async_request = AsyncMock(side_effect=lambda *args: None)

    async def resolve(*args):
        await gate.wait()
        return True

    info.async_request.side_effect = resolve
    with patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info):
        discovery._changed(MagicMock(), "service", "name", ServiceStateChange.Added)
        await asyncio.sleep(0)
        discovery._changed(MagicMock(), "service", "name", ServiceStateChange.Removed)
        gate.set()
        await asyncio.sleep(0)
        coordinator.client.api.configure_local.assert_not_called()
        await discovery.async_stop()


async def test_incomplete_discovery_has_no_control_effect():
    coordinator = MagicMock()
    discovery = LocalDiscovery(coordinator)
    discovery._generations["name"] = 1
    info = MagicMock(async_request=AsyncMock(return_value=False))
    with patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info):
        await discovery._resolve(MagicMock(), "service", "name", 1)
        info.async_request.return_value = True
        info.properties = {}
        await discovery._resolve(MagicMock(), "service", "name", 1)
        info.properties = {b"node_id": b"node"}
        info.parsed_scoped_addresses.return_value = []
        await discovery._resolve(MagicMock(), "service", "name", 1)
        info.parsed_scoped_addresses.return_value = ["192.0.2.1"]
        info.port = 8080
        coordinator.get_device.return_value.services.local_endpoint.return_value = None
        await discovery._resolve(MagicMock(), "service", "name", 1)
        coordinator.client.api.configure_local.assert_not_called()
