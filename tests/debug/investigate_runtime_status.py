#!/usr/bin/env python3
"""
Investigate system runtime and status values to find correct parameters.
"""
import asyncio
from secrets import THERMACELL_API_BASE_URL, THERMACELL_PASSWORD, THERMACELL_USERNAME
from unittest.mock import MagicMock

import aiohttp

from custom_components.thermacell_liv.api import ThermacellLivAPI


async def investigate_runtime_and_status(session):
    """Investigate all runtime and status related parameters."""
    print("🔍 Investigating System Runtime and Status Parameters")
    print("=" * 70)

    hass = MagicMock()
    api = ThermacellLivAPI(hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    api.session = session

    node_id = "JM7UVxmMgPUYUhVJVBWEf6"

    print("🔐 Authenticating...")
    if not await api.authenticate():
        print("❌ Authentication failed")
        return

    print("✅ Authentication successful")

    # Get comprehensive parameter data
    print("\n📊 Getting comprehensive device parameters...")
    nodes = await api.get_user_nodes()

    if nodes:
        for node in nodes:
            if node["id"] == node_id:
                params = node.get("params", {}).get("LIV Hub", {})

                print("\n🔍 ALL LIV Hub Parameters:")
                print("=" * 50)

                # Look for all time/runtime related parameters
                time_params = {}
                status_params = {}
                numeric_params = {}

                for key, value in params.items():
                    key_lower = key.lower()

                    # Categorize parameters
                    if any(term in key_lower for term in ['time', 'runtime', 'hour', 'minute', 'day']):
                        time_params[key] = value
                    elif any(term in key_lower for term in ['status', 'state', 'mode']):
                        status_params[key] = value
                    elif isinstance(value, (int, float)) and value > 0:
                        numeric_params[key] = value

                print("⏰ TIME/RUNTIME Parameters:")
                for key, value in time_params.items():
                    print(f"   {key}: {value}")

                    # Calculate what this would be in days/hours/minutes if it's minutes
                    if isinstance(value, (int, float)) and value > 0:
                        total_minutes = int(value)
                        days = total_minutes // (24 * 60)
                        hours = (total_minutes % (24 * 60)) // 60
                        minutes = total_minutes % 60
                        print(f"      → As time: {days} days, {hours} hours, {minutes} minutes")

                print("\n📊 STATUS/STATE Parameters:")
                for key, value in status_params.items():
                    print(f"   {key}: {value}")

                print("\n🔢 NUMERIC Parameters (potential runtime candidates):")
                for key, value in sorted(numeric_params.items()):
                    if key not in time_params:  # Don't duplicate
                        print(f"   {key}: {value}")

                        # If it's a reasonable runtime value, calculate time
                        if isinstance(value, (int, float)) and 1000 < value < 10000:
                            total_minutes = int(value)
                            days = total_minutes // (24 * 60)
                            hours = (total_minutes % (24 * 60)) // 60
                            mins = total_minutes % 60
                            print(f"      → As time: {days} days, {hours} hours, {mins} minutes")

                            # Check if this matches expected ~3 days 3 hours 24 minutes
                            expected_total = (3 * 24 * 60) + (3 * 60) + 24  # ~4524 minutes
                            if abs(total_minutes - expected_total) < 300:  # Within 5 hours
                                print(f"      ✅ POTENTIAL MATCH for ~3d 3h 24m (expected ~{expected_total} min)")

                # Look specifically for system status values
                print("\n🎯 CURRENT VALUES vs EXPECTED:")
                current_runtime = params.get("System Runtime", 0)
                current_status = params.get("System Status", 1)

                print(f"   Current 'System Runtime': {current_runtime}")
                if current_runtime > 0:
                    days = current_runtime // (24 * 60)
                    hours = (current_runtime % (24 * 60)) // 60
                    mins = current_runtime % 60
                    print(f"      → Time: {days} days, {hours} hours, {mins} minutes")

                print(f"   Current 'System Status': {current_status}")
                print("   Expected Runtime: ~3 days, 3 hours, 24 minutes (~4524 minutes)")
                print("   Expected Status: 'Protected' when operational")

                # Check alternative runtime parameters
                alt_candidates = []
                for key, value in params.items():
                    if isinstance(value, (int, float)) and 4000 < value < 5000:
                        alt_candidates.append((key, value))

                if alt_candidates:
                    print("\n🎯 ALTERNATIVE RUNTIME CANDIDATES (4000-5000 range):")
                    for key, value in alt_candidates:
                        days = int(value) // (24 * 60)
                        hours = (int(value) % (24 * 60)) // 60
                        mins = int(value) % 60
                        print(f"   {key}: {value} → {days}d {hours}h {mins}m")

                break

    print("\n📋 INVESTIGATION SUMMARY:")
    print("   🔍 Need to find parameter showing ~3d 3h 24m (~4524 minutes)")
    print("   🔍 Need to map system status codes to 'Protected' state")
    print("   💡 Check all numeric parameters in 4000-5000 range")


async def main():
    """Run the runtime and status investigation."""
    async with aiohttp.ClientSession() as session:
        await investigate_runtime_and_status(session)

    print("\n🎉 Runtime and status investigation completed!")


if __name__ == "__main__":
    asyncio.run(main())
