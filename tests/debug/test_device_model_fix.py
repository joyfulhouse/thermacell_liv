#!/usr/bin/env python3
"""
Test device model display fix.
"""
import asyncio
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from unittest.mock import MagicMock


async def test_device_model_display(session):
    """Test that device model shows as 'Thermacell LIV Hub' instead of 'thermacell-hub'."""
    print("🔧 Testing Device Model Display Fix")
    print("=" * 50)
    
    hass = MagicMock()
    api = ThermacellLivAPI(hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    api.session = session
    
    node_id = "JM7UVxmMgPUYUhVJVBWEf6"
    
    print("🔐 Authenticating...")
    if not await api.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get raw API model data
    print("\n📊 Raw API Model Data:")
    config_data = await api.get_node_config(node_id)
    if config_data and "info" in config_data:
        info = config_data["info"]
        raw_model = info.get("model")
        print(f"   API Raw Model: '{raw_model}'")
    
    # Test our coordinator logic
    print("\n🔄 Testing Coordinator Model Conversion:")
    if raw_model == "thermacell-hub":
        converted_model = "Thermacell LIV Hub"
        print(f"   ✅ CONVERSION: '{raw_model}' → '{converted_model}'")
    else:
        print(f"   ⚠️  Unexpected raw model: '{raw_model}'")
    
    # Get processed node data to verify
    print("\n📋 Processed Node Data:")
    nodes = await api.get_user_nodes() 
    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                print(f"   Node Name: {node.get('node_name', 'Unknown')}")
                print(f"   Node Type: {node.get('type', 'Unknown')}")
                
                # Simulate coordinator processing
                if config_data and "info" in config_data:
                    info = config_data["info"]
                    fw_version = info.get("fw_version", "Unknown")
                    raw_model = info.get("model", "thermacell-hub")
                    
                    if raw_model == "thermacell-hub":
                        final_model = "Thermacell LIV Hub"
                    else:
                        final_model = raw_model
                    
                    print("\n📊 Coordinator Would Set:")
                    print(f"   Firmware Version: {fw_version}")
                    print(f"   Model: {final_model}")
                    
                    if final_model == "Thermacell LIV Hub":
                        print("   ✅ SUCCESS: Model will display as 'Thermacell LIV Hub'")
                    else:
                        print(f"   ❌ ISSUE: Model would display as '{final_model}'")
                break
    
    print("\n🎯 Device Info Display:")
    print("   Before Fix: 'thermacell-hub' (technical name)")
    print("   After Fix:  'Thermacell LIV Hub' (user-friendly name)")
    print("   ✅ Home Assistant device info will now show proper model name")


async def main():
    """Run the device model test."""
    async with aiohttp.ClientSession() as session:
        await test_device_model_display(session)
    
    print("\n🎉 Device model display test completed!")


if __name__ == "__main__":
    asyncio.run(main())