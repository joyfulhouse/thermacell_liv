#!/usr/bin/env python3
"""
Investigate device information available in the API.
"""
import asyncio
import aiohttp
import json
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from unittest.mock import MagicMock


async def investigate_device_info(session):
    """Investigate all available device information."""
    print("🔍 Investigating Device Information in API")
    print("=" * 60)
    
    hass = MagicMock()
    api = ThermacellLivAPI(hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    api.session = session
    
    node_id = "JM7UVxmMgPUYUhVJVBWEf6"
    
    print("🔐 Authenticating...")
    if not await api.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get user nodes (includes basic device info)
    print("\n📊 Getting user nodes...")
    nodes = await api.get_user_nodes()
    
    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                print(f"\n🏷️  NODE DATA for {node_id}:")
                print(json.dumps(node, indent=2))
                
                # Look specifically for firmware info
                print(f"\n🔍 Searching for firmware version...")
                for key, value in node.items():
                    if "fw" in key.lower() or "firmware" in key.lower() or "version" in key.lower():
                        print(f"   {key}: {value}")
                
                # Check params for additional info
                params = node.get("params", {})
                if "LIV Hub" in params:
                    liv_params = params["LIV Hub"]
                    print(f"\n🔍 LIV Hub Parameters:")
                    
                    # Look for runtime, serial, system ID
                    runtime_keys = []
                    serial_keys = []
                    system_keys = []
                    version_keys = []
                    
                    for key, value in liv_params.items():
                        key_lower = key.lower()
                        print(f"   {key}: {value}")
                        
                        if any(term in key_lower for term in ['runtime', 'uptime', 'time', 'hours', 'days']):
                            runtime_keys.append((key, value))
                        elif any(term in key_lower for term in ['serial', 'sn', 'number']):
                            serial_keys.append((key, value))
                        elif any(term in key_lower for term in ['system', 'id', 'uuid', 'guid']):
                            system_keys.append((key, value))
                        elif any(term in key_lower for term in ['version', 'fw', 'firmware', 'ver']):
                            version_keys.append((key, value))
                    
                    print(f"\n📊 POTENTIAL MATCHES:")
                    if version_keys:
                        print(f"   Firmware/Version keys: {version_keys}")
                    if runtime_keys:
                        print(f"   Runtime keys: {runtime_keys}")
                    if serial_keys:
                        print(f"   Serial keys: {serial_keys}")
                    if system_keys:
                        print(f"   System ID keys: {system_keys}")
                break
    
    # Get node status (might contain additional info)
    print(f"\n📊 Getting node status...")
    status = await api.get_node_status(node_id)
    
    if status:
        print(f"\n🏷️  NODE STATUS for {node_id}:")
        print(json.dumps(status, indent=2))
        
        # Look for firmware info in status
        print(f"\n🔍 Searching status for firmware/device info...")
        
        def search_nested(data, path=""):
            for key, value in data.items() if isinstance(data, dict) else []:
                current_path = f"{path}.{key}" if path else key
                key_lower = key.lower()
                
                if any(term in key_lower for term in ['fw', 'firmware', 'version', 'ver', 'runtime', 'uptime', 'serial', 'sn', 'system', 'id']):
                    print(f"   {current_path}: {value}")
                
                if isinstance(value, dict):
                    search_nested(value, current_path)
        
        search_nested(status)
    
    # Try to get additional device endpoints
    print(f"\n🔍 Trying additional API endpoints...")
    
    # Try device info endpoint
    try:
        device_info_response = await api._make_request("GET", f"/user/nodes/info?nodeid={node_id}")
        if device_info_response:
            print(f"\n📊 DEVICE INFO ENDPOINT:")
            print(json.dumps(device_info_response, indent=2))
    except:
        print("   No /user/nodes/info endpoint")
    
    # Try config endpoint  
    try:
        config_response = await api._make_request("GET", f"/user/nodes/config?nodeid={node_id}")
        if config_response:
            print(f"\n📊 DEVICE CONFIG ENDPOINT:")
            print(json.dumps(config_response, indent=2))
    except:
        print("   No /user/nodes/config endpoint")


async def main():
    """Run device info investigation."""
    async with aiohttp.ClientSession() as session:
        await investigate_device_info(session)
    
    print("\n🎉 Device information investigation completed!")


if __name__ == "__main__":
    asyncio.run(main())