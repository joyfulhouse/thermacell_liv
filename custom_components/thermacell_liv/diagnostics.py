"""Allowlisted diagnostics without account, node, or local-control credentials."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.components.diagnostics.const import REDACTED
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
    "job_id",
}


def _json_data(value: Any, secrets: set[str]) -> Any:
    """Redact original keys before normalizing containers and scrubbing strings."""
    if isinstance(value, Mapping):
        return {
            _json_data(key, secrets): _json_data(item, secrets)
            for key, item in async_redact_data(value, TO_REDACT).items()
            if isinstance(key, str)
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_data(item, secrets) for item in value]
    if isinstance(value, str):
        if value in secrets:
            return REDACTED
        for secret in sorted(secrets, key=len, reverse=True):
            if len(secret) >= 4:
                value = value.replace(secret, REDACTED)
        return value
    return value if type(value) in (bool, int, float) or value is None else None


def _measurements(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Do not copy arbitrary nested metadata, labels, audit errors, or strings."""
    return {key: value for key in keys if type(value := data.get(key)) in (bool, int, float) or value is None}


async def async_get_config_entry_diagnostics(_hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Export support data under anonymous node/device labels, redacting secrets."""
    coordinator = entry.runtime_data["coordinator"]
    known = [*entry.data.values(), entry.title, entry.unique_id, *(coordinator.data or {})]
    client = entry.runtime_data.get("client", coordinator.client)
    auth = getattr(client, "_auth_handler", None)
    known.extend(getattr(auth, key, None) for key in ("username", "password", "access_token", "user_id"))
    for transport in client.api.local_transports.values():
        known.extend((transport.endpoint.pop, transport.endpoint.username))
    for node_id, data in (coordinator.data or {}).items():
        known.extend(data.get("devices", {}))
        if (device := coordinator.get_device(node_id)) is not None:
            known.extend(
                device.services.value("esp.service.local_control", f"esp.param.local_control_{key}")
                for key in ("pop", "username")
            )
    secrets = {value for value in known if isinstance(value, str) and value}
    nodes = {}
    for index, (node_id, node_data) in enumerate(sorted((coordinator.data or {}).items()), 1):
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
        node = _json_data(node, secrets)
        node["devices"] = {
            f"device_{device_index}": _json_data(
                {
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
                },
                secrets,
            )
            for device_index, (_, device_data) in enumerate(sorted(node_data.get("devices", {}).items()), 1)
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
