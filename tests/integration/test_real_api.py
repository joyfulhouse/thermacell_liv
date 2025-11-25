#!/usr/bin/env python3
"""
Test script to validate Thermacell LIV API using pythermacell library.
This script tests actual API calls and verifies the library works correctly.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import ThermacellClient


async def test_real_api():
    """Test the Thermacell LIV API using pythermacell library."""
    print("Testing Thermacell LIV API with pythermacell library...")
    print(f"Username: {THERMACELL_USERNAME}")
    print("-" * 60)

    async with aiohttp.ClientSession() as session:
        try:
            async with ThermacellClient(
                username=THERMACELL_USERNAME,
                password=THERMACELL_PASSWORD,
                session=session,
            ) as client:
                # Test 1: Get devices (validates authentication and API connectivity)
                print("1. Testing authentication and device discovery...")
                devices = await client.get_devices()
                print(f"   Found {len(devices)} device(s)")

                if not devices:
                    print("   No devices found!")
                    return

                # Test 2: Display device information
                print("\n2. Device details:")
                for i, device in enumerate(devices, 1):
                    print(f"   Device {i}:")
                    print(f"     Node ID: {device.node_id}")
                    print(f"     Name: {device.name}")
                    print(f"     Model: {device.model}")
                    print(f"     Firmware: {device.fw_version}")
                    print(f"     Online: {device.is_online}")
                    print(f"     Powered On: {device.is_powered_on}")

                # Test 3: Get detailed device state (read-only)
                print("\n3. Device state details (first device):")
                device = devices[0]
                print(f"   Hub Serial: {device.hub_serial}")
                print(f"   System Status: {device.system_status}")
                print(f"   System Runtime: {device.system_runtime} minutes")
                print(f"   Refill Life: {device.refill_life}%")
                print(f"   LED Power: {device.led_power}")
                print(f"   LED Brightness: {device.led_brightness}")
                print(f"   LED Color: H={device.led_hue}, S={device.led_saturation}, V={device.led_value}")
                print(f"   Error Code: {device.error_code}")

                print("\n" + "=" * 60)
                print("API testing completed successfully!")

        except Exception as e:
            print(f"Error during API testing: {e}")
            import traceback

            traceback.print_exc()


def main():
    """Run the API test."""
    asyncio.run(test_real_api())


if __name__ == "__main__":
    main()
