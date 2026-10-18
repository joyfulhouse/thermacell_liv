"""Native controls, persisted history, and shutdown evidence."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pythermacell import ThermacellDevice
from pythermacell.models import Group
from pythermacell.parsers import parse_device_state
from pythermacell.services import TIMER_ID, TIMER_NAME, FirmwareUpdate, HubServices, Schedule

from custom_components.thermacell_liv.binary_sensor import ThermacellDiagnosticFlag
from custom_components.thermacell_liv.button import ThermacellNativeButton, native_buttons
from custom_components.thermacell_liv.coordinator import ThermacellLivCoordinator
from custom_components.thermacell_liv.features import HubFeatures
from custom_components.thermacell_liv.sensor import ThermacellFeatureSensor
from custom_components.thermacell_liv.switch import ThermacellGroupSwitch, ThermacellLivSwitch, ThermacellScheduleSwitch
from custom_components.thermacell_liv.text import ThermacellTimezone
from custom_components.thermacell_liv.update import ThermacellFirmwareUpdate
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


@pytest.fixture
def feature_hub():
    client = MagicMock()
    client.get_groups = AsyncMock(return_value=[Group("g", "Yard", False, False, 1)])
    client.get_group_nodes = AsyncMock(return_value=["n"])
    client.api.last_transport = {"n": "local"}
    coordinator = ThermacellLivCoordinator(MagicMock(), client)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_update_listeners = MagicMock()
    device = ThermacellDevice(
        MagicMock(),
        parse_device_state(
            "n",
            {"LIV Hub": {"Name": "Yard", "Enable Repellers": False, "System Status": 1, "Refill Life": 80}},
            {"connectivity": {"connected": True}},
            {"info": {"fw_version": "5.4.1"}},
        ),
        enable_queue=False,
    )
    services = MagicMock(spec=HubServices)
    services.supports.return_value = True
    services.schedules = [Schedule("app", "Evening", True, [{"m": 100}], {"LIV Hub": {"Enable Repellers": True}})]
    services.timezone = "America/New_York"
    services.check_firmware = AsyncMock(return_value=FirmwareUpdate(True, "6.0", "job", "Fixes"))
    device.services = services
    device.set_power = AsyncMock(return_value=True)
    device.reset_refill = AsyncMock(return_value=True)
    device.refresh = AsyncMock(return_value=True)
    coordinator._devices = {"n": device}
    coordinator.data = {"n": coordinator._device_to_node_data(device)}
    coordinator.nodes = coordinator.data
    coordinator.last_update_success = True
    return coordinator, device, services


async def test_reset_metadata_survives_storage_and_failed_reset_does_not_replace_it(feature_hub, tmp_path):
    coordinator, device, _ = feature_hub
    features = coordinator.features
    real_hass = HomeAssistant(str(tmp_path))
    coordinator.hass = real_hass
    await features.async_load("entry")
    assert features.remaining_hours("n", 80) is None
    assert await coordinator.async_reset_refill_life("n", "Yard", 2)
    reset_at = features.history["n"]["reset_at"]
    coordinator.refill_types["n"] = 0
    assert features.remaining_hours("n", 50) == 90
    device.reset_refill.return_value = False
    assert not await coordinator.async_reset_refill_life("n", "Yard", 0)
    assert features.history["n"]["reset_at"] == reset_at
    assert features.history["n"]["applied_type"] == 2
    restored = HubFeatures(coordinator)
    await restored.async_load("entry")
    assert restored.history == features.history
    assert restored.remaining_hours("n", 50) == 90
    assert restored.remaining_hours("n", None) is None
    await real_hass.async_stop(force=True)


async def test_run_timer_before_power_and_retain_safeguard_on_failed_start(feature_hub):
    coordinator, device, services = feature_hub
    order = []

    async def timer(seconds):
        order.append(("timer", seconds))

    async def power(*args, **kwargs):
        order.append(("power", args[0]))
        return True

    services.set_shutdown_timer.side_effect = timer
    device.set_power.side_effect = power
    await coordinator.features.command("n", "run_for", 1800)
    assert order == [("timer", 1800), ("power", True)]
    assert coordinator.features.audit["n"]["requested_power"] is True
    services.cancel_shutdown_timer.assert_not_awaited()
    device.set_power.side_effect = None
    device.set_power.return_value = False
    with pytest.raises(HomeAssistantError, match="did not confirm"):
        await coordinator.features.command("n", "run_for", 1800)
    services.cancel_shutdown_timer.assert_not_awaited()
    assert coordinator.features.audit["n"]["result"] == "failed"
    services.set_shutdown_timer.side_effect = RuntimeError("Rejected")
    device.set_power.reset_mock()
    with pytest.raises(HomeAssistantError):
        await coordinator.features.command("n", "run_for", 3600)
    device.set_power.assert_not_awaited()


async def test_shutdown_cancel_and_native_commands(feature_hub):
    coordinator, device, services = feature_hub
    features = coordinator.features
    await features.command("n", "schedule_shutdown", 1800)
    device.set_power.assert_not_awaited()
    services.schedules.append(Schedule(TIMER_ID, TIMER_NAME, True))
    assert features.shutdown_at("n") is not None
    await features.command("n", "cancel_timer")
    assert features.shutdown_at("n") is None
    services.cancel_shutdown_timer.assert_awaited_once()
    await features.command("n", "timezone", "UTC")
    services.set_timezone.assert_awaited_once_with("UTC")
    await features.command("n", "reboot")
    services.reboot.assert_awaited_once()
    await features.command("n", "schedule", ("app", False))
    services.set_schedule_enabled.assert_awaited_once_with("app", False)
    device.refresh.return_value = False
    with pytest.raises(HomeAssistantError, match="refresh timer"):
        await features.command("n", "cancel_timer")
    with pytest.raises(HomeAssistantError, match="Unknown"):
        await features.command("n", "invalid")
    with pytest.raises(HomeAssistantError, match="no longer"):
        await features.command("missing", "reboot")


def test_drain_requires_continuous_off_reports_not_optimism(feature_hub):
    coordinator, device, _ = feature_hub
    features = coordinator.features
    start = datetime(2026, 10, 18, tzinfo=UTC)
    with patch("custom_components.thermacell_liv.features.dt_util.utcnow") as clock:
        for minute in range(11):
            clock.return_value = start + timedelta(minutes=minute)
            device._state.params.refill_life = 80 if minute < 8 else 77
            features.observe(device)
            assert features.anomalies["n"] is (minute == 10)
        device._state.params.system_status = 3
        features.observe(device)
        assert features.anomalies["n"] is False
        assert features.reported["n"] is True
        device._state.params.system_status = 1
        features.observe(device)
        clock.return_value += timedelta(hours=2)
        features.observe(device)
        assert features.anomalies["n"] is False
        device._state.params.refill_life = None
        features.observe(device)
        assert features.anomalies["n"] is None
        device._state.status.connected = False
        features.observe(device)
        assert features.reported["n"] is None


async def test_optional_refresh_throttling_and_failure_isolation(feature_hub):
    coordinator, _, services = feature_hub
    features = coordinator.features
    await features.async_refresh()
    assert features.groups == {"g": {"name": "Yard", "nodes": ["n"]}}
    assert features.groups_available
    await features.async_refresh()
    coordinator.client.get_groups.assert_awaited_once_with(strict=True)
    services.check_firmware.assert_awaited_once()
    features.firmware["n"].status = "triggered"
    await features.async_refresh()
    services.refresh_firmware_status.assert_awaited_once()
    features._next_groups = datetime.min.replace(tzinfo=UTC)
    coordinator.client.get_groups.side_effect = RuntimeError()
    services.refresh_firmware_status.side_effect = RuntimeError()
    await features.async_refresh()
    assert not features.groups_available
    assert features.groups["g"]["nodes"] == ["n"]
    assert "n" in features.firmware_errors
    features.firmware["n"].status = None
    await features.command("n", "check_firmware")
    assert "n" not in features.firmware_errors


async def test_group_partial_failure_keeps_successful_members(feature_hub):
    coordinator, device, _ = feature_hub
    features = coordinator.features
    await features.async_refresh()
    features.observe(device)
    entity = ThermacellGroupSwitch(coordinator, "entry", "g")
    assert entity.available and not entity.is_on
    assert entity.name == "Thermacell group Yard"
    assert entity.extra_state_attributes == {"node_ids": ["n"]}
    await entity.async_turn_on()
    await entity.async_turn_off()
    assert device.set_power.await_count == 2
    features.groups["g"]["nodes"].append("offline")
    assert entity.is_on is None
    with pytest.raises(HomeAssistantError, match="offline"):
        await entity.async_turn_off()
    device.set_power.assert_awaited_with(False, verify=True)
    features.groups["g"]["nodes"] = []
    with pytest.raises(HomeAssistantError, match="empty"):
        await features.group_power("g", False)
    features.groups_available = False
    with pytest.raises(HomeAssistantError, match="membership"):
        await features.group_power("g", False)


async def test_timed_run_with_warming_up_off_report_fails_switch_and_group(feature_hub):
    """Replay the ADU report through the real library confirmation path."""
    coordinator, device, services = feature_hub
    device.set_power = ThermacellDevice.set_power.__get__(device)
    device._api.update_node_params = AsyncMock(return_value=(200, {"status": "success"}))
    device._api.get_node_params = AsyncMock(
        return_value=(200, {"LIV Hub": {"Enable Repellers": True, "System State": 2, "System Status": 2}})
    )
    await coordinator.features.command("n", "run_for", 60)
    services.set_shutdown_timer.assert_awaited_once_with(60)
    device._api.get_node_params.return_value = (
        200,
        {"LIV Hub": {"Enable Repellers": False, "System State": 2, "System Status": 2, "Error": 0}},
    )
    coordinator.features.groups = {"g": {"name": "Yard", "nodes": ["n"]}}
    coordinator.features.groups_available = True
    with patch("pythermacell.devices.asyncio.sleep", new_callable=AsyncMock):
        switch = ThermacellLivSwitch(coordinator, "n", "Yard")
        with pytest.raises(HomeAssistantError, match="Failed to change"):
            await switch.async_turn_off()
        with pytest.raises(HomeAssistantError, match="n"):
            await coordinator.features.group_power("g", False)
    assert coordinator.data["n"]["devices"]["Yard"]["power"]
    assert coordinator.features.audit["n"]["result"] == "failed"
    services.cancel_shutdown_timer.assert_not_awaited()


async def test_firmware_entity_uses_server_stage_and_rejects_changed_offer(feature_hub):
    coordinator, _, services = feature_hub
    features = coordinator.features
    await features.command("n", "check_firmware")
    entity = ThermacellFirmwareUpdate(coordinator, "n", "Yard")
    assert entity.installed_version == "5.4.1"
    assert entity.latest_version == "6.0"
    assert await entity.async_release_notes() == "Fixes"
    assert not entity.in_progress and entity.available
    with pytest.raises(HomeAssistantError, match="version has changed"):
        await entity.async_install("5.5", False)
    await entity.async_install("6.0", False)
    services.install_firmware.assert_awaited_once()
    features.firmware["n"].status = "triggered"
    assert entity.in_progress
    assert entity.extra_state_attributes["stage"] == "triggered"
    with pytest.raises(HomeAssistantError, match="already in progress"):
        await entity.async_install(None, False)
    features.firmware_errors.add("n")
    assert not entity.available
    features.firmware["n"].available = False
    assert entity.latest_version == "5.4.1"


async def test_feature_entities_read_evidence_and_call_operations(feature_hub):
    coordinator, device, services = feature_hub
    features = coordinator.features
    features.observe(device)
    await features.refill_reset("n", 1)
    await features.record("n", "power", "failed", True)
    keys = {
        "installed_refill": "100 hours",
        "remaining_hours": 80,
        "last_command": "failed",
        "shutdown_at": None,
        "transport": "local",
    }
    for key, expected in keys.items():
        sensor = ThermacellFeatureSensor(coordinator, "n", "Yard", key)
        assert sensor.native_value == expected
        assert isinstance(sensor.extra_state_attributes, dict)
    reset = ThermacellFeatureSensor(coordinator, "n", "Yard", "last_refill_reset")
    assert reset.native_value.tzinfo is not None
    for key, expected in (
        ("missing_cartridge", False),
        ("low_refill", False),
        ("refill_drain", False),
        ("power_mismatch", True),
    ):
        flag = ThermacellDiagnosticFlag(coordinator, "n", "Yard", key)
        assert flag.is_on is expected
        assert isinstance(flag.extra_state_attributes, dict)
    device._state.params.refill_life = None
    device._state.params.cartridge_present = False
    assert ThermacellDiagnosticFlag(coordinator, "n", "Yard", "missing_cartridge").is_on
    assert ThermacellDiagnosticFlag(coordinator, "n", "Yard", "low_refill").is_on is None
    schedule = ThermacellScheduleSwitch(coordinator, "n", "Yard", "app")
    assert schedule.available and schedule.is_on
    assert schedule.name == "Schedule Evening"
    assert schedule.extra_state_attributes["actions"] == services.schedules[0].action
    await schedule.async_turn_off()
    await schedule.async_turn_on()
    services.schedules = []
    assert not schedule.available and schedule.is_on is None
    assert schedule.extra_state_attributes == {}
    zone = ThermacellTimezone(coordinator, "n", "Yard")
    assert zone.native_value == "America/New_York"
    await zone.async_set_value("UTC")
    assert len(native_buttons(services)) == 6
    services.supports.return_value = False
    assert native_buttons(services) == [("check_firmware", None)]
    button = ThermacellNativeButton(coordinator, "n", "Yard", "run_for", 30)
    await button.async_press()
    services.set_shutdown_timer.assert_awaited_with(1800)
    switch = ThermacellLivSwitch(coordinator, "n", "Yard")
    await switch.async_run_for(60)
    await switch.async_schedule_shutdown(datetime.now(UTC) + timedelta(hours=1))
    await switch.async_cancel_timer()


@pytest.mark.parametrize("platform", ["binary_sensor", "text", "update"])
async def test_dynamic_platform_discovery(feature_hub, platform):
    from importlib import import_module

    coordinator, device, services = feature_hub
    await coordinator.features.async_refresh()
    callback = None

    def subscribe(listener):
        nonlocal callback
        callback = listener
        return MagicMock()

    coordinator.async_add_listener = subscribe
    entry = MagicMock(runtime_data={"coordinator": coordinator})
    add = MagicMock()
    module = import_module(f"custom_components.thermacell_liv.{platform}")
    await module.async_setup_entry(MagicMock(), entry, add)
    count = len(add.call_args.args[0])
    callback()
    add.assert_called_once()
    coordinator.data["second"] = coordinator.data["n"]
    coordinator._devices["second"] = device
    coordinator.features.firmware["second"] = FirmwareUpdate()
    callback()
    assert add.call_count == 2
    assert len(add.call_args.args[0]) == count


async def test_cancelled_power_reverts_ui_and_records_uncertainty(feature_hub):
    coordinator, device, _ = feature_hub
    device.set_power.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await coordinator.async_set_device_power("n", "Yard", True)
    assert coordinator.data["n"]["devices"]["Yard"]["power"] is False
    assert coordinator.features.audit["n"]["result"] == "cancelled"
    with pytest.raises(asyncio.CancelledError):
        await coordinator.features.command("n", "run_for", 1800)
    assert coordinator.features.audit["n"]["result"] == "cancelled"


async def test_external_reset_invalidates_capacity_estimate(feature_hub):
    coordinator, device, _ = feature_hub
    features = coordinator.features
    await features.refill_reset("n", 2)
    features.history["n"]["reset_at"] = "2025-01-01T00:00:00+00:00"
    features.observe(device)
    device._state.params.refill_life = 100
    features.observe(device)
    assert features.remaining_hours("n", 100) is None
    await features.async_refresh()
    assert not features._history_dirty
