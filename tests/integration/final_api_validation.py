#!/usr/bin/env python3
"""
Final API validation using pythermacell library.
Comprehensive test of all library functionality.
"""

import asyncio
from secrets import THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp
from pythermacell import AuthenticationError, ThermacellClient, ThermacellConnectionError


async def final_validation():
    """Comprehensive API validation."""
    print("Final Thermacell LIV API Validation")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print()

    async with aiohttp.ClientSession() as session:
        print("1. Testing Authentication...")
        try:
            async with ThermacellClient(
                username=THERMACELL_USERNAME,
                password=THERMACELL_PASSWORD,
                session=session,
            ) as client:
                print("   Authentication successful!")
                print()

                print("2. Testing Device Discovery...")
                devices = await client.get_devices()
                print(f"   Found {len(devices)} device(s)")

                if not devices:
                    print("   No devices - cannot test endpoints")
                    return

                print()
                print("3. Testing Device Properties...")

                for device in devices:
                    print(f"\n   Device: {device.name}")
                    print("   " + "-" * 40)

                    # All read-only properties
                    properties = [
                        ("node_id", device.node_id),
                        ("name", device.name),
                        ("model", device.model),
                        ("fw_version", device.fw_version),
                        ("hub_serial", device.hub_serial),
                        ("is_online", device.is_online),
                        ("is_powered_on", device.is_powered_on),
                        ("led_power", device.led_power),
                        ("led_brightness", device.led_brightness),
                        ("led_hue", device.led_hue),
                        ("led_saturation", device.led_saturation),
                        ("led_value", device.led_value),
                        ("refill_life", device.refill_life),
                        ("system_status", device.system_status),
                        ("system_runtime", device.system_runtime),
                        ("error_code", device.error_code),
                    ]

                    for prop_name, prop_value in properties:
                        status = "OK" if prop_value is not None else "N/A"
                        print(f"     {prop_name}: {prop_value} [{status}]")

                print()
                print("=" * 60)
                print("Validation completed successfully!")
                print()
                print("Summary:")
                print("  - Authentication: OK")
                print(f"  - Device Discovery: OK ({len(devices)} devices)")
                print("  - Property Access: OK")
                print()
                print("Note: Control commands not tested to avoid state changes.")
                print("Available control methods:")
                print("  - set_power(bool)")
                print("  - set_led_power(bool)")
                print("  - set_led_brightness(int)")
                print("  - set_led_color(hue, saturation, brightness)")
                print("  - reset_refill()")

        except AuthenticationError as e:
            print(f"   Authentication failed: {e}")
        except ThermacellConnectionError as e:
            print(f"   Connection error: {e}")
        except Exception as e:
            print(f"   Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(final_validation())
