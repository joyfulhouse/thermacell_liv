#!/usr/bin/env python3
"""
Final test of LED brightness control after Home Assistant integration fixes.
"""
import asyncio
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from coordinator import ThermacellLivCoordinator
from unittest.mock import MagicMock


class BrightnessIntegrationTest:
    """Test the complete brightness control flow."""
    
    def __init__(self):
        self.node_id = "JM7UVxmMgPUYUhVJVBWEf6"  # Your test node
    
    async def test_brightness_flow(self):
        """Test the complete brightness control flow."""
        print("🧪 Testing Complete LED Brightness Control Flow")
        print("=" * 60)
        
        # Create a mock HomeAssistant instance
        hass = MagicMock()
        
        # Initialize API
        api = ThermacellLivAPI(hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
        
        # Initialize coordinator
        coordinator = ThermacellLivCoordinator(hass, api)
        
        print("🔐 Authenticating...")
        auth_success = await api.authenticate()
        if not auth_success:
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
        
        # Get initial data
        print("\n📊 Getting current device state...")
        await coordinator.async_refresh()
        
        if not coordinator.data:
            print("❌ No device data found")
            return
        
        device_name = "LIV Hub"  # Based on your API structure
        device_data = coordinator.get_device_data(self.node_id, device_name)
        
        if not device_data:
            print(f"❌ No device data found for {device_name}")
            return
        
        print(f"📊 Current device state:")
        print(f"   LED Power: {device_data.get('led_power', 'Unknown')}")
        print(f"   LED Brightness (HA format 0-255): {device_data.get('led_brightness', 'Unknown')}")
        print(f"   LED Brightness (Thermacell %): {device_data.get('led_brightness_pct', 'Unknown')}")
        print(f"   LED Color: {device_data.get('led_color', 'Unknown')}")
        
        # Test brightness control
        test_brightness_values = [143, 76, 204, 25]  # 56%, 30%, 80%, 10% in 0-255 range
        
        for brightness in test_brightness_values:
            percentage = int((brightness / 255) * 100)
            print(f"\n🔧 Testing brightness: {brightness} (HA format) = {percentage}% (Thermacell format)")
            
            success = await coordinator.async_set_device_led_brightness(
                self.node_id, device_name, brightness
            )
            
            if success:
                print("✅ API call successful")
                
                # Wait a moment for the change
                await asyncio.sleep(2)
                
                # Refresh data and check result
                await coordinator.async_refresh()
                updated_data = coordinator.get_device_data(self.node_id, device_name)
                
                if updated_data:
                    actual_brightness = updated_data.get('led_brightness', 0)
                    actual_pct = updated_data.get('led_brightness_pct', 0)
                    print(f"📊 Updated state:")
                    print(f"   LED Brightness (HA): {actual_brightness}")
                    print(f"   LED Brightness (%): {actual_pct}")
                    
                    # Check if it matches expected
                    if abs(actual_brightness - brightness) <= 2:  # Allow for rounding
                        print("✅ Brightness set correctly!")
                    else:
                        print(f"⚠️  Brightness mismatch: expected {brightness}, got {actual_brightness}")
                else:
                    print("❌ Could not get updated device data")
            else:
                print("❌ API call failed")
        
        # Test the specific 56% case the user mentioned
        print(f"\n🎯 Testing specific 56% brightness case...")
        target_56_percent = int(0.56 * 255)  # Should be 143
        print(f"   56% = {target_56_percent} in HA format")
        
        success = await coordinator.async_set_device_led_brightness(
            self.node_id, device_name, target_56_percent
        )
        
        if success:
            await asyncio.sleep(2)
            await coordinator.async_refresh()
            final_data = coordinator.get_device_data(self.node_id, device_name)
            
            if final_data:
                final_brightness = final_data.get('led_brightness', 0)
                final_pct = final_data.get('led_brightness_pct', 0)
                
                print(f"📊 Final 56% test result:")
                print(f"   LED Brightness (HA): {final_brightness}")
                print(f"   LED Brightness (%): {final_pct}")
                
                if abs(final_pct - 56) <= 1:  # Allow 1% tolerance
                    print("✅ 56% brightness test PASSED!")
                else:
                    print(f"❌ 56% brightness test FAILED: expected ~56%, got {final_pct}%")


async def main():
    """Run the brightness integration test."""
    async with aiohttp.ClientSession() as session:
        test = BrightnessIntegrationTest()
        await test.test_brightness_flow()
    
    print("\n🎉 Brightness integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())