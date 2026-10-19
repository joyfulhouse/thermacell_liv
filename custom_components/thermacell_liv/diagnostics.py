"""Allowlisted diagnostics without account, node, or local-control credentials."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.components.diagnostics.const import REDACTED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_CREDENTIAL_KEYS = {
    "username",
    "password",
    "access_token",
    "idtoken",
    "refreshtoken",
    "token",
    "pop",
    "proof_of_possession",
    "local_username",
    "user_name",
    "email",
    "refresh_token",
    "id_token",
}
TO_REDACT = _CREDENTIAL_KEYS | {
    "user_id",
    "account_id",
    "title",
    "unique_id",
    "hub_serial",
    "Hub ID",
    "node_id",
    "nodeid",
    "device_id",
    "serial_num",
    "serial_number",
    "name",
    "message",
    "job_id",
}


def _json_data(value: Any, credentials: set[str], labels: set[str]) -> Any:
    """Redact original keys before normalizing containers and scrubbing strings."""
    if isinstance(value, Mapping):
        result = {}
        redacted = async_redact_data(value, TO_REDACT)
        for original in sorted(key for key in redacted if isinstance(key, str)):
            base = key = _json_data(original, credentials, labels)
            suffix = 2
            while key in result:
                key = f"{base}_{suffix}"
                suffix += 1
            result[key] = _json_data(redacted[original], credentials, labels)
        return result
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_data(item, credentials, labels) for item in value]
    if isinstance(value, str):
        if value in credentials or value in labels:
            return REDACTED
        for secret in sorted(credentials, key=lambda item: (-len(item), item)):
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
    known = [entry.unique_id, *(value for key, value in entry.data.items() if key in _CREDENTIAL_KEYS)]
    client = entry.runtime_data.get("client", coordinator.client)
    auth = getattr(client, "_auth_handler", None)
    known.extend(getattr(auth, key, None) for key in ("username", "password", "access_token"))
    labels = {
        value
        for value in (
            entry.title,
            getattr(auth, "user_id", None),
            *(coordinator.data or {}),
            *(value for key, value in entry.data.items() if key not in _CREDENTIAL_KEYS),
        )
        if isinstance(value, str) and value
    }
    for transport in client.api.local_transports.values():
        known.extend((transport.endpoint.pop, transport.endpoint.username))
    for node_id, data in (coordinator.data or {}).items():
        labels.update(data.get("devices", {}))
        if (device := coordinator.get_device(node_id)) is not None:
            known.extend(
                device.services.value("esp.service.local_control", f"esp.param.local_control_{key}")
                for key in ("pop", "username")
            )
    credentials = {value for value in known if isinstance(value, str) and value}
    nodes = {}
    for index, (node_id, node_data) in enumerate(sorted((coordinator.data or {}).items()), 1):
        node = _measurements(node_data, ("online", "system_runtime"))
        node.update(
            {
                "type": node_data.get("type"),
                "fw_version": node_data.get("fw_version"),
                "maintenance": coordinator.features.history.get(node_id, {}),
                "last_command": coordinator.features.audit.get(node_id, {}),
                "reported_power": coordinator.features.reported.get(node_id),
                "refill_drain": coordinator.features.anomalies.get(node_id),
            }
        )
        node = {
            key: _json_data(value, credentials, labels) for key, value in async_redact_data(node, TO_REDACT).items()
        }
        # Standard model/status literals can coincide with names without identifying a hub.
        node["model"] = _json_data(node_data.get("model"), credentials, labels - {"Thermacell LIV Hub"})
        node["devices"] = {
            f"device_{device_index}": {
                **{
                    key: _json_data(value, credentials, labels)
                    for key, value in async_redact_data(
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
                        },
                        TO_REDACT,
                    ).items()
                },
                "system_status": _json_data(
                    device_data.get("system_status"),
                    credentials,
                    labels - {"Off", "Warming Up", "Protected", "Unknown"},
                ),
            }
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
