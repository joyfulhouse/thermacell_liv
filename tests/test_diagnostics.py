"""Diagnostics export only anonymous operational measurements."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace
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
    return MagicMock(version=1, data={}, runtime_data={"coordinator": coordinator})


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


@pytest.mark.parametrize("shape", ["tuple", "nested-list", "scalar-list", "set"])
async def test_diagnostics_scrubs_support_containers(diagnostic_entry, shape):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    known = [
        f"SYNTHETIC-{name}"
        for name in (
            "password",
            "token",
            "user",
            "pop",
            "local-user",
            "cached-pop",
            "cached-user",
            "auth-password",
            "auth-user",
        )
    ]
    password, token, user, pop, local_user, cached_pop, cached_user, auth_password, auth_user = known
    diagnostic_entry.data = {"password": password}
    diagnostic_entry.runtime_data["client"] = SimpleNamespace(
        _auth_handler=SimpleNamespace(access_token=token, user_id=user, password=auth_password, username=auth_user),
        api=SimpleNamespace(
            local_transports={
                "account-node": SimpleNamespace(endpoint=SimpleNamespace(pop=cached_pop, username=cached_user))
            }
        ),
    )
    coordinator.get_device.return_value.services.value.side_effect = lambda service, param: {
        "esp.param.local_control_pop": pop,
        "esp.param.local_control_username": local_user,
    }.get(param)
    record = {"pop": "SYNTHETIC-UNKNOWN-POP", "opaque": [*known, "account-node", "LIV Hub"], "support": "benign"}
    payload = {
        "tuple": (record,),
        "nested-list": [[record]],
        "scalar-list": [*known, "benign"],
        "set": {*known, "benign"},
    }[shape]
    coordinator.features.history["account-node"]["metadata"] = payload
    coordinator.features.audit["account-node"]["details"] = payload
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    serialized = json.dumps(result)
    assert all(secret not in serialized for secret in [*known, "SYNTHETIC-UNKNOWN-POP"])
    assert "account-node" not in serialized
    node = result["nodes"]["node_1"]
    assert isinstance(node["maintenance"]["metadata"], list)
    assert "benign" in json.dumps(node["maintenance"]["metadata"])
    assert "benign" in json.dumps(node["last_command"]["details"])
    assert '"LIV Hub"' not in json.dumps(node["maintenance"])
    assert '"LIV Hub"' not in json.dumps(node["last_command"])
    assert node["fw_version"] == "5.4.7"
    assert node["last_command"]["result"] == "failed"


@pytest.mark.parametrize(
    "field", ["type", "model", "fw_version", "led_color", "system_status", "reported_power", "refill_drain"]
)
@pytest.mark.parametrize("malformed", [False, True])
async def test_diagnostics_scrubs_known_secrets_in_support_fields(diagnostic_entry, field, malformed):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    secret = "SYNTHETIC-PASSWORD"
    diagnostic_entry.data = {"password": secret}
    value = object() if malformed else secret
    if field in ("reported_power", "refill_drain"):
        values = coordinator.features.reported if field == "reported_power" else coordinator.features.anomalies
        values["account-node"] = value
    else:
        data = coordinator.data["account-node"]
        if field in ("led_color", "system_status"):
            data = data["devices"]["LIV Hub"]
        data[field] = value
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert secret not in json.dumps(result)
    node = result["nodes"]["node_1"]
    exported = node["devices"]["device_1"] if field in ("led_color", "system_status") else node
    assert exported[field] == (None if malformed else "**REDACTED**")


async def test_diagnostics_labels_are_stable_across_insertion_order(diagnostic_entry):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    node = coordinator.data["account-node"]
    node["devices"]["Another device"] = {**node["devices"]["LIV Hub"], "power": True}
    coordinator.data["z-node"] = {**deepcopy(node), "fw_version": "5.3.2"}
    first = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    coordinator.data = dict(reversed(coordinator.data.items()))
    for data in coordinator.data.values():
        data["devices"] = dict(reversed(data["devices"].items()))
    second = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert first == second
    assert first["nodes"]["node_1"]["fw_version"] == "5.4.7"
    assert first["nodes"]["node_1"]["devices"]["device_1"]["power"] is True
    assert "account-node" not in json.dumps(first)
    assert "Another device" not in json.dumps(first)


async def test_diagnostics_redacts_ota_job_id(diagnostic_entry):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    coordinator.features.history["account-node"]["firmware"] = {
        "job_id": "SYNTHETIC-JOB-ID",
        "description": "Firmware update",
        "version": "5.4.7",
    }
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert "SYNTHETIC-JOB-ID" not in json.dumps(result)
    assert result["nodes"]["node_1"]["maintenance"]["firmware"] == {
        "job_id": "**REDACTED**",
        "description": "Firmware update",
        "version": "5.4.7",
    }


@pytest.mark.parametrize("owner", ["node", "device"])
@pytest.mark.parametrize("key", ["message", "password", "token", "job_id"])
async def test_diagnostics_redacts_original_keys_before_name_scrubbing(diagnostic_entry, owner, key):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    node_id = key if owner == "node" else "account-node"
    node = coordinator.data.pop("account-node")
    coordinator.data[node_id] = node
    if owner == "device":
        node["devices"] = {key: node["devices"]["LIV Hub"]}
    for values in (
        coordinator.features.history,
        coordinator.features.audit,
        coordinator.features.reported,
        coordinator.features.anomalies,
    ):
        values[node_id] = values.pop("account-node")
    historical = "SYNTHETIC-HISTORICAL-CREDENTIAL"
    coordinator.features.audit[node_id] = {key: (historical,), "result": "failed"}
    before = deepcopy((coordinator.data, coordinator.features.history, coordinator.features.audit))
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert historical not in json.dumps(result)
    assert result["nodes"]["node_1"]["last_command"] == {"**REDACTED**": "**REDACTED**", "result": "failed"}
    assert (coordinator.data, coordinator.features.history, coordinator.features.audit) == before


@pytest.mark.parametrize("template", ["Bearer {}", "{} expired", "before:{}:after", "{0}/{0}"])
async def test_diagnostics_scrubs_embedded_credentials_in_keys_and_values(diagnostic_entry, template):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    password, token, pop, username = (f"SYNTHETIC-{kind}" for kind in ("PASSWORD", "TOKEN", "POP", "USERNAME"))
    diagnostic_entry.data = {"password": password}
    diagnostic_entry.runtime_data["client"] = SimpleNamespace(
        _auth_handler=SimpleNamespace(access_token=token),
        api=SimpleNamespace(
            local_transports={"account-node": SimpleNamespace(endpoint=SimpleNamespace(pop=pop, username=username))}
        ),
    )
    coordinator.features.history["account-node"]["firmware"] = {
        "description": template.format(token),
        "additional_info": {template.format(pop): [template.format(password), template.format(username), "benign"]},
    }
    coordinator.features.audit["account-node"]["details"] = (template.format(token), [template.format(pop)])
    before = deepcopy((coordinator.data, coordinator.features.history, coordinator.features.audit))
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert all(secret not in json.dumps(result) for secret in (password, token, pop, username))
    scrubbed = template.format("**REDACTED**")
    node = result["nodes"]["node_1"]
    assert node["maintenance"]["firmware"] == {
        "description": scrubbed,
        "additional_info": {scrubbed: [scrubbed, scrubbed, "benign"]},
    }
    assert node["last_command"]["details"] == [scrubbed, [scrubbed]]
    assert node["fw_version"] == "5.4.7"
    assert (coordinator.data, coordinator.features.history, coordinator.features.audit) == before


@pytest.mark.parametrize("node_id", ["nodes", "node_1", "devices", "device_1"])
async def test_diagnostics_anonymizes_after_scrubbing_support_records(diagnostic_entry, node_id):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    coordinator.data = {node_id: coordinator.data["account-node"]}
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert set(result) == {"entry", "coordinator", "nodes"}
    assert set(result["nodes"]) == {"node_1"}
    node = result["nodes"]["node_1"]
    assert set(node["devices"]) == {"device_1"}
    assert node["devices"]["device_1"]["system_status"] == "Warming Up"
    assert node["model"] == "Thermacell LIV Hub"


@pytest.mark.parametrize("name", ["LIV Hub", "Thermacell LIV Hub", "Protected", "Pool", "power"])
@pytest.mark.parametrize("owner", ["node", "device", "auth-user-id", "serial"])
async def test_diagnostics_labels_do_not_mangle_support(diagnostic_entry, name, owner):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    data = coordinator.data.pop("account-node")
    node_id = name if owner == "node" else "account-node"
    coordinator.data[node_id] = data
    device = data["devices"].pop("LIV Hub")
    data["devices"][name if owner == "device" else "LIV Hub"] = device
    device["system_status"] = "Protected"
    if owner == "auth-user-id":
        diagnostic_entry.runtime_data["client"] = SimpleNamespace(
            _auth_handler=SimpleNamespace(user_id=name), api=SimpleNamespace(local_transports={})
        )
    elif owner == "serial":
        diagnostic_entry.data = {"serial_number": name}
    coordinator.features.history = {node_id: {"description": f"firmware for {name} hub", "opaque": name}}
    before = deepcopy((coordinator.data, coordinator.features.history))
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    node = result["nodes"]["node_1"]
    assert node["model"] == "Thermacell LIV Hub"
    assert node["devices"]["device_1"]["system_status"] == "Protected"
    assert node["devices"]["device_1"]["power"] is False
    description = name if owner == "device" else "**REDACTED**"
    assert node["maintenance"] == {"description": f"firmware for {description} hub", "opaque": "**REDACTED**"}
    assert (coordinator.data, coordinator.features.history) == before


@pytest.mark.parametrize("field,secret", [("model", "Thermacell LIV Hub"), ("system_status", "Protected")])
async def test_diagnostics_credentials_override_standard_literals(diagnostic_entry, field, secret):
    diagnostic_entry.data = {"password": secret}
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    coordinator.data["account-node"]["devices"]["LIV Hub"]["system_status"] = "Protected"
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    node = result["nodes"]["node_1"]
    record = node if field == "model" else node["devices"]["device_1"]
    assert record[field] == "**REDACTED**"
    assert secret not in json.dumps(result)


async def test_diagnostics_preserves_colliding_scrubbed_keys(diagnostic_entry):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    token, pop = "SYNTHETIC-TOKEN-A", "SYNTHETIC-POP-B"
    diagnostic_entry.data = {"access_token": token, "pop": pop}
    details = {
        f"detail:{token}": {"result": "failed"},
        f"detail:{pop}": {"result": "confirmed"},
        "detail:**REDACTED**": {"result": "original"},
        "detail:**REDACTED**_2": {"result": "suffixed"},
    }
    coordinator.features.audit["account-node"]["details"] = details
    before = deepcopy(coordinator.features.audit)
    first = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert token not in json.dumps(first) and pop not in json.dumps(first)
    assert first["nodes"]["node_1"]["last_command"]["details"] == {
        "detail:**REDACTED**": {"result": "original"},
        "detail:**REDACTED**_2": {"result": "suffixed"},
        "detail:**REDACTED**_3": {"result": "confirmed"},
        "detail:**REDACTED**_4": {"result": "failed"},
    }
    assert coordinator.features.audit == before
    coordinator.features.audit["account-node"]["details"] = dict(reversed(details.items()))
    assert await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry) == first


@pytest.mark.parametrize("secret", ["Q", "Q7", "Q7Z"])
@pytest.mark.parametrize("credential", ["pop", "username"])
async def test_diagnostics_redacts_strings_containing_short_credentials(diagnostic_entry, secret, credential):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    endpoint = SimpleNamespace(pop=None, username=None)
    setattr(endpoint, credential, secret)
    diagnostic_entry.runtime_data["client"] = SimpleNamespace(
        api=SimpleNamespace(local_transports={"account-node": SimpleNamespace(endpoint=endpoint)})
    )
    coordinator.features.history["account-node"]["metadata"] = {
        f"proof:{secret}": f"proof={secret}",
        "items": [f"proof:{secret}", (f"proof={secret}",)],
        "benign": "unchanged support",
    }
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert secret not in json.dumps(result)
    node = result["nodes"]["node_1"]
    assert node["maintenance"]["metadata"] == {
        "**REDACTED**": "**REDACTED**",
        "items": ["**REDACTED**", ["**REDACTED**"]],
        "benign": "unchanged support",
    }
    assert node["model"] == "Thermacell LIV Hub"
    assert node["devices"]["device_1"]["system_status"] == "Warming Up"


@pytest.mark.parametrize(
    "identifier",
    ["node_id", "hub_serial", "job_id", "user_id", "account_id", "unique_id", "title"],
)
@pytest.mark.parametrize("secret", ["SYNTHETIC-IDENTIFIER", "Q", "Q7", "Q7Z"])
async def test_diagnostics_scrubs_embedded_machine_identifiers(diagnostic_entry, identifier, secret):
    coordinator = diagnostic_entry.runtime_data["coordinator"]
    if identifier == "node_id":
        coordinator.data[secret] = coordinator.data.pop("account-node")
    elif identifier == "hub_serial":
        coordinator.data["account-node"][identifier] = secret
    elif identifier == "job_id":
        coordinator.features.history["account-node"]["firmware"] = {identifier: secret}
    elif identifier == "user_id":
        diagnostic_entry.runtime_data["client"] = SimpleNamespace(
            _auth_handler=SimpleNamespace(user_id=secret), api=SimpleNamespace(local_transports={})
        )
    elif identifier == "account_id":
        diagnostic_entry.data = {identifier: secret}
    else:
        setattr(diagnostic_entry, identifier, secret)
    node_id = next(iter(coordinator.data))
    details = {
        f"record:{secret}": [f"id={secret}", (f"id:{secret}",)],
        "record:**REDACTED**": "unchanged support",
    }
    coordinator.features.audit[node_id] = {"result": "failed", "details": details}
    before = deepcopy((coordinator.data, coordinator.features.history, coordinator.features.audit))
    result = await async_get_config_entry_diagnostics(MagicMock(), diagnostic_entry)
    assert secret not in json.dumps(result)
    node = result["nodes"]["node_1"]
    key = "**REDACTED**" if len(secret) < 4 else "record:**REDACTED**_2"
    values = ["**REDACTED**", ["**REDACTED**"]] if len(secret) < 4 else ["id=**REDACTED**", ["id:**REDACTED**"]]
    assert node["last_command"] == {
        "result": "failed",
        "details": {
            "record:**REDACTED**": "unchanged support",
            key: values,
        },
    }
    assert node["model"] == "Thermacell LIV Hub"
    assert node["devices"]["device_1"]["system_status"] == "Warming Up"
    assert (coordinator.data, coordinator.features.history, coordinator.features.audit) == before
