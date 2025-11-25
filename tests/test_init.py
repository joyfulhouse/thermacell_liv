#!/usr/bin/env python3
"""Unit tests for __init__ module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pythermacell import AuthenticationError, ThermacellClient

import custom_components.thermacell_liv as init_module
from custom_components.thermacell_liv.const import DOMAIN


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(self):
        """Test successful setup."""
        hass = MagicMock()
        entry = MagicMock()
        entry.data = {"username": "test@example.com", "password": "password123"}
        entry.options.get.return_value = 60
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        with (
            patch("custom_components.thermacell_liv.async_get_clientsession") as mock_session,
            patch("custom_components.thermacell_liv.ThermacellClient") as mock_client_class,
            patch("custom_components.thermacell_liv.ThermacellLivCoordinator") as mock_coordinator_class,
        ):
            # Setup mocks
            mock_client = AsyncMock(spec=ThermacellClient)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.data = {"node1": {}}
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_add_listener = MagicMock(return_value=MagicMock())
            mock_coordinator_class.return_value = mock_coordinator

            hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

            # Run setup
            result = await init_module.async_setup_entry(hass, entry)

            # Verify
            assert result is True
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            assert entry.runtime_data == {"coordinator": mock_coordinator, "client": mock_client}
            hass.config_entries.async_forward_entry_setups.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_entry_auth_failure(self):
        """Test setup with authentication failure."""
        from homeassistant.exceptions import ConfigEntryAuthFailed

        hass = MagicMock()
        entry = MagicMock()
        entry.data = {"username": "test@example.com", "password": "wrongpass"}

        with (
            patch("custom_components.thermacell_liv.async_get_clientsession") as mock_session,
            patch("custom_components.thermacell_liv.ThermacellClient") as mock_client_class,
        ):
            mock_client = AsyncMock(spec=ThermacellClient)
            mock_client.__aenter__ = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))
            mock_client_class.return_value = mock_client

            with pytest.raises(ConfigEntryAuthFailed):
                await init_module.async_setup_entry(hass, entry)

    @pytest.mark.asyncio
    async def test_async_setup_entry_with_custom_scan_interval(self):
        """Test setup with custom scan interval."""
        hass = MagicMock()
        entry = MagicMock()
        entry.data = {"username": "test@example.com", "password": "password123"}
        entry.options.get.return_value = 120  # Custom interval
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        with (
            patch("custom_components.thermacell_liv.async_get_clientsession") as mock_session,
            patch("custom_components.thermacell_liv.ThermacellClient") as mock_client_class,
            patch("custom_components.thermacell_liv.ThermacellLivCoordinator") as mock_coordinator_class,
        ):
            mock_client = AsyncMock(spec=ThermacellClient)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.data = {}
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_add_listener = MagicMock(return_value=MagicMock())
            mock_coordinator_class.return_value = mock_coordinator

            hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

            result = await init_module.async_setup_entry(hass, entry)

            # Verify custom scan interval was used
            mock_coordinator_class.assert_called_once_with(hass, mock_client, scan_interval=120)
            assert result is True

    @pytest.mark.asyncio
    async def test_async_setup_entry_registers_listeners(self):
        """Test that setup registers update and cleanup listeners."""
        hass = MagicMock()
        entry = MagicMock()
        entry.data = {"username": "test@example.com", "password": "password123"}
        entry.options.get.return_value = 60
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        with (
            patch("custom_components.thermacell_liv.async_get_clientsession") as mock_session,
            patch("custom_components.thermacell_liv.ThermacellClient") as mock_client_class,
            patch("custom_components.thermacell_liv.ThermacellLivCoordinator") as mock_coordinator_class,
        ):
            mock_client = AsyncMock(spec=ThermacellClient)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.data = {}
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_add_listener = MagicMock(return_value=MagicMock())
            mock_coordinator_class.return_value = mock_coordinator

            hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

            await init_module.async_setup_entry(hass, entry)

            # Verify listeners were registered
            assert entry.async_on_unload.call_count == 2  # Update listener + cleanup listener
            mock_coordinator.async_add_listener.assert_called_once()


class TestAsyncCleanupStaleDevices:
    """Test _async_cleanup_stale_devices function."""

    def test_async_cleanup_stale_devices_removes_old_devices(self):
        """Test that stale devices are removed."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        # Mock coordinator with current nodes
        coordinator = MagicMock()
        coordinator.data = {"node1": {}, "node2": {}}  # Only node1 and node2 exist
        entry.runtime_data = {"coordinator": coordinator}

        # Mock device registry
        device_registry = MagicMock()

        # Create mock devices - node3 is stale
        device1 = MagicMock()
        device1.identifiers = {(DOMAIN, "node1")}
        device1.name = "Device 1"

        device2 = MagicMock()
        device2.identifiers = {(DOMAIN, "node2")}
        device2.name = "Device 2"

        device3 = MagicMock()  # Stale device
        device3.identifiers = {(DOMAIN, "node3")}
        device3.name = "Device 3"
        device3.id = "device3_id"

        with (
            patch("custom_components.thermacell_liv.dr.async_get", return_value=device_registry),
            patch(
                "custom_components.thermacell_liv.dr.async_entries_for_config_entry",
                return_value=[device1, device2, device3],
            ),
        ):
            init_module._async_cleanup_stale_devices(hass, entry)

            # Verify device3 was removed
            device_registry.async_remove_device.assert_called_once_with("device3_id")

    def test_async_cleanup_stale_devices_no_stale_devices(self):
        """Test when there are no stale devices."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        coordinator = MagicMock()
        coordinator.data = {"node1": {}, "node2": {}}
        entry.runtime_data = {"coordinator": coordinator}

        device_registry = MagicMock()

        device1 = MagicMock()
        device1.identifiers = {(DOMAIN, "node1")}

        device2 = MagicMock()
        device2.identifiers = {(DOMAIN, "node2")}

        with (
            patch("custom_components.thermacell_liv.dr.async_get", return_value=device_registry),
            patch(
                "custom_components.thermacell_liv.dr.async_entries_for_config_entry", return_value=[device1, device2]
            ),
        ):
            init_module._async_cleanup_stale_devices(hass, entry)

            # Verify no devices were removed
            device_registry.async_remove_device.assert_not_called()

    def test_async_cleanup_stale_devices_empty_data(self):
        """Test cleanup when coordinator has no data."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        coordinator = MagicMock()
        coordinator.data = None
        entry.runtime_data = {"coordinator": coordinator}

        device_registry = MagicMock()

        device1 = MagicMock()
        device1.identifiers = {(DOMAIN, "node1")}
        device1.id = "device1_id"

        with (
            patch("custom_components.thermacell_liv.dr.async_get", return_value=device_registry),
            patch("custom_components.thermacell_liv.dr.async_entries_for_config_entry", return_value=[device1]),
        ):
            init_module._async_cleanup_stale_devices(hass, entry)

            # All devices should be removed if coordinator has no data
            device_registry.async_remove_device.assert_called_once_with("device1_id")


