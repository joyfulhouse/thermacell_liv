"""Platform for button integration."""

from __future__ import annotations

import logging

from pythermacell.services import HubServices

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities, setup_dynamic_entities

_LOGGER = logging.getLogger(__name__)


# Limit parallel button presses to avoid API conflicts
PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    await async_setup_platform_entities(
        config_entry, async_add_entities, ThermacellLivResetButton, ThermacellLivRefreshButton
    )
    coordinator = config_entry.runtime_data["coordinator"]
    setup_dynamic_entities(
        config_entry,
        async_add_entities,
        lambda: [
            ThermacellNativeButton(coordinator, node_id, device.name, command, minutes)
            for node_id in coordinator.data
            if (device := coordinator.get_device(node_id))
            for command, minutes in native_buttons(device.services)
        ],
    )


def native_buttons(services: HubServices) -> list[tuple[str, int | None]]:
    """List controls supported by the advertised hub services."""
    buttons: list[tuple[str, int | None]] = [("check_firmware", None)]
    if services.supports("esp.service.schedule", "esp.param.schedules") is True:
        buttons.extend(("run_for", minutes) for minutes in (30, 60, 120))
        buttons.append(("cancel_timer", None))
    if services.supports("esp.service.system", "esp.param.reboot") is True:
        buttons.append(("reboot", None))
    return buttons


class ThermacellNativeButton(ThermacellLivEntity, ButtonEntity):
    """A capability-gated native operation."""

    def __init__(
        self, coordinator: ThermacellLivCoordinator, node_id: str, name: str, command: str, minutes: int | None
    ) -> None:
        super().__init__(coordinator, node_id, name)
        self.command = command
        self.minutes = minutes
        key = f"run_{minutes}" if minutes else command
        self._attr_translation_key = key
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{key}"
        if command in ("reboot", "check_firmware"):
            self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Send the operation through the audited coordinator path."""
        await self.coordinator.features.command(
            self._node_id, self.command, self.minutes * 60 if self.minutes else None
        )


class ThermacellLivResetButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refill reset button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_translation_key = "reset_refill"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_reset_refill"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.async_reset_refill_life(
            self._node_id, self._device_name, self.coordinator.refill_types.get(self._node_id, 1)
        )
        if not success:
            raise HomeAssistantError("Failed to reset Thermacell refill life")


class ThermacellLivRefreshButton(ThermacellLivEntity, ButtonEntity):
    """Representation of a Thermacell LIV refresh button."""

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, node_id, device_name)

        self._attr_translation_key = "refresh"
        self._attr_unique_id = f"{DOMAIN}_{node_id}_{device_name}_refresh"
        self._attr_icon = "mdi:refresh"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Refresh requested for %s %s", self._node_id, self._device_name)
        await self.coordinator.async_request_refresh()
