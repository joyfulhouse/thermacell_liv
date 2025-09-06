#!/usr/bin/env python3
"""
Extended investigation for total system runtime - check if there are cumulative values
or other endpoints that might have the total runtime information.
"""
import asyncio
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from unittest.mock import MagicMock


async def investigate_extended_runtime(session):
    """Look for total runtime in different ways."""
    print("🕵️ Extended Runtime Investigation")
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
    
    # Check all available endpoints for runtime data
    print("\n🔍 Checking multiple data sources...")
    
    # 1. Check node status endpoint
    print("\n📊 Node Status Endpoint:")
    status_data = await api.get_node_status(node_id)
    if status_data:
        print(f"Status data keys: {list(status_data.keys())}")
        if "connectivity" in status_data:
            connectivity = status_data["connectivity"]
            timestamp = connectivity.get("timestamp", 0)
            if timestamp > 0:
                # Convert timestamp to readable date
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"   Last seen: {dt}")
                print(f"   Timestamp: {timestamp}")
    
    # 2. Check node config endpoint  
    print("\n📊 Node Config Endpoint:")
    config_data = await api.get_node_config(node_id)
    if config_data:
        print(f"Config data keys: {list(config_data.keys())}")
        # Look for any time/runtime related info
        def search_config_for_runtime(data, path=""):
            results = []
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    key_lower = key.lower()
                    
                    if any(term in key_lower for term in ['time', 'runtime', 'hour', 'total']):
                        results.append((current_path, value))
                    
                    if isinstance(value, (int, float)) and 3000 < value < 6000:
                        results.append((f"{current_path} (potential runtime)", value))
                    
                    if isinstance(value, dict):
                        results.extend(search_config_for_runtime(value, current_path))
            
            return results
        
        runtime_candidates = search_config_for_runtime(config_data)
        if runtime_candidates:
            print("   Runtime candidates found:")
            for path, value in runtime_candidates:
                print(f"      {path}: {value}")
                if isinstance(value, (int, float)) and value > 0:
                    total_minutes = int(value)
                    days = total_minutes // (24 * 60)
                    hours = (total_minutes % (24 * 60)) // 60
                    mins = total_minutes % 60
                    print(f"         → As time: {days}d {hours}h {mins}m")
    
    # 3. Check if there are repeller-specific runtime values
    print("\n🔍 Checking individual repeller data for cumulative runtime...")
    nodes = await api.get_user_nodes()
    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                params = node.get("params", {}).get("LIV Hub", {})
                
                # Look at repeller data for runtime info
                repeller_runtimes = []
                for key, value in params.items():
                    if "repeller" in key and isinstance(value, dict):
                        rep_data = value
                        print(f"\n   {key} data:")
                        for rep_key, rep_value in rep_data.items():
                            print(f"      {rep_key}: {rep_value}")
                            if "time" in rep_key.lower() or "runtime" in rep_key.lower():
                                repeller_runtimes.append((f"{key}.{rep_key}", rep_value))
                
                if repeller_runtimes:
                    print(f"\n   Repeller runtime data found:")
                    for path, value in repeller_runtimes:
                        print(f"      {path}: {value}")
                
                # Check if we need to sum up different runtime components
                current_runtime = params.get("Current Runtime", 0)
                daily_runtime = params.get("Daily Runtime", 0) 
                system_runtime = params.get("System Runtime", 0)
                
                print(f"\n📊 Runtime Component Analysis:")
                print(f"   Current Runtime: {current_runtime} minutes")
                print(f"   Daily Runtime: {daily_runtime} minutes") 
                print(f"   System Runtime: {system_runtime} minutes")
                
                total_sum = current_runtime + daily_runtime + system_runtime
                print(f"   Sum of all: {total_sum} minutes")
                
                # Check if any single value is close to expected
                expected = 4524  # 3d 3h 24m in minutes
                print(f"\n🎯 Comparison to expected {expected} minutes (3d 3h 24m):")
                
                candidates = {
                    "Current Runtime": current_runtime,
                    "Daily Runtime": daily_runtime,
                    "System Runtime": system_runtime,
                    "Sum of all": total_sum
                }
                
                for name, value in candidates.items():
                    if value > 0:
                        diff = abs(value - expected)
                        days = value // (24 * 60)
                        hours = (value % (24 * 60)) // 60
                        mins = value % 60
                        
                        print(f"   {name}: {value} min ({days}d {hours}h {mins}m) - diff: {diff}")
                        if diff < 500:  # Within 8 hours
                            print(f"      ✅ CLOSE MATCH!")
                
                break
    
    # 4. Manual calculation suggestion
    print(f"\n💡 MANUAL INVESTIGATION NEEDED:")
    print(f"   Expected total runtime: 3 days, 3 hours, 24 minutes = 4524 minutes")
    print(f"   Current 'System Runtime': 715 minutes (11h 55m)")
    print(f"   Difference: {4524 - 715} = 3809 minutes missing")
    print(f"")
    print(f"   Possible explanations:")
    print(f"   1. 'System Runtime' is current session, not total lifetime")
    print(f"   2. Total runtime might be stored in a different parameter")
    print(f"   3. Need to check device settings or different API endpoint")
    print(f"   4. Runtime might reset periodically (daily/weekly)")


async def main():
    """Run the extended runtime investigation."""
    async with aiohttp.ClientSession() as session:
        await investigate_extended_runtime(session)
    
    print("\n🎉 Extended runtime investigation completed!")


if __name__ == "__main__":
    asyncio.run(main())