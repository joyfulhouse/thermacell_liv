#!/usr/bin/env python3
"""
Test node details using pythermacell library.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import ThermacellClient


async def test_node_details():
    """Test node details via pythermacell."""
    print("Thermacell Node Details Testing")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        print("Authenticating...")
        async with ThermacellClient(
            username=THERMACELL_USERNAME,
            password=THERMACELL_PASSWORD,
            session=session,
        ) as client:
            print("   Success!")
            print()

            print("Getting Devices...")
            devices = await client.get_devices()
            print(f"   Found {len(devices)} device(s)")
            print()

            for i, device in enumerate(devices, 1):
                print(f"Device {i}: {device.name}")
                print("=" * 50)

                # Basic info
                print("\nBasic Information:")
                print(f"   Node ID: {device.node_id}")
                print(f"   Name: {device.name}")
                print(f"   Model: {device.model}")

                # Firmware and hardware
                print("\nFirmware/Hardware:")
                print(f"   Firmware Version: {device.fw_version}")
                print(f"   Hub Serial: {device.hub_serial}")

                # Status
                print("\nStatus:")
                print(f"   Online: {device.is_online}")
                print(f"   Powered On: {device.is_powered_on}")
                print(f"   System Status: {device.system_status}")
                print(f"   Error Code: {device.error_code}")

                # Runtime
                print("\nRuntime:")
                print(f"   System Runtime: {device.system_runtime} minutes")

                # LED
                print("\nLED Configuration:")
                print(f"   Power: {device.led_power}")
                print(f"   Brightness: {device.led_brightness}")
                print(f"   Hue: {device.led_hue}")
                print(f"   Saturation: {device.led_saturation}")
                print(f"   Value: {device.led_value}")

                # Refill
                print("\nRefill:")
                print(f"   Life: {device.refill_life}%")

                print()

    print("Testing completed!")


async def main():
    """Main function."""
    await test_node_details()


if __name__ == "__main__":
    asyncio.run(main())
