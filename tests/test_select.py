"""Cartridge selection persistence and reset behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.thermacell_liv.button import ThermacellLivResetButton
from custom_components.thermacell_liv.const import REFILL_TYPES
from custom_components.thermacell_liv.select import ThermacellLivRefillTypeSelect


@pytest.mark.parametrize(("label", "code"), REFILL_TYPES.items())
async def test_selection_only_affects_next_reset(label, code):
    coordinator = MagicMock()
    coordinator.refill_types = {}
    coordinator.async_reset_refill_life = AsyncMock(return_value=True)
    entity = ThermacellLivRefillTypeSelect(coordinator, "hub", "Garden")
    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option(label)
    assert entity.current_option == label
    coordinator.async_reset_refill_life.assert_not_awaited()
    await ThermacellLivResetButton(coordinator, "hub", "Garden").async_press()
    coordinator.async_reset_refill_life.assert_awaited_once_with("hub", "Garden", code)


async def test_restore_selection():
    coordinator = MagicMock()
    coordinator.refill_types = {}
    entity = ThermacellLivRefillTypeSelect(coordinator, "hub", "Garden")
    state = MagicMock(state="180 Hour - Gray Cap")
    with (
        patch("custom_components.thermacell_liv.entity.CoordinatorEntity.async_added_to_hass", new_callable=AsyncMock),
        patch.object(entity, "async_get_last_state", new_callable=AsyncMock, return_value=state),
    ):
        await entity.async_added_to_hass()
    assert coordinator.refill_types == {"hub": 2}
    assert entity.current_option == state.state
