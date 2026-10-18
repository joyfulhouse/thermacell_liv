"""Allowlisted diagnostics without account, node, or local-control credentials."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


def _measurements(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Do not copy arbitrary nested metadata, labels, audit errors, or strings."""
    return {key: value for key in keys if type(value := data.get(key)) in (bool, int, float) or value is None}


async def async_get_config_entry_diagnostics(_hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Export only operational measurements under anonymous node/device labels."""
    coordinator = entry.runtime_data["coordinator"]
    nodes = {}
    for index, node_data in enumerate((coordinator.data or {}).values(), 1):
        node = _measurements(node_data, ("online", "system_runtime"))
        node["devices"] = {
            f"device_{device_index}": _measurements(
                device_data,
                (
                    "power",
                    "led_power",
                    "led_brightness",
                    "led_brightness_pct",
                    "refill_life",
                    "cartridge_present",
                    "system_status_code",
                    "error_code",
                    "last_updated",
                ),
            )
            for device_index, device_data in enumerate(node_data.get("devices", {}).values(), 1)
        }
        nodes[f"node_{index}"] = node
    return {
        "entry": {"domain": DOMAIN, "version": entry.version},
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": (
                str(coordinator.last_update_success_time) if coordinator.last_update_success_time else None
            ),
            "update_interval": str(coordinator.update_interval),
            "node_count": len(nodes),
        },
        "nodes": nodes,
    }
