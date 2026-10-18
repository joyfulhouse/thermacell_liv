"""Diagnostics export only anonymous operational measurements."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json
from unittest.mock import MagicMock, patch

import pytest

from custom_components.thermacell_liv.diagnostics import async_get_config_entry_diagnostics


@pytest.fixture
def diagnostic_entry():
    coordinator = MagicMock(
        last_update_success=True, last_update_success_time=None, update_interval=timedelta(seconds=60)
    )
    coordinator.data = {
        "account-node": {
            "type": "thermacell-hub",
            "model": "Thermacell LIV Hub",
            "fw_version": "5.4.7",
            "online": True,
            "system_runtime": 120,
            "devices": {
                "LIV Hub": {
                    "power": False,
                    "led_power": True,
                    "led_brightness": 128,
                    "led_brightness_pct": 50,
                    "led_color": {"r": 255, "g": 128, "b": 0},
                    "refill_life": 75,
                    "cartridge_present": True,
                    "system_status": "Warming Up",
                    "system_status_code": 2,
                    "error_code": 0,
                    "last_updated": 1234567890,
                }
            },
        }
    }
    coordinator.features.history = {"account-node": {"reset_at": "2026-10-18T12:00:00+00:00", "applied_type": 1}}
    coordinator.features.audit = {
        "account-node": {
            "command": "power",
            "result": "failed",
            "requested_power": False,
            "time": "2026-10-18T12:00:00+00:00",
        }
    }
    coordinator.features.reported = {"account-node": True}
    coordinator.features.anomalies = {"account-node": False}
    return MagicMock(version=1, runtime_data={"coordinator": coordinator})


@pytest.mark.parametrize(
    "field,expected",
    [
        ("type", "thermacell-hub"),
        ("model", "Thermacell LIV Hub"),
        ("fw_version", "5.4.7"),
        ("maintenance", {"reset_at": "2026-10-18T12:00:00+00:00", "applied_type": 1}),
        (
            "last_command",
            {
                "command": "power",
                "result": "failed",
                "requested_power": False,
                "time": "2026-10-18T12:00:00+00:00",
            },
        ),
        ("reported_power", True),
        ("refill_drain", False),
        ("devices/device_1/led_color", {"r": 255, "g": 128, "b": 0}),
        ("devices/device_1/system_status", "Warming Up"),
    ],
)
async def test_support_fields_are_retained(diagnostic_entry, field, expected):
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    value = result["nodes"]["node_1"]
    for key in field.split("/"):
        value = value[key]
    assert value == expected
    device = result["nodes"]["node_1"]["devices"]["device_1"]
    assert device["power"] is False
    assert device["system_status_code"] == 2
    assert device["led_brightness"] == 128
    assert device["led_brightness_pct"] == 50
    assert device["refill_life"] == 75
    assert device["cartridge_present"] is True
    assert device["error_code"] == 0
    assert device["last_updated"] == 1234567890


@pytest.mark.parametrize("updated", [None, datetime(2026, 10, 18, 12, tzinfo=UTC)])
async def test_multiple_nodes_and_update_time(diagnostic_entry, updated):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    coordinator.last_update_success_time = updated
    coordinator.data["second-node"] = deepcopy(coordinator.data["account-node"])
    coordinator.data["second-node"]["fw_version"] = "5.3.2"
    coordinator.data["second-node"]["online"] = False
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert result["coordinator"] == {
        "last_update_success": True,
        "last_update_success_time": str(updated) if updated else None,
        "update_interval": "0:01:00",
        "node_count": 2,
    }
    assert set(result["nodes"]) == {"node_1", "node_2"}
    assert result["nodes"]["node_1"]["fw_version"] == "5.4.7"
    assert result["nodes"]["node_2"]["fw_version"] == "5.3.2"
    assert result["nodes"]["node_1"]["online"] is True
    assert result["nodes"]["node_2"]["online"] is False
    assert result["nodes"]["node_2"]["maintenance"] == {}
    assert result["nodes"]["node_2"]["last_command"] == {}
    assert result["nodes"]["node_2"]["reported_power"] is None
    assert result["nodes"]["node_2"]["refill_drain"] is None


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
    sensitive = {
        "user_id": account,
        "account_id": account,
        "password": password,
        "pop": pop,
        "proof_of_possession": pop,
        "username": username,
        "local_username": username,
        "token": token,
        "access_token": token,
        "idtoken": token,
        "refreshtoken": token,
        "id_token": token,
        "refresh_token": token,
        "node_id": node_id,
        "nodeid": node_id,
        "device_id": device_name,
        "name": account,
        "serial_num": device_name,
        "serial_number": device_name,
        "hub_serial": node_id,
        "Hub ID": node_id,
        "email": account,
        "user_name": username,
        "title": account,
        "unique_id": unique_id,
    }
    redacted = dict.fromkeys(sensitive, "**REDACTED**")
    device = {
        **sensitive,
        "power": True,
        "refill_life": 75.0,
        "error_code": 0,
        "led_color": {"r": 1, "pop": pop},
        "system_status": "Warming Up",
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
                "type": "thermacell-hub",
                "model": "Thermacell LIV Hub",
                "fw_version": "5.4.7",
                "devices": {device_name: device},
            }
        }
        if with_nodes
        else {}
    )
    coordinator.features.history = {node_id: {"applied_type": 1, "metadata": [sensitive]}}
    coordinator.features.audit = {
        node_id: {"command": "power", "result": "failed", "message": f"{account}: {pop}", "details": [sensitive]}
    }
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
                "type": "thermacell-hub",
                "model": "Thermacell LIV Hub",
                "fw_version": "5.4.7",
                "maintenance": {"applied_type": 1, "metadata": [redacted]},
                "last_command": {
                    "command": "power",
                    "result": "failed",
                    "message": "**REDACTED**",
                    "details": [redacted],
                },
                "reported_power": redacted,
                "refill_drain": redacted,
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
                        "led_color": {"r": 1, "pop": "**REDACTED**"},
                        "system_status": "Warming Up",
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


async def test_diagnostics_retains_defense_in_depth_redaction(diagnostic_entry):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    coordinator.data = {"node": {"devices": {}}}
    with patch("custom_components.thermacell_liv.diagnostics._measurements", return_value={"pop": "SENTINEL-POP"}):
        result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert "SENTINEL-POP" not in json.dumps(result)
    assert result["nodes"]["node_1"]["pop"] == "**REDACTED**"
