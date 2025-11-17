#!/usr/bin/env python3
"""Unit tests for repairs module."""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.thermacell_liv.repairs import async_create_fix_flow


class TestRepairs:
    """Test repairs functionality."""

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_auth_failed(self):
        """Test creating fix flow for auth_failed issue."""
        # Mock hass
        hass = MagicMock()

        # Create fix flow for auth_failed
        flow = await async_create_fix_flow(hass, "auth_failed", None)

        # Verify flow is created and is a ConfirmRepairFlow
        assert flow is not None
        assert hasattr(flow, "async_step_init") or hasattr(flow, "async_step_confirm")

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_device_offline(self):
        """Test creating fix flow for device_offline issue."""
        # Mock hass
        hass = MagicMock()

        # Create fix flow for device_offline
        flow = await async_create_fix_flow(hass, "device_offline", None)

        # Verify flow is created and is a ConfirmRepairFlow
        assert flow is not None
        assert hasattr(flow, "async_step_init") or hasattr(flow, "async_step_confirm")

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_with_data(self):
        """Test creating fix flow with additional data."""
        # Mock hass
        hass = MagicMock()

        # Create fix flow with data
        data = {"node_id": "node123", "error_code": 5}
        flow = await async_create_fix_flow(hass, "auth_failed", data)

        # Verify flow is created regardless of data
        assert flow is not None

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_unknown_issue(self):
        """Test creating fix flow for unknown issue type."""
        # Mock hass
        hass = MagicMock()

        # Create fix flow for unknown issue
        flow = await async_create_fix_flow(hass, "unknown_issue", None)

        # Verify flow is created (function doesn't discriminate)
        assert flow is not None

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_empty_issue_id(self):
        """Test creating fix flow with empty issue ID."""
        # Mock hass
        hass = MagicMock()

        # Create fix flow with empty issue ID
        flow = await async_create_fix_flow(hass, "", None)

        # Verify flow is created
        assert flow is not None


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio

    test = TestRepairs()

    print("🧪 Running Repairs Tests")
    print("=" * 50)

    async def run_async_tests():
        """Run all async tests."""
        try:
            await test.test_async_create_fix_flow_auth_failed()
            print("✅ Auth failed repair flow test passed")
        except Exception as e:
            print(f"❌ Auth failed repair flow test failed: {e}")

        try:
            await test.test_async_create_fix_flow_device_offline()
            print("✅ Device offline repair flow test passed")
        except Exception as e:
            print(f"❌ Device offline repair flow test failed: {e}")

        try:
            await test.test_async_create_fix_flow_with_data()
            print("✅ Repair flow with data test passed")
        except Exception as e:
            print(f"❌ Repair flow with data test failed: {e}")

        try:
            await test.test_async_create_fix_flow_unknown_issue()
            print("✅ Unknown issue repair flow test passed")
        except Exception as e:
            print(f"❌ Unknown issue repair flow test failed: {e}")

        try:
            await test.test_async_create_fix_flow_empty_issue_id()
            print("✅ Empty issue ID repair flow test passed")
        except Exception as e:
            print(f"❌ Empty issue ID repair flow test failed: {e}")

    asyncio.run(run_async_tests())

    print("\n🎉 Repairs tests completed!")