class TestAsyncReloadEntry:
    """Test async_reload_entry function."""

    @pytest.mark.asyncio
    async def test_async_reload_entry(self):
        """Test reloading config entry."""
        hass = MagicMock()
        hass.config_entries.async_reload = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "test_entry"

        await init_module.async_reload_entry(hass, entry)

        hass.config_entries.async_reload.assert_called_once_with("test_entry")


class TestAsyncUnloadEntry:
    """Test async_unload_entry function."""

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(self):
        """Test successful unload."""
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        mock_client = AsyncMock(spec=ThermacellClient)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        entry = MagicMock()
        entry.runtime_data = {"coordinator": MagicMock(), "client": mock_client}

        result = await init_module.async_unload_entry(hass, entry)

        assert result is True
        hass.config_entries.async_unload_platforms.assert_called_once()
        mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_unload_entry_failure(self):
        """Test failed unload."""
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        entry = MagicMock()
        entry.runtime_data = None

        result = await init_module.async_unload_entry(hass, entry)

        assert result is False


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio

    test_setup = TestAsyncSetupEntry()
    test_cleanup = TestAsyncCleanupStaleDevices()
    test_reload = TestAsyncReloadEntry()
    test_unload = TestAsyncUnloadEntry()

    print("🧪 Running Init Module Tests")
    print("=" * 50)

    async def run_async_tests():
        """Run all async tests."""
        try:
            await test_setup.test_async_setup_entry_success()
            print("✅ Setup entry success test passed")
        except Exception as e:
            print(f"❌ Setup entry success test failed: {e}")

        try:
            await test_setup.test_async_setup_entry_auth_failure()
            print("✅ Setup entry auth failure test passed")
        except Exception as e:
            print(f"❌ Setup entry auth failure test failed: {e}")

        try:
            await test_reload.test_async_reload_entry()
            print("✅ Reload entry test passed")
        except Exception as e:
            print(f"❌ Reload entry test failed: {e}")

        try:
            await test_unload.test_async_unload_entry_success()
            print("✅ Unload entry success test passed")
        except Exception as e:
            print(f"❌ Unload entry success test failed: {e}")

    asyncio.run(run_async_tests())

    # Sync tests
    try:
        test_cleanup.test_async_cleanup_stale_devices_removes_old_devices()
        print("✅ Cleanup stale devices test passed")
    except Exception as e:
        print(f"❌ Cleanup stale devices test failed: {e}")

    print("\n🎉 Init module tests completed!")
