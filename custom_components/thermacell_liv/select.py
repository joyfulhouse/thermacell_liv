"""Select the cartridge type to use for the next refill reset."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, REFILL_TYPES
from .coordinator import ThermacellLivCoordinator
from .entity import ThermacellLivEntity, async_setup_platform_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a refill type selector for each hub."""
    await async_setup_platform_entities(config_entry, async_add_entities, ThermacellLivRefillTypeSelect)


class ThermacellLivRefillTypeSelect(ThermacellLivEntity, RestoreEntity, SelectEntity):
    """Remember a local cartridge preference without resetting the hub."""

    _attr_translation_key = "refill_type"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bottle-tonic"
    _attr_options = list(REFILL_TYPES)

    def __init__(self, coordinator: ThermacellLivCoordinator, node_id: str, device_name: str) -> None:
        """Initialize the selector."""
        super().__init__(coordinator, node_id, device_name)
        self._attr_unique_id = f"{DOMAIN}_{node_id}_refill_type"

    @property
    def current_option(self) -> str:
        """Return the preference used by the reset button."""
        refill_type = self.coordinator.refill_types.get(self._node_id, 1)
        return next(label for label, value in REFILL_TYPES.items() if value == refill_type)

    async def async_added_to_hass(self) -> None:
        """Restore the last selection across restarts."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) and state.state in REFILL_TYPES:
            self.coordinator.refill_types[self._node_id] = REFILL_TYPES[state.state]

    async def async_select_option(self, option: str) -> None:
        """Save the type for the next reset; no cloud command is sent here."""
        self.coordinator.refill_types[self._node_id] = REFILL_TYPES[option]
        self.async_write_ha_state()
