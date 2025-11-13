"""The Thermacell LIV integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import ThermacellLivAPI
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import ThermacellLivCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.LIGHT, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Thermacell LIV from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Initialize API client
    api = ThermacellLivAPI(hass, username, password)

    # Test authentication
    if not await api.authenticate():
        raise ConfigEntryNotReady("Failed to authenticate with Thermacell API")

    # Initialize coordinator with configurable scan interval
    scan_interval = entry.options.get("scan_interval", 60)
    coordinator = ThermacellLivCoordinator(hass, api, scan_interval=scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in runtime_data (HA 2024.x+ best practice)
    entry.runtime_data = coordinator

    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms - runtime_data is automatically cleared by HA
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
