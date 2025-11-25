#!/usr/bin/env python3
"""
Test to examine System Status values and understand the different states.

NOTE: This test is READ-ONLY and does not toggle device power.
The original test had excessive on/off calls which has been removed.
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


async def analyze_system_status():
    """Analyze current system status (read-only)."""
    print("Thermacell System Status Analysis")
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

            devices = await client.get_devices()

            if not devices:
                print("No devices found")
                return

            for device in devices:
                print(f"Device: {device.name} ({device.node_id})")
                print("-" * 40)

                # Current status parameters
                print("\nStatus Parameters:")
                print(f"   System Status Code: {device.system_status}")
                print(f"   Is Powered On: {device.is_powered_on}")
                print(f"   Error Code: {device.error_code}")
                print(f"   System Runtime: {device.system_runtime} minutes")

                # Interpret status
                status_text = interpret_system_status(
                    device.system_status,
                    device.is_powered_on,
                    device.error_code,
                )
                print(f"\n   Interpreted Status: {status_text}")

                # LED State
                print("\nLED State:")
                print(f"   LED Power: {device.led_power}")
                print(f"   LED Brightness: {device.led_brightness}")

                # Online status
                print("\nConnectivity:")
                print(f"   Online: {device.is_online}")

                print()

            # Document status code meanings
            print("=" * 60)
            print("System Status Code Reference:")
            print("-" * 40)
            print("   1 = Off (device commanded off)")
            print("   2 = Warming Up (transitioning)")
            print("   3 = Protected (fully operational)")
            print("   4 = Standby mode")
            print()
            print("Note: Error takes precedence if error_code > 0")

    print("\nSystem Status analysis completed!")


async def main():
    """Main function to analyze System Status."""
    await analyze_system_status()


if __name__ == "__main__":
    asyncio.run(main())
