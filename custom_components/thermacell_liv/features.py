"""Native controls and persisted maintenance/command diagnostics."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from pythermacell.services import TIMER_ID, TIMER_NAME, FirmwareUpdate

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from pythermacell import ThermacellDevice

    from .coordinator import ThermacellLivCoordinator

_LOGGER = logging.getLogger(__name__)
CAPACITIES = {0: 40, 1: 100, 2: 180}


@dataclass
class DrainObservation:
    """Require a continuous, confirmed off window before flagging consumption."""

    started: datetime
    last_seen: datetime
    baseline: float | None = None
    confirmations: int = 0


class HubFeatures:
    """Keep optional API failures separate from core hub polling."""

    def __init__(self, coordinator: ThermacellLivCoordinator) -> None:
        """Initialize per-entry state; no credentials are persisted here."""
        self.coordinator = coordinator
        self.history: dict[str, dict[str, Any]] = {}
        self.audit: dict[str, dict[str, Any]] = {}
        self.reported: dict[str, bool | None] = {}
        self.anomalies: dict[str, bool | None] = {}
        self.groups: dict[str, dict[str, Any]] = {}
        self.firmware: dict[str, FirmwareUpdate] = {}
        self.firmware_errors: set[str] = set()
        self.groups_available = False
        self._observations: dict[str, DrainObservation] = {}
        self._store: Store[dict[str, Any]] | None = None
        self._next_groups = dt_util.utcnow()
        self._next_firmware: dict[str, datetime] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_refill: dict[str, float] = {}
        self._history_dirty = False

    async def async_load(self, entry_id: str) -> None:
        """Restore only successfully applied maintenance metadata."""
        self._store = Store(self.coordinator.hass, 1, f"{DOMAIN}.{entry_id}.history")
        data = await self._store.async_load()
        if isinstance(data, dict):
            self.history = data.get("history", {})
            self.audit = data.get("audit", {})
            for node_id, item in self.history.items():
                if isinstance(item.get("firmware"), dict):
                    self.firmware[node_id] = FirmwareUpdate(**item["firmware"])

    async def async_save(self) -> None:
        """Save accepted changes immediately so restart does not lose them."""
        if self._store:
            await self._store.async_save({"history": self.history, "audit": self.audit})

    def device(self, node_id: str) -> ThermacellDevice:
        """Resolve a current device or fail explicitly."""
        device = self.coordinator.get_device(node_id)
        if device is None:
            raise HomeAssistantError("Thermacell hub is no longer available")
        return device

    def observe(self, device: ThermacellDevice) -> None:
        """Use polled data only, never optimistic state, for shutdown diagnostics."""
        node_id = device.node_id
        code = device.system_status
        self.reported[node_id] = code != 1 if code in (1, 2, 3) and device.is_online else None
        refill = device.refill_life
        now = dt_util.utcnow()
        metadata = self.history.get(node_id, {})
        previous_refill = self._last_refill.get(node_id)
        reset_at = dt_util.parse_datetime(metadata.get("reset_at", ""))
        recent_reset = reset_at is not None and now - reset_at < timedelta(minutes=10)
        if (
            device.is_online
            and "applied_type" in metadata
            and (
                device.cartridge_present is False
                or (
                    refill is not None
                    and previous_refill is not None
                    and refill > previous_refill + 5
                    and not recent_reset
                )
            )
        ):
            # An app reset/replacement cannot tell us which cartridge was used.
            metadata.pop("applied_type")
            self._history_dirty = True
        if refill is not None:
            self._last_refill[node_id] = refill
        if not device.is_online or refill is None or code not in (1, 2, 3):
            self._observations.pop(node_id, None)
            self.anomalies[node_id] = None
            return
        if code != 1 or device.power is not False:
            self._observations.pop(node_id, None)
            self.anomalies[node_id] = False
            return
        observation = self._observations.get(node_id)
        interval = self.coordinator.update_interval or timedelta(seconds=60)
        if observation is None or now - observation.last_seen > interval * 3:
            self._observations[node_id] = DrainObservation(now, now)
            self.anomalies[node_id] = False
            return
        observation.last_seen = now
        elapsed = (now - observation.started).total_seconds()
        if elapsed < 120:
            return
        if observation.baseline is None or refill > observation.baseline:
            observation.baseline = refill
            observation.confirmations = 0
            self.anomalies[node_id] = False
        elif observation.baseline - refill >= 2:
            observation.confirmations += 1
            self.anomalies[node_id] = elapsed >= 600 and observation.confirmations >= 2

    async def record(self, node_id: str, command: str, result: str, requested: bool | None = None) -> None:
        """Persist command outcome separately from the hub's reported state."""
        previous = self.audit.get(node_id, {})
        self.audit[node_id] = {
            "command": command,
            "result": result,
            "time": dt_util.utcnow().isoformat(),
            "requested_power": requested if requested is not None else previous.get("requested_power"),
        }
        await self.async_save()
        self.coordinator.async_update_listeners()

    async def refill_reset(self, node_id: str, refill_type: int) -> None:
        """Record the applied cartridge, independent of the next-reset selector."""
        self.history.setdefault(node_id, {}).update(
            {
                "reset_at": dt_util.utcnow().isoformat(),
                "applied_type": refill_type,
            }
        )
        self._observations.pop(node_id, None)
        self.anomalies[node_id] = False
        await self.record(node_id, "reset_refill", "accepted")

    def remaining_hours(self, node_id: str, refill: float | None) -> float | None:
        """Estimate operating hours only after a known successful reset."""
        capacity = CAPACITIES.get(self.history.get(node_id, {}).get("applied_type", -1))
        return round(refill * capacity / 100, 1) if capacity is not None and refill is not None else None

    async def async_refresh(self) -> None:
        """Poll groups every 15 minutes, firmware offers every six hours."""
        now = dt_util.utcnow()
        if self._history_dirty:
            await self.async_save()
            self._history_dirty = False
        if now >= self._next_groups:
            self._next_groups = now + timedelta(minutes=15)
            try:
                groups = await self.coordinator.client.get_groups(strict=True)
                memberships = await asyncio.gather(
                    *(self.coordinator.client.get_group_nodes(g.group_id, strict=True) for g in groups)
                )
                self.groups = {
                    group.group_id: {"name": group.group_name, "nodes": nodes}
                    for group, nodes in zip(groups, memberships, strict=True)
                }
                self.groups_available = True
            except Exception as err:
                self.groups_available = False
                _LOGGER.debug("Group discovery unavailable: %s", type(err).__name__)
        await asyncio.gather(*(self._refresh_firmware(node_id, now) for node_id in self.coordinator.nodes))

    async def _refresh_firmware(self, node_id: str, now: datetime) -> None:
        update = self.firmware.get(node_id)
        if not (update and update.in_progress) and now < self._next_firmware.get(node_id, now):
            return
        self._next_firmware[node_id] = now + timedelta(hours=6)
        try:
            services = self.device(node_id).services
            if update and update.in_progress:
                await services.refresh_firmware_status(update)
                self.history.setdefault(node_id, {})["firmware"] = asdict(update)
                await self.async_save()
            else:
                self.firmware[node_id] = await services.check_firmware()
            self.firmware_errors.discard(node_id)
        except Exception as err:
            self.firmware_errors.add(node_id)
            self._next_firmware[node_id] = now + timedelta(minutes=15)
            _LOGGER.debug("Firmware check unavailable for %s: %s", node_id, type(err).__name__)

    async def command(self, node_id: str, command: str, value: Any = None) -> None:
        """Run a native operation, audit errors, and refresh reported state."""
        async with self._locks.setdefault(node_id, asyncio.Lock()):
            try:
                await self._execute(node_id, command, value)
            except asyncio.CancelledError:
                await self.record(node_id, command, "cancelled")
                raise
            except Exception as err:
                await self.record(node_id, command, "failed")
                raise HomeAssistantError(f"Thermacell {command} failed: {err}") from err
            await self.record(node_id, command, "accepted")
        await self.coordinator.async_request_refresh()

    async def _execute(self, node_id: str, command: str, value: Any) -> None:
        device = self.device(node_id)
        services = device.services
        if command in ("run_for", "schedule_shutdown"):
            seconds = int(value)
            await services.set_shutdown_timer(seconds)
            self.history.setdefault(node_id, {})["shutdown_at"] = (
                dt_util.utcnow() + timedelta(seconds=seconds)
            ).isoformat()
            await self.async_save()
            if command == "run_for" and not await self.coordinator.async_set_device_power(node_id, device.name, True):
                raise HomeAssistantError("Timer installed but hub did not confirm power on")
        elif command == "cancel_timer":
            if not await device.refresh(skip_config=True):
                raise HomeAssistantError("Cannot refresh timer state")
            await services.cancel_shutdown_timer()
            self.history.setdefault(node_id, {}).pop("shutdown_at", None)
        elif command == "reboot":
            await services.reboot()
        elif command == "timezone":
            await services.set_timezone(value)
        elif command == "schedule":
            await services.set_schedule_enabled(value[0], value[1])
        elif command == "check_firmware":
            self.firmware[node_id] = await services.check_firmware()
            self.firmware_errors.discard(node_id)
        elif command == "install_firmware":
            if (current := self.firmware.get(node_id)) and current.in_progress:
                raise HomeAssistantError("Firmware installation is already in progress")
            update = await services.check_firmware()
            if value is not None and value != update.version:
                raise HomeAssistantError("The offered firmware version has changed; check for updates again")
            await services.install_firmware(update)
            self.firmware[node_id] = update
            self.history.setdefault(node_id, {})["firmware"] = asdict(update)
        else:
            raise HomeAssistantError("Unknown Thermacell command")

    def shutdown_at(self, node_id: str) -> datetime | None:
        """Expose a remembered deadline only while the native timer is enabled."""
        device = self.coordinator.get_device(node_id)
        if device and any(s.id == TIMER_ID and s.name == TIMER_NAME and s.enabled for s in device.services.schedules):
            value = self.history.get(node_id, {}).get("shutdown_at")
            return dt_util.parse_datetime(value) if value else None
        return None

    async def group_power(self, group_id: str, power: bool) -> None:
        """Coordinate members and report partial failures without rollback."""
        if not self.groups_available or group_id not in self.groups:
            raise HomeAssistantError("Thermacell group membership is unavailable")
        nodes = self.groups[group_id]["nodes"]
        if not nodes:
            raise HomeAssistantError("Thermacell group is empty")

        async def control(node_id: str) -> bool:
            device = self.coordinator.get_device(node_id)
            if not device or not device.is_online:
                return False
            return await self.coordinator.async_set_device_power(node_id, device.name, power)

        results = await asyncio.gather(*(control(node_id) for node_id in nodes), return_exceptions=True)
        failed = [node for node, result in zip(nodes, results, strict=True) if result is not True]
        await self.coordinator.async_request_refresh()
        if failed:
            raise HomeAssistantError(f"Thermacell group command failed for: {', '.join(failed)}")
