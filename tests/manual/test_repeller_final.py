#!/usr/bin/env python3
"""
Final test of repeller control with corrected API structure.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class RepellerFinalTester:
    """Final test of repeller control functionality."""
    
    def __init__(self):
        self.base_url = THERMACELL_API_BASE_URL.rstrip('/')
        self.username = THERMACELL_USERNAME
        self.password = THERMACELL_PASSWORD
        self.access_token = None
        self.user_id = None
        self.session = None
    
    def _decode_jwt_payload(self, jwt_token: str) -> dict:
        """Decode JWT token payload without verification."""
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return {}
            
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded_bytes = base64.urlsafe_b64decode(payload)
            return json.loads(decoded_bytes.decode('utf-8'))
        except Exception:
            return {}
    
    async def authenticate(self) -> bool:
        """Authenticate and extract tokens."""
        try:
            url = f"{self.base_url}/v1/login2"
            data = {
                "user_name": self.username,
                "password": self.password,
            }

            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.access_token = auth_data.get("accesstoken")
                    
                    id_token = auth_data.get("idtoken")
                    if id_token:
                        id_payload = self._decode_jwt_payload(id_token)
                        if id_payload:
                            self.user_id = id_payload.get("custom:user_id")
                    
                    return self.access_token is not None and self.user_id is not None
                else:
                    return False
        except Exception:
            return False
    
    async def set_repeller_power(self, node_id: str, power_on: bool) -> bool:
        """Set repeller power using corrected API structure."""
        headers = {"Authorization": self.access_token}
        
        # Use the corrected API structure
        url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        payload = {
            "LIV Hub": {
                "Enable Repellers": power_on
            }
        }
        
        action = "ON" if power_on else "OFF"
        print(f"🔄 Turning repellers {action} for node {node_id}...")
        print(f"   URL: {url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.put(url, json=payload, headers=headers, timeout=timeout) as response:
                print(f"   Status: {response.status}")
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        print(f"   ✅ SUCCESS! Response: {json.dumps(response_data, indent=2)}")
                        return True
                    except:
                        print(f"   ✅ SUCCESS! (non-JSON): {response_text}")
                        return True
                else:
                    try:
                        error_data = json.loads(response_text)
                        print(f"   ❌ Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"   ❌ Error: {response_text}")
                    return False
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    async def get_repeller_status(self, node_id: str) -> dict:
        """Get current repeller status."""
        headers = {"Authorization": self.access_token}
        
        # Get current parameters to see the state
        params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        
        try:
            async with self.session.get(params_url, headers=headers) as response:
                if response.status == 200:
                    params_data = await response.json()
                    liv_hub_params = params_data.get("LIV Hub", {})
                    
                    enable_repellers = liv_hub_params.get("Enable Repellers", False)
                    refill_life = liv_hub_params.get("Refill Life", 0)
                    led_hue = liv_hub_params.get("LED Hue", 0)
                    led_brightness = liv_hub_params.get("LED Brightness", 0)
                    
                    print("📊 Current Status:")
                    print(f"   Enable Repellers: {enable_repellers}")
                    print(f"   Refill Life: {refill_life} hours")
                    print(f"   LED Hue: {led_hue}")
                    print(f"   LED Brightness: {led_brightness}")
                    
                    return {
                        "enable_repellers": enable_repellers,
                        "refill_life": refill_life,
                        "led_hue": led_hue,
                        "led_brightness": led_brightness
                    }
        except Exception as e:
            print(f"   ❌ Error getting status: {e}")
        
        return {}
    
    async def test_led_control(self, node_id: str):
        """Test LED color and brightness control."""
        headers = {"Authorization": self.access_token}
        
        print(f"🌈 Testing LED control for node {node_id}...")
        
        # Test different LED colors
        led_tests = [
            {"hue": 0, "brightness": 100, "color": "Red"},
            {"hue": 120, "brightness": 80, "color": "Green"},  
            {"hue": 240, "brightness": 60, "color": "Blue"},
            {"hue": 60, "brightness": 90, "color": "Yellow"},
        ]
        
        for led_test in led_tests:
            url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
            payload = {
                "LIV Hub": {
                    "LED Hue": led_test["hue"],
                    "LED Brightness": led_test["brightness"]
                }
            }
            
            print(f"   🎨 Setting LED to {led_test['color']} (Hue: {led_test['hue']}, Brightness: {led_test['brightness']})...")
            
            try:
                async with self.session.put(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        print(f"      ✅ Success: {response_data.get('description', 'LED updated')}")
                    else:
                        error_text = await response.text()
                        print(f"      ❌ Failed: {error_text}")
                
                # Brief delay between color changes
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Exception: {e}")


async def main():
    """Main function to test repeller control with corrected API."""
    print("✅ Thermacell Repeller Control - Final Test")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tester = RepellerFinalTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Test with a known node
            test_node_id = "JM7UVxmMgPUYUhVJVBWEf6"
            
            print(f"\n🎯 Testing with node: {test_node_id}")
            
            # Get initial status
            print("\n📊 Initial Status:")
            await tester.get_repeller_status(test_node_id)
            
            # Test turning repellers ON
            print(f"\n{'='*60}")
            success = await tester.set_repeller_power(test_node_id, True)
            
            if success:
                print("\n⏸️  Waiting 3 seconds for status update...")
                await asyncio.sleep(3)
                
                # Check status after turning on
                await tester.get_repeller_status(test_node_id)
                
                # Test LED control while repellers are on
                print(f"\n{'='*60}")
                await tester.test_led_control(test_node_id)
                
                # Test turning repellers OFF
                print(f"\n{'='*60}")
                await tester.set_repeller_power(test_node_id, False)
                
                print("\n⏸️  Waiting 3 seconds for status update...")
                await asyncio.sleep(3)
                
                # Final status check
                print("\n📊 Final Status:")
                await tester.get_repeller_status(test_node_id)
            else:
                print("❌ Failed to control repellers")
        else:
            print("   ❌ Authentication failed")
    
    print("\n🎉 Final testing completed!")


if __name__ == "__main__":
    asyncio.run(main())