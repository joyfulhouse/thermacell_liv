"""Platform for switch integration."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any

from pythermacell.services import Schedule
import voluptuous as vol

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, service
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities, setup_dynamic_entities

# Limit parallel updates to avoid overwhelming the API
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    await async_setup_platform_entities(config_entry, async_add_entities, ThermacellLivSwitch)
    actions: tuple[tuple[str, dict[str | vol.Marker, Any], str], ...] = (
        ("run_for", {vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440))}, "async_run_for"),
        ("schedule_shutdown", {vol.Required("at"): cv.datetime}, "async_schedule_shutdown"),
        ("cancel_timer", {}, "async_cancel_timer"),
    )
    for name, schema, method in actions:
        service.async_register_platform_entity_service(
            _hass,
            DOMAIN,
            name,
            entity_domain="switch",
            entity_device_classes=[SwitchDeviceClass.SWITCH],
            schema=cv.make_entity_service_schema(schema),
            func=method,
        )
    coordinator = config_entry.runtime_data["coordinator"]
    setup_dynamic_entities(
        config_entry,
        async_add_entities,
        lambda: [
            ThermacellScheduleSwitch(coordinator, node_id, device.name, schedule.id)
            for node_id in coordinator.data
            if (device := coordinator.get_device(node_id))
            for schedule in device.services.schedules
        ],
    )
    setup_dynamic_entities(
        config_entry,
        async_add_entities,
        lambda: [
            ThermacellGroupSwitch(coordinator, config_entry.entry_id, group_id)
            for group_id in coordinator.features.groups
        ],
    )


class ThermacellScheduleSwitch(ThermacellLivEntity, SwitchEntity):
    """Toggle one native schedule, preserving its triggers and actions."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, name: str, schedule_id: str) -> None:
        super().__init__(coordinator, node_id, name)
        self.schedule_id = schedule_id
        self._attr_unique_id = f"{DOMAIN}_{node_id}_schedule_{schedule_id}"

    @property
    def schedule(self) -> Schedule | None:
        device = self.coordinator.get_device(self._node_id)
        return next((s for s in device.services.schedules if s.id == self.schedule_id), None) if device else None

    @property
    def available(self) -> bool:
        return super().available and self.schedule is not None

    @property
    def name(self) -> str:
        schedule = self.schedule
        return f"Schedule {schedule.name if schedule else self.schedule_id}"

    @property
    def is_on(self) -> bool | None:
        schedule = self.schedule
        return schedule.enabled if schedule else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        schedule = self.schedule
        return (
            {"schedule_id": schedule.id, "triggers": schedule.triggers, "actions": schedule.action} if schedule else {}
        )

    async def async_turn_on(self, **_kwargs: Any) -> None:
        await self.coordinator.features.command(self._node_id, "schedule", (self.schedule_id, True))

    async def async_turn_off(self, **_kwargs: Any) -> None:
        await self.coordinator.features.command(self._node_id, "schedule", (self.schedule_id, False))


class ThermacellGroupSwitch(CoordinatorEntity[ThermacellLivCoordinator], SwitchEntity):
    """An account group with verified, concurrent member controls."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ThermacellLivCoordinator, entry_id: str, group_id: str) -> None:
        super().__init__(coordinator)
        self.group_id = group_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_group_{group_id}"

    @property
    def name(self) -> str:
        return f"Thermacell group {self.coordinator.features.groups.get(self.group_id, {}).get('name', self.group_id)}"

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self.coordinator.features.groups_available
            and self.group_id in self.coordinator.features.groups
        )

    @property
    def is_on(self) -> bool | None:
        values = [
            self.coordinator.features.reported.get(node)
            for node in self.coordinator.features.groups.get(self.group_id, {}).get("nodes", [])
        ]
        return True if True in values else False if values and all(v is False for v in values) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"node_ids": self.coordinator.features.groups.get(self.group_id, {}).get("nodes", [])}

    async def async_turn_on(self, **_kwargs: Any) -> None:
        await self.coordinator.features.group_power(self.group_id, True)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        await self.coordinator.features.group_power(self.group_id, False)


class ThermacellLivSwitch(ThermacellLivEntity, SwitchEntity):
    """Representation of a Thermacell LIV switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    async def async_run_for(self, minutes: int) -> None:
        """Start the hub after programming a native shutdown timer."""
        await self.coordinator.features.command(self._node_id, "run_for", minutes * 60)

    async def async_schedule_shutdown(self, at: datetime) -> None:
        """Convert the selected shutdown instant to a hub-native countdown."""
        seconds = math.ceil((dt_util.as_utc(at) - dt_util.utcnow()).total_seconds())
        await self.coordinator.features.command(self._node_id, "schedule_shutdown", seconds)

    async def async_cancel_timer(self) -> None:
        """Cancel the integration's timer without changing power."""
        await self.coordinator.features.command(self._node_id, "cancel_timer")

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_name = None  # Main entity uses device name only
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_switch"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        device_data = self.coordinator.get_device_data(self._node_id, self._device_name)
        return device_data.get("power", False) if device_data else False

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn the switch on."""
        if not await self.coordinator.async_set_device_power(self._node_id, self._device_name, True):
            raise HomeAssistantError("Failed to change Thermacell power; check the hub state")

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn the switch off."""
        if not await self.coordinator.async_set_device_power(self._node_id, self._device_name, False):
            raise HomeAssistantError("Failed to change Thermacell power; check the hub state")
