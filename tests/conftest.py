"""Pytest configuration for Thermacell LIV tests."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path to enable custom_components imports
# This allows tests to import custom_components.thermacell_liv
project_root = os.path.join(os.path.dirname(__file__), "..")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Patch frame helper functions at module level before any imports
# This prevents RuntimeError when frame helper tries to check _hass.hass
patch("homeassistant.helpers.frame.report_usage", return_value=None).start()
patch("homeassistant.helpers.frame.warn_use", return_value=None).start()
patch("homeassistant.helpers.frame.report_non_thread_safe_operation", return_value=None).start()


@pytest.fixture(autouse=True)
def disable_frame_helper():
    """Ensure frame helper patches are active for all tests."""
    # Patches are already applied at module level, just yield
    yield
