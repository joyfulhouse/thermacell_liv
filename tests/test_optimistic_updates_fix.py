#!/usr/bin/env python3
"""
Test optimistic updates fix for multi-device data corruption issue.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import ThermacellLivCoordinator

class TestOptimisticUpdatesFix:
    """Test that optimistic updates work correctly with multi-device data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock Home Assistant
        self.hass = MagicMock()
        
        # Mock API
        self.api = MagicMock()
        
        # Create coordinator with mocked dependencies
        self.coordinator = ThermacellLivCoordinator.__new__(ThermacellLivCoordinator)
        self.coordinator.hass = self.hass
        self.coordinator.api = self.api
        self.coordinator.last_update_success = True
        self.coordinator.async_update_listeners = MagicMock()
        
        # Set up multi-device data
        self.coordinator.data = {
            "device1": {
                "name": "Hub 1",
                "online": True,
                "devices": {
                    "LIV Hub": {
                        "power": False,
                        "led_power": False,
                        "led_brightness": 128,
                        "led_brightness_pct": 50,
                        "led_color": {"r": 255, "g": 255, "b": 0},
                        "system_status": "Off",
                        "refill_life": 75
                    }
                }
            },
            "device2": {
                "name": "Hub 2", 
                "online": True,
                "devices": {
                    "LIV Hub": {
                        "power": True,
                        "led_power": True,
                        "led_brightness": 200,
                        "led_brightness_pct": 78,
                        "led_color": {"r": 0, "g": 255, "b": 255},
                        "system_status": "Protected",
                        "refill_life": 90
                    }
                }
            }
        }
        
    @pytest.mark.asyncio
    async def test_power_optimistic_update_isolation(self):
        """Test that power updates don't affect other devices."""
        # Mock successful API call
        self.api.set_device_power = AsyncMock(return_value=True)
        
        # Update power for device1 only
        result = await self.coordinator.async_set_device_power("device1", "LIV Hub", True)
        
        assert result == True
        
        # Verify device1 was updated
        device1_data = self.coordinator.data["device1"]["devices"]["LIV Hub"]
        assert device1_data["power"] == True
        assert device1_data["led_power"] == True  # Should be True because brightness > 0
        
        # Verify device2 was NOT affected
        device2_data = self.coordinator.data["device2"]["devices"]["LIV Hub"]
        assert device2_data["power"] == True  # Original state unchanged
        assert device2_data["led_power"] == True  # Original state unchanged
        assert device2_data["led_brightness"] == 200  # Original state unchanged
        
        # Verify UI update was called
        self.coordinator.async_update_listeners.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_led_brightness_optimistic_update_isolation(self):
        """Test that LED brightness updates don't affect other devices."""
        # Mock successful API call
        self.api.set_device_led_brightness = AsyncMock(return_value=True)
        
        # Update brightness for device2 only
        result = await self.coordinator.async_set_device_led_brightness("device2", "LIV Hub", 100)
        
        assert result == True
        
        # Verify device2 was updated
        device2_data = self.coordinator.data["device2"]["devices"]["LIV Hub"]
        assert device2_data["led_brightness"] == 100
        assert device2_data["led_brightness_pct"] == int((100 / 255) * 100)  # ~39%
        
        # Verify device1 was NOT affected
        device1_data = self.coordinator.data["device1"]["devices"]["LIV Hub"]
        assert device1_data["led_brightness"] == 128  # Original state unchanged
        assert device1_data["led_brightness_pct"] == 50  # Original state unchanged
        assert device1_data["power"] == False  # Original state unchanged
        
    @pytest.mark.asyncio
    async def test_led_color_optimistic_update_isolation(self):
        """Test that LED color updates don't affect other devices."""
        # Mock successful API call
        self.api.set_device_led_color = AsyncMock(return_value=True)
        
        # Update color for device1 only
        result = await self.coordinator.async_set_device_led_color("device1", "LIV Hub", 255, 0, 0)
        
        assert result == True
        
        # Verify device1 was updated
        device1_data = self.coordinator.data["device1"]["devices"]["LIV Hub"]
        assert device1_data["led_color"] == {"r": 255, "g": 0, "b": 0}
        
        # Verify device2 was NOT affected
        device2_data = self.coordinator.data["device2"]["devices"]["LIV Hub"]
        assert device2_data["led_color"] == {"r": 0, "g": 255, "b": 255}  # Original state unchanged
        
    @pytest.mark.asyncio
    async def test_failed_api_call_revert_isolation(self):
        """Test that failed API calls revert only the affected device."""
        # Mock failed API call
        self.api.set_device_power = AsyncMock(return_value=False)
        
        # Store original states
        original_device1_power = self.coordinator.data["device1"]["devices"]["LIV Hub"]["power"]
        original_device2_power = self.coordinator.data["device2"]["devices"]["LIV Hub"]["power"]
        
        # Attempt to update power for device1 (will fail)
        result = await self.coordinator.async_set_device_power("device1", "LIV Hub", True)
        
        assert result == False
        
        # Verify device1 was reverted to original state
        device1_data = self.coordinator.data["device1"]["devices"]["LIV Hub"]
        assert device1_data["power"] == original_device1_power  # Reverted
        
        # Verify device2 was never affected
        device2_data = self.coordinator.data["device2"]["devices"]["LIV Hub"]
        assert device2_data["power"] == original_device2_power  # Unchanged
        
        # Verify UI update was called twice (optimistic + revert)
        assert self.coordinator.async_update_listeners.call_count == 2
        
    def test_nonexistent_device_handling(self):
        """Test that updates to nonexistent devices don't crash or corrupt data."""
        # Mock successful API call
        self.api.set_device_power = AsyncMock(return_value=True)
        
        # Store original data for comparison
        original_data = {
            node_id: {
                "devices": {
                    device_name: device_data.copy()
                    for device_name, device_data in node_data["devices"].items()
                }
            }
            for node_id, node_data in self.coordinator.data.items()
        }
        
        # Attempt to update nonexistent device
        import asyncio
        result = asyncio.run(self.coordinator.async_set_device_power("nonexistent_node", "LIV Hub", True))
        
        # Should return True (API call succeeded) but not crash
        assert result == True
        
        # Verify original data is unchanged
        for node_id, node_data in self.coordinator.data.items():
            for device_name, device_data in node_data["devices"].items():
                for key, value in device_data.items():
                    assert value == original_data[node_id]["devices"][device_name][key]
        
        # UI update should not have been called (no data changed)
        self.coordinator.async_update_listeners.assert_not_called()


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio
    
    test = TestOptimisticUpdatesFix()
    
    print("🧪 Running Optimistic Updates Fix Tests")
    print("=" * 60)
    
    # Test 1: Power update isolation
    print("\n1. Testing power update isolation...")
    try:
        test.setup_method()
        asyncio.run(test.test_power_optimistic_update_isolation())
        print("✅ Power update isolation test passed")
    except Exception as e:
        print(f"❌ Power update isolation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LED brightness update isolation
    print("\n2. Testing LED brightness update isolation...")
    try:
        test.setup_method()
        asyncio.run(test.test_led_brightness_optimistic_update_isolation())
        print("✅ LED brightness update isolation test passed")
    except Exception as e:
        print(f"❌ LED brightness update isolation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: LED color update isolation
    print("\n3. Testing LED color update isolation...")
    try:
        test.setup_method()
        asyncio.run(test.test_led_color_optimistic_update_isolation())
        print("✅ LED color update isolation test passed")
    except Exception as e:
        print(f"❌ LED color update isolation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Failed API call revert isolation
    print("\n4. Testing failed API call revert isolation...")
    try:
        test.setup_method()
        asyncio.run(test.test_failed_api_call_revert_isolation())
        print("✅ Failed API call revert isolation test passed")
    except Exception as e:
        print(f"❌ Failed API call revert isolation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Nonexistent device handling
    print("\n5. Testing nonexistent device handling...")
    try:
        test.setup_method()
        test.test_nonexistent_device_handling()
        print("✅ Nonexistent device handling test passed")
    except Exception as e:
        print(f"❌ Nonexistent device handling test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Optimistic updates fix tests completed!")
    print("\nThe fix ensures that:")
    print("✅ Device updates are properly isolated")
    print("✅ Multi-device data integrity is maintained") 
    print("✅ Failed API calls only affect the target device")
    print("✅ Nonexistent devices don't cause data corruption")