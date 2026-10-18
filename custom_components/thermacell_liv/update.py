"""Cloud firmware offers and installation stages."""

from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateDeviceClass, UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, setup_dynamic_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(_hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Discover updates only after a successful API capability check."""
    coordinator = entry.runtime_data["coordinator"]
    setup_dynamic_entities(
        entry,
        async_add_entities,
        lambda: [
            ThermacellFirmwareUpdate(coordinator, node_id, device.name)
            for node_id in coordinator.features.firmware
            if (device := coordinator.get_device(node_id))
        ],
    )


class ThermacellFirmwareUpdate(ThermacellLivEntity, UpdateEntity):
    """Install the offered node-specific OTA job, with server-reported stages."""

    _attr_translation_key = "firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, name: str) -> None:
        super().__init__(coordinator, node_id, name)
        self._attr_unique_id = f"{DOMAIN}_{node_id}_firmware_update"

    @property
    def available(self) -> bool:
        return super().available and self._node_id not in self.coordinator.features.firmware_errors

    @property
    def installed_version(self) -> str | None:
        device = self.coordinator.get_device(self._node_id)
        return device.firmware_version if device else None

    @property
    def latest_version(self) -> str | None:
        update = self.coordinator.features.firmware.get(self._node_id)
        return update.version if update and update.available else self.installed_version

    @property
    def in_progress(self) -> bool:
        update = self.coordinator.features.firmware.get(self._node_id)
        return bool(update and update.in_progress)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        update = self.coordinator.features.firmware.get(self._node_id)
        return {"stage": update.status, "details": update.additional_info} if update else {}

    async def async_release_notes(self) -> str | None:
        update = self.coordinator.features.firmware.get(self._node_id)
        return update.description if update else None

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        await self.coordinator.features.command(self._node_id, "install_firmware", version)
