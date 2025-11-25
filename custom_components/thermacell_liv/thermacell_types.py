"""Type definitions for Thermacell LIV integration.

This module provides TypedDict definitions for structured data used throughout
the integration, ensuring type safety and enabling strict mypy validation.

Platinum tier requirement: strict-typing
This file provides comprehensive type definitions for all structured data
used in the integration, enabling full mypy strict mode compliance.
"""

from __future__ import annotations

from typing import TypedDict


class RGBColor(TypedDict):
    """RGB color values (0-255 range)."""

    r: int
    g: int
    b: int


class DeviceParams(TypedDict, total=False):
    """Device parameters from API and coordinator processing.

    These are the processed device parameters stored in coordinator.data
    after transformation from raw API responses.
    """

    power: bool
    led_power: bool
    led_brightness: int
    led_brightness_pct: int
    led_color: RGBColor
    refill_life: int
    system_status: str
    system_status_code: int
    error_code: int
    last_updated: int


class NodeData(TypedDict, total=False):
    """Node (hub) data structure stored in coordinator.data.

    This is the processed node data structure that coordinator maintains
    for each Thermacell LIV hub device.
    """

    id: str
    name: str
    type: str
    fw_version: str
    model: str
    hub_serial: str | None
    system_runtime: int | None
    online: bool
    devices: dict[str, DeviceParams]
