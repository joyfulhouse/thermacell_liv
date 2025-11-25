#!/usr/bin/env python3
"""
Investigate device information available through pythermacell library.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import ThermacellClient


async def investigate_device_info():
    """Investigate all available device information."""
    print("Investigating Device Information via pythermacell")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        print("Authenticating...")
        async with ThermacellClient(
            username=THERMACELL_USERNAME,
            password=THERMACELL_PASSWORD,
            session=session,
        ) as client:
            print("Authentication successful")

            devices = await client.get_devices()
            print(f"\nFound {len(devices)} device(s)")

            for device in devices:
                print(f"\nDevice: {device.name} ({device.node_id})")
                print("-" * 40)

                # Display all available device properties
                print("\nBasic Info:")
                print(f"  Node ID: {device.node_id}")
                print(f"  Name: {device.name}")
                print(f"  Model: {device.model}")
                print(f"  Firmware Version: {device.fw_version}")
                print(f"  Hub Serial: {device.hub_serial}")

                print("\nConnectivity:")
                print(f"  Online: {device.is_online}")

                print("\nPower State:")
                print(f"  Powered On: {device.is_powered_on}")
                print(f"  System Status: {device.system_status}")
                print(f"  System Runtime: {device.system_runtime} minutes")

                print("\nLED State:")
                print(f"  LED Power: {device.led_power}")
                print(f"  LED Brightness: {device.led_brightness}")
                print(f"  LED Hue: {device.led_hue}")
                print(f"  LED Saturation: {device.led_saturation}")
                print(f"  LED Value: {device.led_value}")

                print("\nRefill & Error:")
                print(f"  Refill Life: {device.refill_life}%")
                print(f"  Error Code: {device.error_code}")

                # Format runtime
                if device.system_runtime:
                    runtime = device.system_runtime
                    days = runtime // (24 * 60)
                    hours = (runtime % (24 * 60)) // 60
                    minutes = runtime % 60

                    runtime_parts = []
                    if days > 0:
                        runtime_parts.append(f"{days} day{'s' if days != 1 else ''}")
                    if hours > 0:
                        runtime_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                    if minutes > 0:
                        runtime_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

                    formatted_runtime = ", ".join(runtime_parts) if runtime_parts else "0 minutes"
                    print(f"\nFormatted Runtime: {formatted_runtime}")

    print("\nDevice information investigation completed!")


async def main():
    """Run device info investigation."""
    await investigate_device_info()


if __name__ == "__main__":
    asyncio.run(main())
