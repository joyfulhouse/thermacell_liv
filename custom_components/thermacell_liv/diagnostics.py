"""Allowlisted diagnostics without account, node, or local-control credentials."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "username",
    "password",
    "user_id",
    "account_id",
    "title",
    "unique_id",
    "access_token",
    "idtoken",
    "refreshtoken",
    "token",
    "pop",
    "proof_of_possession",
    "local_username",
    "hub_serial",
    "Hub ID",
    "node_id",
    "nodeid",
    "device_id",
    "serial_num",
    "serial_number",
    "name",
    "user_name",
    "email",
    "refresh_token",
    "id_token",
    "message",
}


def _measurements(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Do not copy arbitrary nested metadata, labels, audit errors, or strings."""
    return {key: value for key in keys if type(value := data.get(key)) in (bool, int, float) or value is None}


async def async_get_config_entry_diagnostics(_hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Export support data under anonymous node/device labels, redacting secrets."""
    coordinator = entry.runtime_data["coordinator"]
    nodes = {}
    for index, (node_id, node_data) in enumerate((coordinator.data or {}).items(), 1):
        node = _measurements(node_data, ("online", "system_runtime"))
        node.update(
            {
                "type": node_data.get("type"),
                "model": node_data.get("model"),
                "fw_version": node_data.get("fw_version"),
                "maintenance": coordinator.features.history.get(node_id, {}),
                "last_command": coordinator.features.audit.get(node_id, {}),
                "reported_power": coordinator.features.reported.get(node_id),
                "refill_drain": coordinator.features.anomalies.get(node_id),
            }
        )
        node["devices"] = {
            f"device_{device_index}": {
                **_measurements(
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
                ),
                "led_color": device_data.get("led_color"),
                "system_status": device_data.get("system_status"),
            }
            for device_index, device_data in enumerate(node_data.get("devices", {}).values(), 1)
        }
        nodes[f"node_{index}"] = node
    return async_redact_data(
        {
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
        },
        TO_REDACT,
    )
