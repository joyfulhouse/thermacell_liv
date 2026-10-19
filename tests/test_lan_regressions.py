"""Offline address, account lifecycle, and route-evidence regressions."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pythermacell.api import ThermacellAPI
from pythermacell.local import LocalEndpoint, LocalTransport
from zeroconf import ServiceStateChange

from custom_components.thermacell_liv.coordinator import ThermacellLivCoordinator
from custom_components.thermacell_liv.local import LocalDiscovery
from custom_components.thermacell_liv.sensor import ThermacellFeatureSensor
from homeassistant.helpers.update_coordinator import UpdateFailed


@pytest.fixture
def lan():
    coordinator = MagicMock()
    coordinator.client.api = ThermacellAPI(auth_handler=MagicMock(), session=MagicMock())
    coordinator.hass.async_create_task.side_effect = asyncio.create_task
    device = MagicMock()
    device.services.local_endpoint.side_effect = lambda host, port: LocalEndpoint("node", host, port, 2, "fake-pop")
    coordinator.get_device.side_effect = lambda node: device if node == "node" else None
    discovery = LocalDiscovery(coordinator)
    info = MagicMock(async_request=AsyncMock(return_value=True), port=8080)
    info.properties = {b"node_id": b"node"}
    info.parsed_scoped_addresses.return_value = ["192.0.2.1"]
    return coordinator, discovery, info, device


async def announce(discovery, info, name="service", state=ServiceStateChange.Added):
    with patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info):
        discovery._changed(MagicMock(), "service-type", name, state)
        await asyncio.sleep(0)


@pytest.mark.parametrize(
    "addresses,expected",
    [
        (["2001:db8::1", "192.0.2.1"], "192.0.2.1"),
        (["fe80::1%eth0", "2001:db8::1"], "2001:db8::1"),
        (["fe80::1", "fe80::1%eth0"], "fe80::1%eth0"),
    ],
)
async def test_address_policy(lan, addresses, expected):
    coordinator, discovery, info, _ = lan
    info.parsed_scoped_addresses.return_value = addresses
    await announce(discovery, info)
    assert coordinator.client.api.local_transports["node"].endpoint.host == expected
    assert coordinator.client.api.local_transports["node"].endpoint.security == 2


@pytest.mark.parametrize("addresses", [["::", "0.0.0.0"], ["bad", "ff02::1", "127.0.0.1", "fe80::1"]])
async def test_no_usable_address(lan, addresses):
    coordinator, discovery, info, _ = lan
    info.parsed_scoped_addresses.return_value = addresses
    await announce(discovery, info)
    assert not coordinator.client.api.local_transports


@pytest.mark.parametrize("fails", [False, True])
async def test_read_failover_and_cloud_fallback(lan, fails):
    coordinator, discovery, info, _ = lan
    info.parsed_scoped_addresses.return_value = ["192.0.2.1", "192.0.2.2"]
    await announce(discovery, info)
    visited = []
    snapshot = ({"node_id": "node"}, {"Hub": {}})

    async def read(transport):
        visited.append(transport.endpoint.host)
        if fails or transport.endpoint.host == "192.0.2.1":
            raise ConnectionError("offline")
        return snapshot

    api = coordinator.client.api
    with patch.object(LocalTransport, "read", read):
        result = await api.read_local("node")
        assert visited == ["192.0.2.1", "192.0.2.2"]
        assert result == (None if fails else snapshot)
        assert api.last_transport["node"] == ("cloud" if fails else "local")
        if not fails:
            visited.clear()
            assert await api.read_local("node") == snapshot
            assert visited == ["192.0.2.2"]


async def test_write_never_retries_another_address_or_cloud(lan):
    coordinator, discovery, info, _ = lan
    info.parsed_scoped_addresses.return_value = ["192.0.2.1", "192.0.2.2"]
    await announce(discovery, info)
    api = coordinator.client.api
    with (
        patch.object(LocalTransport, "read", AsyncMock(side_effect=[ConnectionError(), ({}, {})])),
        patch.object(LocalTransport, "write", autospec=True, side_effect=TimeoutError("uncertain")) as write,
        patch.object(api, "request", AsyncMock()) as cloud,
    ):
        await api.read_local("node")
        with pytest.raises(TimeoutError, match="uncertain"):
            await api.update_node_params("node", {"Hub": {"LED": True}})
        write.assert_awaited_once()
        assert write.call_args.args[0].endpoint.host == "192.0.2.2"
        cloud.assert_not_called()


async def test_failover_transport_initializes_library_state_and_entry_points(lan):
    coordinator, discovery, info, _ = lan
    info.parsed_scoped_addresses.return_value = ["192.0.2.1", "192.0.2.2"]
    await announce(discovery, info)
    api = coordinator.client.api
    transport = api.local_transports["node"]
    assert transport._session is api._session
    assert not transport._lock.locked()
    assert transport._base.host == transport.endpoint.host
    params = {"Hub": {"LED": True}}
    snapshot = ({"node_id": "node"}, params)
    with (
        patch.object(LocalTransport, "read", AsyncMock(return_value=snapshot)) as read,
        patch.object(LocalTransport, "write", AsyncMock()) as write,
        patch.object(api, "request", AsyncMock()) as cloud,
    ):
        assert await api.read_local("node") == snapshot
        assert await api.update_node_params("node", params) == (200, {})
        read.assert_awaited_once_with()
        write.assert_awaited_once_with(params)
        cloud.assert_not_awaited()


async def test_eager_cached_resolution_does_not_retain_completed_task(lan):
    coordinator, discovery, info, _ = lan
    coordinator.hass.async_create_task.side_effect = lambda coroutine: asyncio.Task(
        coroutine, loop=asyncio.get_running_loop(), eager_start=True
    )
    await announce(discovery, info)
    assert set(coordinator.client.api.local_transports) == {"node"}
    assert discovery._services["service"].info is info
    assert not discovery._tasks
    discovery.reconcile()
    info.async_request.assert_awaited_once()


async def test_address_update_and_node_remap(lan):
    coordinator, discovery, info, device = lan
    await announce(discovery, info)
    info.parsed_scoped_addresses.return_value = ["192.0.2.2"]
    await announce(discovery, info, state=ServiceStateChange.Updated)
    assert coordinator.client.api.local_transports["node"].endpoint.host == "192.0.2.2"
    info.properties = {b"node_id": b"other"}
    coordinator.get_device.side_effect = lambda node: device if node == "other" else None
    device.services.local_endpoint.side_effect = lambda host, port: LocalEndpoint("other", host, port, 2)
    await announce(discovery, info, state=ServiceStateChange.Updated)
    assert set(coordinator.client.api.local_transports) == {"other"}


@pytest.mark.parametrize("late", ["account", "capability", "timeout"])
async def test_late_announcement_after_refresh(lan, late):
    coordinator, discovery, info, device = lan
    if late == "account":
        coordinator.get_device.side_effect = lambda node: None
    elif late == "capability":
        device.services.local_endpoint.side_effect = lambda *args: None
    else:
        info.async_request.return_value = False
    await announce(discovery, info)
    assert not coordinator.client.api.local_transports
    coordinator.get_device.side_effect = lambda node: device if node == "node" else None
    device.services.local_endpoint.side_effect = lambda host, port: LocalEndpoint("node", host, port, 2)
    info.async_request.return_value = True
    with patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info):
        discovery.reconcile()
        await asyncio.sleep(0)
    assert set(coordinator.client.api.local_transports) == {"node"}


async def test_alias_removal_preserves_remaining_endpoint(lan):
    coordinator, discovery, info, _ = lan
    await announce(discovery, info, "first")
    info2 = MagicMock(async_request=AsyncMock(return_value=True), port=8080)
    info2.properties = {b"node_id": b"node"}
    info2.parsed_scoped_addresses.return_value = ["192.0.2.2"]
    await announce(discovery, info2, "second")
    discovery._changed(MagicMock(), "service-type", "first", ServiceStateChange.Removed)
    assert coordinator.client.api.local_transports["node"].endpoint.host == "192.0.2.2"
    discovery._changed(MagicMock(), "service-type", "second", ServiceStateChange.Removed)
    assert not coordinator.client.api.local_transports


async def test_account_removal_prunes_transport(lan):
    coordinator, discovery, info, _ = lan
    await announce(discovery, info)
    api = coordinator.client.api
    api.last_transport["node"] = "local"
    sensor = ThermacellFeatureSensor(coordinator, "node", "Hub", "transport")
    assert sensor.native_value == "local"
    coordinator.get_device.side_effect = lambda node: None
    discovery.reconcile()
    assert not api.local_transports
    assert "node" not in api.last_transport
    assert sensor.native_value is None
    assert sensor.extra_state_attributes["local_endpoint_configured"] is False


async def test_started_discovery_reconciles_after_real_coordinator_refresh(lan):
    mock_coordinator, _, info, device = lan
    device.node_id = "node"
    device.name = "Hub"
    device.is_online = True
    coordinator = ThermacellLivCoordinator(mock_coordinator.hass, mock_coordinator.client)
    coordinator.features.observe = MagicMock()
    coordinator.features.async_refresh = AsyncMock()
    coordinator._device_to_node_data = MagicMock(return_value={})
    coordinator.client.get_devices = AsyncMock(return_value=[device])
    discovery = LocalDiscovery(coordinator)
    browser = MagicMock(async_cancel=AsyncMock())
    with (
        patch("custom_components.thermacell_liv.local.async_get_async_instance", AsyncMock()),
        patch("custom_components.thermacell_liv.local.AsyncServiceBrowser", return_value=browser),
    ):
        await discovery.async_start()
    assert coordinator.local_discovery is discovery
    await announce(discovery, info)
    assert not coordinator.client.api.local_transports
    await coordinator._async_update_data()
    assert set(coordinator.client.api.local_transports) == {"node"}
    coordinator.client.get_devices.return_value = []
    with pytest.raises(UpdateFailed, match="No devices found"):
        await coordinator._async_update_data()
    assert not coordinator.client.api.local_transports
    await discovery.async_stop()
    assert coordinator.local_discovery is None
    browser.async_cancel.assert_awaited_once()


async def test_retry_and_retained_service_bounds(lan):
    _, discovery, info, _ = lan
    info.async_request.return_value = False
    with patch("custom_components.thermacell_liv.local.MAX_SERVICES", 2):
        await announce(discovery, info, "first")
        for _ in range(10):
            with patch("custom_components.thermacell_liv.local.AsyncServiceInfo", return_value=info):
                discovery.reconcile()
                await asyncio.sleep(0)
        assert info.async_request.await_count == 3
        await announce(discovery, info, "second")
        await announce(discovery, info, "third")
        assert set(discovery._services) == {"second", "third"}
        assert set(discovery._generations) == {"second", "third"}
    await discovery.async_stop()
    assert not discovery._services


async def test_stop_prevents_pending_resolution_and_refresh(lan):
    coordinator, discovery, info, _ = lan
    gate = asyncio.Event()

    async def wait(*args):
        await gate.wait()
        return True

    info.async_request.side_effect = wait
    await announce(discovery, info)
    pending = discovery._tasks["service"]
    await discovery.async_stop()
    assert pending.cancelled()
    assert not discovery._services
    gate.set()
    discovery.reconcile()
    await asyncio.sleep(0)
    assert not coordinator.client.api.local_transports
    assert not discovery._tasks


@pytest.mark.parametrize("route", [None, "cloud", "local"])
def test_transport_sensor_is_a_qualified_hint(lan, route):
    coordinator, _, _, _ = lan
    if route:
        coordinator.client.api.last_transport["node"] = route
    sensor = ThermacellFeatureSensor(coordinator, "node", "Hub", "transport")
    assert sensor.native_value == route
    assert sensor.extra_state_attributes == {
        "evidence": "library_route_hint",
        "proves_success": False,
        "per_refresh": False,
        "local_endpoint_configured": False,
    }


async def test_configured_endpoint_without_route_evidence_remains_unknown(lan):
    """Configuring an endpoint does not prove cloud or LAN success."""
    coordinator, discovery, info, _ = lan
    with patch.object(LocalTransport, "read", AsyncMock()) as read:
        await announce(discovery, info)
        sensor = ThermacellFeatureSensor(coordinator, "node", "Hub", "transport")
        assert sensor.native_value is None
        assert sensor.extra_state_attributes["local_endpoint_configured"] is True
        assert sensor.extra_state_attributes["proves_success"] is False
        read.assert_not_awaited()
