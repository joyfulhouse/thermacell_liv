#!/usr/bin/env python3
"""Unit tests for diagnostics module."""

from datetime import datetime, timedelta
import os
import sys
from unittest.mock import MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from diagnostics import TO_REDACT, async_get_config_entry_diagnostics


class TestDiagnostics:
    """Test diagnostics functionality."""

    @pytest.mark.asyncio
    async def test_async_get_config_entry_diagnostics_basic(self):
        """Test basic diagnostics output."""
        # Create mock config entry
        entry = MagicMock()
        entry.title = "Test Hub"
        entry.domain = DOMAIN
        entry.version = 1
        entry.unique_id = "test_unique_id"

        # Create mock coordinator with minimal data
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.last_update_success_time = datetime.now()
        coordinator.update_interval = timedelta(seconds=60)
        coordinator.data = {}

        entry.runtime_data = coordinator

        # Mock hass
        hass = MagicMock()

        # Get diagnostics
        result = await async_get_config_entry_diagnostics(hass, entry)

        # Verify basic structure
        assert "entry" in result
        assert "coordinator" in result
        assert "nodes" in result

        # Verify entry data
        assert result["entry"]["title"] == "Test Hub"
        assert result["entry"]["domain"] == DOMAIN
        assert result["entry"]["version"] == 1
        assert result["entry"]["unique_id"] == "test_unique_id"

        # Verify coordinator data
        assert result["coordinator"]["last_update_success"] is True
        assert result["coordinator"]["last_update_success_time"] is not None
        assert "60" in result["coordinator"]["update_interval"]
        assert result["coordinator"]["node_count"] == 0

    @pytest.mark.asyncio
    async def test_async_get_config_entry_diagnostics_with_nodes(self):
        """Test diagnostics with node data."""
        # Create mock config entry
        entry = MagicMock()
        entry.title = "Test Hub"
        entry.domain = DOMAIN
        entry.version = 1
        entry.unique_id = "test_unique_id"

        # Create mock coordinator with node data
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.last_update_success_time = datetime.now()
        coordinator.update_interval = timedelta(seconds=60)
        coordinator.data = {
            "node1": {
                "name": "Living Room",
                "type": "thermacell-hub",
                "model": "Thermacell LIV Hub",
                "fw_version": "5.3.2",
                "online": True,
                "system_runtime": 120,
                "devices": {
                    "LIV Hub": {
                        "power": True,
                        "led_power": True,
                        "led_brightness": 128,
                        "led_brightness_pct": 50,
                        "led_color": {"r": 255, "g": 128, "b": 0},
                        "refill_life": 75,
                        "system_status": "Protected",
                        "system_status_code": 3,
                        "error_code": 0,
                        "last_updated": 1234567890,
                    }
                },
            }
        }

        entry.runtime_data = coordinator

        # Mock hass
        hass = MagicMock()

        # Get diagnostics
        result = await async_get_config_entry_diagnostics(hass, entry)

        # Verify node count
        assert result["coordinator"]["node_count"] == 1

        # Verify node data
        assert "node1" in result["nodes"]
        node = result["nodes"]["node1"]
        assert node["name"] == "Living Room"
        assert node["type"] == "thermacell-hub"
        assert node["model"] == "Thermacell LIV Hub"
        assert node["fw_version"] == "5.3.2"
        assert node["online"] is True
        assert node["system_runtime"] == 120

        # Verify device data
        assert "LIV Hub" in node["devices"]
        device = node["devices"]["LIV Hub"]
        assert device["power"] is True
        assert device["led_power"] is True
        assert device["led_brightness"] == 128
        assert device["led_brightness_pct"] == 50
        assert device["led_color"] == {"r": 255, "g": 128, "b": 0}
        assert device["refill_life"] == 75
        assert device["system_status"] == "Protected"
        assert device["system_status_code"] == 3
        assert device["error_code"] == 0
        assert device["last_updated"] == 1234567890

    @pytest.mark.asyncio
    async def test_async_get_config_entry_diagnostics_multiple_nodes(self):
        """Test diagnostics with multiple nodes."""
        # Create mock config entry
        entry = MagicMock()
        entry.title = "Test Hub"
        entry.domain = DOMAIN
        entry.version = 1
        entry.unique_id = "test_unique_id"

        # Create mock coordinator with multiple nodes
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.last_update_success_time = datetime.now()
        coordinator.update_interval = timedelta(seconds=60)
        coordinator.data = {
            "node1": {
                "name": "Living Room",
                "model": "Thermacell LIV Hub",
                "fw_version": "5.3.2",
                "online": True,
                "devices": {"LIV Hub": {"power": True}},
            },
            "node2": {
                "name": "Bedroom",
                "model": "Thermacell LIV Hub",
                "fw_version": "5.3.2",
                "online": False,
                "devices": {"LIV Hub": {"power": False}},
            },
        }

        entry.runtime_data = coordinator

        # Mock hass
        hass = MagicMock()

        # Get diagnostics
        result = await async_get_config_entry_diagnostics(hass, entry)

        # Verify multiple nodes
        assert result["coordinator"]["node_count"] == 2
        assert "node1" in result["nodes"]
        assert "node2" in result["nodes"]
        assert result["nodes"]["node1"]["name"] == "Living Room"
        assert result["nodes"]["node2"]["name"] == "Bedroom"

    @pytest.mark.asyncio
    async def test_async_get_config_entry_diagnostics_no_update_time(self):
        """Test diagnostics when last_update_success_time is None."""
        # Create mock config entry
        entry = MagicMock()
        entry.title = "Test Hub"
        entry.domain = DOMAIN
        entry.version = 1
        entry.unique_id = "test_unique_id"

        # Create mock coordinator with no update time
        coordinator = MagicMock()
        coordinator.last_update_success = False
        coordinator.last_update_success_time = None
        coordinator.update_interval = timedelta(seconds=60)
        coordinator.data = None

        entry.runtime_data = coordinator

        # Mock hass
        hass = MagicMock()

        # Get diagnostics
        result = await async_get_config_entry_diagnostics(hass, entry)

        # Verify None is handled
        assert result["coordinator"]["last_update_success_time"] is None
        assert result["coordinator"]["node_count"] == 0

    def test_to_redact_contains_sensitive_keys(self):
        """Test that TO_REDACT contains expected sensitive keys."""
        assert CONF_USERNAME in TO_REDACT
        assert CONF_PASSWORD in TO_REDACT
        assert "user_id" in TO_REDACT
        assert "access_token" in TO_REDACT
        assert "idtoken" in TO_REDACT
        assert "refreshtoken" in TO_REDACT
        assert "hub_serial" in TO_REDACT
        assert "Hub ID" in TO_REDACT


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio

    test = TestDiagnostics()

    print("🧪 Running Diagnostics Tests")
    print("=" * 50)

    async def run_async_tests():
        """Run all async tests."""
        try:
            await test.test_async_get_config_entry_diagnostics_basic()
            print("✅ Basic diagnostics test passed")
        except Exception as e:
            print(f"❌ Basic diagnostics test failed: {e}")

        try:
            await test.test_async_get_config_entry_diagnostics_with_nodes()
            print("✅ Diagnostics with nodes test passed")
        except Exception as e:
            print(f"❌ Diagnostics with nodes test failed: {e}")

        try:
            await test.test_async_get_config_entry_diagnostics_multiple_nodes()
            print("✅ Multiple nodes test passed")
        except Exception as e:
            print(f"❌ Multiple nodes test failed: {e}")

        try:
            await test.test_async_get_config_entry_diagnostics_no_update_time()
            print("✅ No update time test passed")
        except Exception as e:
            print(f"❌ No update time test failed: {e}")

    asyncio.run(run_async_tests())

    try:
        test.test_to_redact_contains_sensitive_keys()
        print("✅ TO_REDACT keys test passed")
    except Exception as e:
        print(f"❌ TO_REDACT keys test failed: {e}")

    print("\n🎉 Diagnostics tests completed!")
