#!/usr/bin/env python3
"""
Test the complete device information and sensors functionality via pythermacell.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import ThermacellClient


async def test_device_info_and_sensors():
    """Test the complete device info and sensor functionality."""
    print("Testing Complete Device Info and Sensors")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        print("Authenticating...")
        async with ThermacellClient(
            username=THERMACELL_USERNAME,
            password=THERMACELL_PASSWORD,
            session=session,
        ) as client:
            print("Authentication successful\n")

            devices = await client.get_devices()

            if not devices:
                print("No devices found")
                return

            device = devices[0]
            print(f"Testing device: {device.name}")
            print("-" * 40)

            # Test device info properties
            print("\n1. Device Info Properties:")
            print(f"   Node ID: {device.node_id}")
            print(f"   Name: {device.name}")
            print(f"   Model: {device.model}")
            print(f"   Firmware Version: {device.fw_version}")
            print(f"   Hub Serial: {device.hub_serial}")

            # Test connectivity
            print("\n2. Connectivity Status:")
            print(f"   Online: {device.is_online}")

            # Test power state
            print("\n3. Power State:")
            print(f"   Powered On: {device.is_powered_on}")
            print(f"   System Status Code: {device.system_status}")

            # Interpret system status
            status_text = "Unknown"
            if device.error_code and device.error_code > 0:
                status_text = "Error"
            elif not device.is_powered_on or device.system_status == 1:
                status_text = "Off"
            elif device.system_status == 2:
                status_text = "Warming Up"
            elif device.system_status == 3:
                status_text = "Protected"
            print(f"   Status Text: {status_text}")

            # Test runtime
            print("\n4. System Runtime:")
            runtime = device.system_runtime or 0
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
            print(f"   Raw Runtime: {runtime} minutes")
            print(f"   Formatted: {formatted_runtime}")
            print(f"   Total Hours: {round(runtime / 60, 1)}")
            print(f"   Total Days: {round(runtime / (24 * 60), 2)}")

            # Test LED state
            print("\n5. LED State:")
            print(f"   Power: {device.led_power}")
            print(f"   Brightness: {device.led_brightness}")
            print(f"   Hue: {device.led_hue}")
            print(f"   Saturation: {device.led_saturation}")
            print(f"   Value: {device.led_value}")

            # Test refill and error
            print("\n6. Refill and Error:")
            print(f"   Refill Life: {device.refill_life}%")
            print(f"   Error Code: {device.error_code}")

            # Summary
            print("\n" + "=" * 60)
            print("Summary of Findings:")
            print("   Device config working: Yes")
            print(f"   Firmware version available: {device.fw_version}")
            print(f"   Hub serial available: {device.hub_serial}")
            print(f"   System runtime available: {runtime} minutes")
            print(f"   Node ID available: {device.node_id}")

            print("\nWhat this enables in Home Assistant:")
            print(f"   Device info will show firmware version {device.fw_version}")
            print(f"   Device info will show serial number {device.hub_serial}")
            print("   System Runtime sensor will show formatted runtime")
            print("   All entities will have proper device grouping")

    print("\nDevice info and sensors test completed!")


async def main():
    """Run the device info and sensor test."""
    await test_device_info_and_sensors()


if __name__ == "__main__":
    asyncio.run(main())
