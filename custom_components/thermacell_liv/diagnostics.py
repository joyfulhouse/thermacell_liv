"""Diagnostics support for Thermacell LIV."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_USERNAME

# Keys to redact from diagnostics
TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    "user_id",
    "access_token",
    "idtoken",
    "refreshtoken",
    "hub_serial",
    "Hub ID",
}


async def async_get_config_entry_diagnostics(_hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data["coordinator"]

    # Gather all diagnostic data
    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "domain": entry.domain,
            "version": entry.version,
            "unique_id": entry.unique_id,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": (
                str(coordinator.last_update_success_time) if coordinator.last_update_success_time else None
            ),
            "update_interval": str(coordinator.update_interval),
            "node_count": len(coordinator.data) if coordinator.data else 0,
        },
        "nodes": {},
    }

    # Add detailed node information
    if coordinator.data:
        for node_id, node_data in coordinator.data.items():
            diagnostics_data["nodes"][node_id] = {
                "name": node_data.get("name"),
                "type": node_data.get("type"),
                "model": node_data.get("model"),
                "fw_version": node_data.get("fw_version"),
                "online": node_data.get("online"),
                "system_runtime": node_data.get("system_runtime"),
                "devices": {},
            }

            # Add device information
            for device_name, device_data in node_data.get("devices", {}).items():
                diagnostics_data["nodes"][node_id]["devices"][device_name] = {
                    "power": device_data.get("power"),
                    "led_power": device_data.get("led_power"),
                    "led_brightness": device_data.get("led_brightness"),
                    "led_brightness_pct": device_data.get("led_brightness_pct"),
                    "led_color": device_data.get("led_color"),
                    "refill_life": device_data.get("refill_life"),
                    "system_status": device_data.get("system_status"),
                    "system_status_code": device_data.get("system_status_code"),
                    "error_code": device_data.get("error_code"),
                    "last_updated": device_data.get("last_updated"),
                }

    # Redact sensitive information
    return async_redact_data(diagnostics_data, TO_REDACT)
