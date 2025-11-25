#!/usr/bin/env python3
"""
Validate Thermacell LIV API using pythermacell library.
This script tests the library and verifies request/response handling.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import AuthenticationError, ThermacellClient, ThermacellConnectionError


async def validate_api():
    """Validate the pythermacell library."""
    print("Thermacell LIV API Validation (via pythermacell)")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print()

    async with aiohttp.ClientSession() as session:
        # Test 1: Authentication
        print("1. Testing Authentication...")
        print("-" * 50)

        try:
            async with ThermacellClient(
                username=THERMACELL_USERNAME,
                password=THERMACELL_PASSWORD,
                session=session,
            ) as client:
                print("   Authentication successful!")

                # Test 2: Get devices
                print("\n2. Testing Device Discovery...")
                print("-" * 50)

                devices = await client.get_devices()
                print(f"   Found {len(devices)} device(s)")

                if not devices:
                    print("   No devices found, skipping device tests")
                    return

                # Test 3: Device information
                print("\n3. Testing Device Information...")
                print("-" * 50)

                for i, device in enumerate(devices, 1):
                    print(f"\n   Device {i}:")
                    print(f"     ID: {device.node_id}")
                    print(f"     Name: {device.name}")
                    print(f"     Model: {device.model}")
                    print(f"     Firmware: {device.fw_version}")
                    print(f"     Online: {device.is_online}")

                # Test 4: Detailed device state (read-only)
                print("\n4. Testing Device State (read-only)...")
                print("-" * 50)

                device = devices[0]
                print(f"   Testing device: {device.name}")
                print(f"     Powered On: {device.is_powered_on}")
                print(f"     System Status: {device.system_status}")
                print(f"     LED Power: {device.led_power}")
                print(f"     LED Brightness: {device.led_brightness}")
                print(f"     Refill Life: {device.refill_life}%")
                print(f"     Error Code: {device.error_code}")

                # Test 5: Safe control test (NOTE: commented out to avoid state changes)
                print("\n5. Control Commands Test:")
                print("-" * 50)
                print("   SAFETY: Not executing control commands to avoid changing device state")
                print("   Available control methods in pythermacell:")
                print("     - device.set_power(bool)")
                print("     - device.set_led_power(bool)")
                print("     - device.set_led_brightness(int)")
                print("     - device.set_led_color(hue, saturation, brightness)")
                print("     - device.reset_refill()")

                print("\n" + "=" * 60)
                print("API validation completed successfully!")

        except AuthenticationError as e:
            print(f"   Authentication failed: {e}")
        except ThermacellConnectionError as e:
            print(f"   Connection error: {e}")
        except Exception as e:
            print(f"   Unexpected error: {e}")
            import traceback

            traceback.print_exc()


async def main():
    """Main validation function."""
    await validate_api()


if __name__ == "__main__":
    asyncio.run(main())
