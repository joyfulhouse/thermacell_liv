"""Diagnostics export only anonymous operational measurements."""

from datetime import timedelta
import json
from unittest.mock import MagicMock, patch

import pytest

from custom_components.thermacell_liv.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.parametrize("with_nodes", [False, True])
async def test_diagnostics_allowlist(with_nodes):
    secrets = [
        f"SENTINEL-{name}"
        for name in (
            "account",
            "password",
            "pop",
            "local-username",
            "token",
            "unique-id",
            "node",
            "device",
        )
    ]
    account, password, pop, username, token, unique_id, node_id, device_name = secrets
    sensitive = {"user_id": account, "password": password, "pop": pop, "username": username, "token": token}
    device = {
        **sensitive,
        "power": True,
        "refill_life": 75.0,
        "error_code": 0,
        "led_color": {"r": 1, "secret": pop},
        "last_updated": token,
    }
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.last_update_success_time = None
    coordinator.update_interval = timedelta(seconds=60)
    coordinator.data = (
        {
            node_id: {
                **sensitive,
                "name": account,
                "online": True,
                "system_runtime": 120,
                "devices": {device_name: device},
            }
        }
        if with_nodes
        else {}
    )
    coordinator.features.history = {node_id: sensitive}
    coordinator.features.audit = {node_id: {"message": pop}}
    coordinator.features.reported = {node_id: sensitive}
    coordinator.features.anomalies = {node_id: sensitive}
    entry = MagicMock(title=f"Thermacell LIV ({account})", unique_id=unique_id, version=1, domain="thermacell_liv")
    entry.data = sensitive
    entry.options = sensitive
    entry.runtime_data = {"coordinator": coordinator}

    result = await async_get_config_entry_diagnostics(MagicMock(), entry)
    serialized = json.dumps(result)
    assert all(secret not in serialized for secret in secrets)
    assert result == {
        "entry": {"domain": "thermacell_liv", "version": 1},
        "coordinator": {
            "last_update_success": True,
            "last_update_success_time": None,
            "update_interval": "0:01:00",
            "node_count": int(with_nodes),
        },
        "nodes": {
            "node_1": {
                "online": True,
                "system_runtime": 120,
                "devices": {
                    "device_1": {
                        "power": True,
                        "led_power": None,
                        "led_brightness": None,
                        "led_brightness_pct": None,
                        "refill_life": 75.0,
                        "cartridge_present": None,
                        "system_status_code": None,
                        "error_code": 0,
                    }
                },
            }
        }
        if with_nodes
        else {},
    }


async def test_diagnostics_rejects_nested_values_in_measurements():
    coordinator = MagicMock(
        last_update_success=False, last_update_success_time=None, update_interval=timedelta(seconds=60)
    )
    coordinator.data = {
        "account-node": {
            "online": {"pop": "SECRET"},
            "system_runtime": "SECRET",
            "devices": {"account-device": {"power": ["SECRET"]}},
        }
    }
    coordinator.features.history = {}
    coordinator.features.audit = {}
    coordinator.features.reported = {}
    coordinator.features.anomalies = {}
    entry = MagicMock(
        version=1, domain="thermacell_liv", title="Title", unique_id="id", runtime_data={"coordinator": coordinator}
    )
    result = await async_get_config_entry_diagnostics(MagicMock(), entry)
    assert "SECRET" not in json.dumps(result)
    assert "online" not in result["nodes"]["node_1"]
    assert "power" not in result["nodes"]["node_1"]["devices"]["device_1"]


async def test_diagnostics_retains_defense_in_depth_redaction():
    coordinator = MagicMock(
        last_update_success=True, last_update_success_time=None, update_interval=timedelta(seconds=60)
    )
    coordinator.data = {"node": {"devices": {}}}
    entry = MagicMock(
        version=1, domain="thermacell_liv", title="Title", unique_id="id", runtime_data={"coordinator": coordinator}
    )
    with patch("custom_components.thermacell_liv.diagnostics._measurements", return_value={"pop": "SENTINEL-POP"}):
        result = await async_get_config_entry_diagnostics(MagicMock(), entry)
    assert "SENTINEL-POP" not in json.dumps(result)
    assert result["nodes"]["node_1"]["pop"] == "**REDACTED**"
