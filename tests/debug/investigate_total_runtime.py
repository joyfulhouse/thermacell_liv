#!/usr/bin/env python3
"""
Investigate total runtime to match Thermacell mobile app display.
The mobile app shows 3d 3h 24m but API shows 11h 55m.
Need to find the correct parameter or calculation.
"""
import asyncio
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI
from unittest.mock import MagicMock


async def investigate_total_runtime_sources(session):
    """Investigate all possible runtime sources that could sum to mobile app total."""
    print("🔍 Investigating Total Runtime Sources")
    print("Mobile app shows: 3d 3h 24m (4524 minutes)")
    print("API currently shows: 11h 55m (715 minutes)")
    print("Difference: 3809 minutes (2d 15h 29m)")
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
    
    nodes = await api.get_user_nodes()
    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                params = node.get("params", {}).get("LIV Hub", {})
                
                print("\n🔍 Comprehensive Runtime Analysis:")
                
                # Collect all runtime-related values
                runtime_values = {}
                
                # Hub-level runtime values
                hub_runtime_keys = [
                    "Current Runtime", 
                    "Daily Runtime", 
                    "System Runtime",
                    "Temperature Delay Time",
                    "Warming Timeout"
                ]
                
                for key in hub_runtime_keys:
                    if key in params:
                        runtime_values[key] = params[key]
                
                print("📊 Hub Runtime Values:")
                total_hub_runtime = 0
                for key, value in runtime_values.items():
                    print(f"   {key}: {value} minutes")
                    if "Runtime" in key:
                        total_hub_runtime += value
                
                print(f"   Hub Runtime Total: {total_hub_runtime} minutes")
                
                # Check individual repellers
                print("\n🔍 Individual Repeller Analysis:")
                active_repellers = []
                repeller_total_runtime = 0
                
                for key, value in params.items():
                    if "repeller" in key and isinstance(value, dict):
                        rep_data = value
                        if rep_data.get("serial_num"):  # Active repeller
                            active_repellers.append((key, rep_data))
                
                print(f"   Active repellers found: {len(active_repellers)}")
                
                for rep_name, rep_data in active_repellers:
                    print(f"\n   {rep_name}:")
                    cart_life = rep_data.get("cart_life", 0)
                    refill_life = rep_data.get("refill_life", 0)
                    
                    print(f"      Cart Life: {cart_life} (units unknown)")
                    print(f"      Refill Life: {refill_life} (units unknown)")
                    
                    # These might be in different units - investigate
                    if cart_life > 0:
                        print(f"         Cart Life as minutes: {cart_life}")
                        print(f"         Cart Life as hours: {cart_life / 60:.1f}")
                        print(f"         Cart Life as days: {cart_life / (24*60):.1f}")
                    
                    # Check if cart_life could be total runtime for this repeller
                    if cart_life > 1000:  # Reasonable for total runtime
                        repeller_total_runtime += cart_life
                
                if repeller_total_runtime > 0:
                    print(f"\n   Total repeller runtime (cart_life sum): {repeller_total_runtime}")
                
                # Total runtime calculations
                print("\n🧮 Runtime Calculation Attempts:")
                
                calculations = {
                    "Hub Runtime Only": total_hub_runtime,
                    "System Runtime Only": runtime_values.get("System Runtime", 0),
                    "Hub + Repeller Runtime": total_hub_runtime + repeller_total_runtime,
                    "Current + Daily + System": (
                        runtime_values.get("Current Runtime", 0) + 
                        runtime_values.get("Daily Runtime", 0) + 
                        runtime_values.get("System Runtime", 0)
                    )
                }
                
                mobile_app_total = 4524  # 3d 3h 24m
                
                print(f"   Target (mobile app): {mobile_app_total} minutes")
                
                best_match = None
                best_diff = float('inf')
                
                for calc_name, calc_value in calculations.items():
                    if calc_value > 0:
                        diff = abs(calc_value - mobile_app_total)
                        days = calc_value // (24 * 60)
                        hours = (calc_value % (24 * 60)) // 60
                        mins = calc_value % 60
                        
                        print(f"   {calc_name}: {calc_value} min ({days}d {hours}h {mins}m) - diff: {diff}")
                        
                        if diff < best_diff:
                            best_diff = diff
                            best_match = (calc_name, calc_value)
                        
                        if diff < 100:  # Within ~1.5 hours
                            print("      ✅ CLOSE MATCH!")
                
                if best_match:
                    print(f"\n🎯 Best Match: {best_match[0]} = {best_match[1]} minutes")
                    print(f"   Difference: {best_diff} minutes")
                    
                    if best_diff > 500:  # More than 8 hours off
                        print("   ⚠️  Still significantly different from mobile app")
                        print("   💡 Possible reasons:")
                        print("      - Mobile app includes historical data not in current API")
                        print("      - Different time units or calculation method")
                        print("      - API resets runtime periodically")
                else:
                    print("\n❌ No close matches found")
                
                # Manual investigation suggestions
                print("\n💡 Investigation Recommendations:")
                print("   1. Check if mobile app runtime resets daily/weekly/monthly")
                print("   2. Verify if API 'System Runtime' is current session only") 
                print("   3. Check if there's a separate 'Total Runtime' parameter")
                print("   4. Consider if cart_life values need different unit conversion")
                
                break


async def main():
    """Run total runtime investigation."""
    async with aiohttp.ClientSession() as session:
        await investigate_total_runtime_sources(session)
    
    print("\n🎉 Total runtime investigation completed!")


if __name__ == "__main__":
    asyncio.run(main())