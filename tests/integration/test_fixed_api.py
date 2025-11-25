#!/usr/bin/env python3
"""
Test the pythermacell client with real endpoints.
Validates that the library correctly handles authentication and device data.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import AuthenticationError, ThermacellClient, ThermacellConnectionError


async def test_pythermacell_client():
    """Test the pythermacell client."""
    print("Testing pythermacell Client")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print()

    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Authentication and device discovery
            print("1. Testing Authentication and Device Discovery...")
            async with ThermacellClient(
                username=THERMACELL_USERNAME,
                password=THERMACELL_PASSWORD,
                session=session,
            ) as client:
                devices = await client.get_devices()
                print(f"   Found {len(devices)} devices")

                if devices:
                    print("   Device details:")
                    for device in devices:
                        print(f"     - {device.name} ({device.node_id})")
                        print(f"       Online: {device.is_online}, Power: {device.is_powered_on}")

                    # Test 2: Detailed device info (read-only operations)
                    print("\n2. Testing Device Properties...")
                    device = devices[0]
                    properties = {
                        "node_id": device.node_id,
                        "name": device.name,
                        "model": device.model,
                        "fw_version": device.fw_version,
                        "hub_serial": device.hub_serial,
                        "is_online": device.is_online,
                        "is_powered_on": device.is_powered_on,
                        "led_power": device.led_power,
                        "led_brightness": device.led_brightness,
                        "led_hue": device.led_hue,
                        "led_saturation": device.led_saturation,
                        "led_value": device.led_value,
                        "refill_life": device.refill_life,
                        "system_status": device.system_status,
                        "system_runtime": device.system_runtime,
                        "error_code": device.error_code,
                    }

                    for prop, value in properties.items():
                        print(f"     {prop}: {value}")

                    print("\n   All properties retrieved successfully!")
                else:
                    print("   No devices found - this could mean:")
                    print("     - No devices are registered to this account")
                    print("     - Devices are offline")

                print()
                print("Testing completed!")

        except AuthenticationError as e:
            print(f"Authentication failed: {e}")
        except ThermacellConnectionError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_pythermacell_client())
