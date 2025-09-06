#!/usr/bin/env python3
"""
Simple test of LED brightness control through the API.
"""
import asyncio
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from unittest.mock import MagicMock


async def test_brightness_api(session):
    """Test LED brightness control directly through the API."""
    print("🧪 Testing LED Brightness API Control")
    print("=" * 50)
    
    # Create a mock HomeAssistant instance
    hass = MagicMock()
    
    # Initialize API
    api = ThermacellLivAPI(hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    api.session = session
    
    node_id = "JM7UVxmMgPUYUhVJVBWEf6"
    device_name = "LIV Hub"
    
    print("🔐 Authenticating...")
    auth_success = await api.authenticate()
    if not auth_success:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get current state
    print("\n📊 Getting current device parameters...")
    nodes = await api.get_user_nodes()
    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                params = node.get("params", {}).get("LIV Hub", {})
                current_brightness = params.get("LED Brightness", "Unknown")
                print(f"   Current LED Brightness: {current_brightness}%")
                break
    
    # Test different brightness levels
    test_values = [
        {"ha_brightness": 143, "description": "56% (your current setting)"},
        {"ha_brightness": 76, "description": "30%"},
        {"ha_brightness": 204, "description": "80%"},
        {"ha_brightness": 25, "description": "10%"},
    ]
    
    for test in test_values:
        ha_brightness = test["ha_brightness"]
        description = test["description"]
        
        print(f"\n🔧 Testing brightness: {ha_brightness} (HA format) - {description}")
        
        # Use the API method that converts HA brightness (0-255) to Thermacell (0-100)
        success = await api.set_device_led_brightness(node_id, device_name, ha_brightness)
        
        if success:
            print("✅ API call successful")
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Check the result
            nodes = await api.get_user_nodes()
            if nodes:
                for node in nodes:
                    if node["id"] == node_id:
                        params = node.get("params", {}).get("LIV Hub", {})
                        actual_brightness = params.get("LED Brightness", 0)
                        
                        # Calculate expected Thermacell value
                        expected_thermacell = int((ha_brightness / 255) * 100)
                        
                        print(f"📊 Result:")
                        print(f"   Expected (Thermacell %): {expected_thermacell}")
                        print(f"   Actual (Thermacell %): {actual_brightness}")
                        
                        if abs(actual_brightness - expected_thermacell) <= 1:
                            print("✅ Brightness set correctly!")
                        else:
                            print(f"⚠️  Brightness mismatch")
                        break
        else:
            print("❌ API call failed")
    
    print(f"\n🎯 Final verification - setting back to 56%...")
    final_success = await api.set_device_led_brightness(node_id, device_name, 143)
    
    if final_success:
        await asyncio.sleep(2)
        nodes = await api.get_user_nodes()
        if nodes:
            for node in nodes:
                if node["id"] == node_id:
                    params = node.get("params", {}).get("LIV Hub", {})
                    final_brightness = params.get("LED Brightness", 0)
                    print(f"📊 Final brightness: {final_brightness}% (should be ~56%)")
                    
                    if abs(final_brightness - 56) <= 1:
                        print("✅ 56% brightness restoration SUCCESSFUL!")
                    else:
                        print(f"⚠️  Expected ~56%, got {final_brightness}%")
                    break


async def main():
    """Run the brightness test."""
    async with aiohttp.ClientSession() as session:
        await test_brightness_api(session)
    
    print("\n🎉 LED brightness test completed!")


if __name__ == "__main__":
    asyncio.run(main())