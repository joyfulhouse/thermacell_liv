"""The Thermacell LIV integration."""

from __future__ import annotations

import logging

from pythermacell import AuthenticationError, ThermacellClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import ThermacellLivCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.LIGHT, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Thermacell LIV from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Get the shared aiohttp session
    session = async_get_clientsession(hass)

    # Initialize pythermacell client with shared session
    client = ThermacellClient(
        username=username,
        password=password,
        session=session,
    )

    # Enter the client context (handles authentication)
    try:
        await client.__aenter__()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Failed to authenticate with Thermacell API: {err}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to connect to Thermacell API: {err}") from err

    # Initialize coordinator with configurable scan interval
    scan_interval = entry.options.get("scan_interval", 60)
    coordinator = ThermacellLivCoordinator(hass, client, scan_interval=scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client in runtime_data (HA 2024.x+ best practice)
    entry.runtime_data = {"coordinator": coordinator, "client": client}

    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Setup stale device cleanup listener (Gold tier: stale-devices requirement)
    # This removes devices from HA when they're removed from Thermacell account
    @callback
    def cleanup_stale_devices() -> None:
        """Cleanup callback for stale devices."""
        _async_cleanup_stale_devices(hass, entry)

    entry.async_on_unload(coordinator.async_add_listener(cleanup_stale_devices))

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Thermacell LIV integration setup complete with %d device(s). "
        "Dynamic device support enabled - new devices will be auto-discovered.",
        len(coordinator.data) if coordinator.data else 0,
    )

    return True


@callback
def _async_cleanup_stale_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove devices that no longer exist in the Thermacell account.

    Gold tier requirement: stale-devices
    Automatically removes devices from HA when they're removed from the user's
    Thermacell account. This keeps the device list in sync with the account.
    """
    coordinator: ThermacellLivCoordinator = entry.runtime_data["coordinator"]
    device_registry = dr.async_get(hass)

    # Get all devices for this integration
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    # Get current node IDs from API
    current_node_ids = set(coordinator.data.keys()) if coordinator.data else set()

    # Remove devices that no longer exist in the API response
    for device in devices:
        # Extract node ID from device identifiers
        # Device identifiers format: {(DOMAIN, node_id)}
        node_id = None
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                node_id = identifier[1]
                break

        if node_id and node_id not in current_node_ids:
            _LOGGER.info(
                "Removing stale device '%s' (node_id: %s) - no longer in Thermacell account",
                device.name,
                node_id,
            )
            device_registry.async_remove_device(device.id)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up the client context
    if unload_ok and entry.runtime_data:
        client: ThermacellClient = entry.runtime_data.get("client")
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as err:
                _LOGGER.debug("Error closing Thermacell client: %s", err)

    return unload_ok
