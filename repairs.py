"""Repairs platform for Thermacell LIV integration."""

from __future__ import annotations

import logging

from homeassistant.components.repairs import ConfirmRepairFlow
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    _hass: HomeAssistant,
    _issue_id: str,
    _data: dict[str, str | int | float | None] | None,
) -> ConfirmRepairFlow:
    """Create flow to fix an issue."""
    # For both auth_failed and device_offline, we just need to show
    # the informational message and let users acknowledge it
    return ConfirmRepairFlow()
