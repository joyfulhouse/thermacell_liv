#!/usr/bin/env python3
"""
Detailed test to understand all possible System Status values.

NOTE: This test is READ-ONLY and monitors current status only.
The original test had excessive on/off calls which has been removed.
To test state transitions, use the Home Assistant integration directly.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import ThermacellClient


def interpret_system_status(
    system_status: int | None,
    is_powered_on: bool,
    error_code: int | None,
) -> str:
    """Interpret system status based on parameters."""
    if error_code and error_code > 0:
        return "Error"
    elif not is_powered_on or system_status == 1:
        return "Off"
    elif system_status == 2:
        return "Warming Up"
    elif system_status == 3:
        return "Protected"
    elif system_status == 4:
        return "Standby"
    else:
        return f"Unknown (Status: {system_status})"


async def detailed_status_analysis():
    """Detailed analysis of current device status (read-only)."""
    print("Thermacell Detailed System Status Analysis")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        print("Authenticating...")
        async with ThermacellClient(
            username=THERMACELL_USERNAME,
            password=THERMACELL_PASSWORD,
            session=session,
        ) as client:
            print("   Success!")
            print()

            devices = await client.get_devices()

            if not devices:
                print("No devices found")
                return

            for device in devices:
                print(f"Device: {device.name}")
                print("=" * 50)

                # Device identification
                print("\n1. Device Identification:")
                print(f"   Node ID: {device.node_id}")
                print(f"   Name: {device.name}")
                print(f"   Model: {device.model}")
                print(f"   Firmware: {device.fw_version}")
                print(f"   Hub Serial: {device.hub_serial}")

                # Connectivity
                print("\n2. Connectivity:")
                print(f"   Online: {device.is_online}")

                # Power and status
                print("\n3. Power and Status:")
                print(f"   Powered On: {device.is_powered_on}")
                print(f"   System Status Code: {device.system_status}")
                print(f"   Error Code: {device.error_code}")

                status_text = interpret_system_status(
                    device.system_status,
                    device.is_powered_on,
                    device.error_code,
                )
                print(f"   Interpreted Status: {status_text}")

                # Runtime
                print("\n4. Runtime:")
                runtime = device.system_runtime or 0
                days = runtime // (24 * 60)
                hours = (runtime % (24 * 60)) // 60
                minutes = runtime % 60

                runtime_parts = []
                if days > 0:
                    runtime_parts.append(f"{days}d")
                if hours > 0:
                    runtime_parts.append(f"{hours}h")
                if minutes > 0:
                    runtime_parts.append(f"{minutes}m")

                formatted = " ".join(runtime_parts) if runtime_parts else "0m"
                print(f"   System Runtime: {runtime} minutes ({formatted})")

                # LED
                print("\n5. LED State:")
                print(f"   LED Power: {device.led_power}")
                print(f"   LED Brightness: {device.led_brightness}")
                print(f"   LED Hue: {device.led_hue}")
                print(f"   LED Saturation: {device.led_saturation}")
                print(f"   LED Value: {device.led_value}")

                # Refill
                print("\n6. Refill:")
                print(f"   Refill Life: {device.refill_life}%")

                print()

            # Reference information
            print("=" * 70)
            print("Status Code Reference:")
            print("-" * 50)
            print("   OFF State:      is_powered_on=False, status=1")
            print("   Warming Up:     is_powered_on=True, status=2")
            print("   Protected:      is_powered_on=True, status=3")
            print("   Error:          error_code > 0")
            print()
            print("NOTE: To test state transitions, toggle power via")
            print("      Home Assistant or the Thermacell mobile app.")

    print("\nDetailed analysis completed!")


async def main():
    """Main function for detailed status analysis."""
    await detailed_status_analysis()


if __name__ == "__main__":
    asyncio.run(main())
