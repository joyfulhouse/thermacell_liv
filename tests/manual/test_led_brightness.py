#!/usr/bin/env python3
"""
Test LED brightness parameters and control in the Thermacell API.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class LEDBrightnessTester:
    """Test LED brightness control and parameters."""
    
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
    
    async def get_all_led_params(self, node_id: str):
        """Get all LED-related parameters from the API."""
        headers = {"Authorization": self.access_token}
        
        print(f"🔍 Examining all LED parameters for node {node_id}...")
        params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        
        async with self.session.get(params_url, headers=headers) as response:
            if response.status == 200:
                params_data = await response.json()
                liv_hub_params = params_data.get("LIV Hub", {})
                
                # Find all LED-related parameters
                led_params = {}
                brightness_params = {}
                
                for key, value in liv_hub_params.items():
                    if "led" in key.lower():
                        led_params[key] = value
                    elif "bright" in key.lower():
                        brightness_params[key] = value
                
                print("📊 LED Parameters Found:")
                for key, value in led_params.items():
                    print(f"   {key}: {value}")
                
                print("📊 Brightness Parameters Found:")
                for key, value in brightness_params.items():
                    print(f"   {key}: {value}")
                
                print("📊 All Parameters (searching for brightness clues):")
                for key, value in liv_hub_params.items():
                    if any(term in key.lower() for term in ['bright', 'led', 'light', 'intensity', 'level', 'dim']):
                        print(f"   {key}: {value}")
                
                return liv_hub_params
        return {}
    
    async def test_brightness_control(self, node_id: str):
        """Test different brightness control approaches."""
        headers = {"Authorization": self.access_token}
        
        print("\n🧪 Testing brightness control approaches...")
        
        # Get current state first
        print("📊 Current LED state:")
        current_params = await self.get_all_led_params(node_id)
        
        # Test different brightness parameter names and values
        brightness_tests = [
            # Test 1: Current approach - LED Brightness
            {
                "name": "LED Brightness (current approach)",
                "params": {"LIV Hub": {"LED Brightness": 25}}
            },
            
            # Test 2: Try brightness as percentage
            {
                "name": "LED Brightness as percentage",
                "params": {"LIV Hub": {"LED Brightness": 56}}  # Match your stated 56%
            },
            
            # Test 3: Try different parameter names
            {
                "name": "Brightness (alternative name)",
                "params": {"LIV Hub": {"Brightness": 56}}
            },
            
            # Test 4: LED Level
            {
                "name": "LED Level",
                "params": {"LIV Hub": {"LED Level": 56}}
            },
            
            # Test 5: LED Intensity
            {
                "name": "LED Intensity",
                "params": {"LIV Hub": {"LED Intensity": 56}}
            },
            
            # Test 6: Try with LED Power combined
            {
                "name": "LED Brightness with LED Power",
                "params": {"LIV Hub": {"LED Brightness": 56, "LED Power": True}}
            },
            
            # Test 7: Try brightness as 0-255 range
            {
                "name": "LED Brightness (0-255 range)",
                "params": {"LIV Hub": {"LED Brightness": 143}}  # 56% of 255
            },
        ]
        
        set_params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        
        for i, test in enumerate(brightness_tests, 1):
            print(f"\n   Test {i}: {test['name']}")
            print(f"   Payload: {json.dumps(test['params'], indent=6)}")
            
            try:
                async with self.session.put(set_params_url, json=test['params'], headers=headers) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        response_data = await response.json()
                        print(f"   ✅ SUCCESS! Response: {json.dumps(response_data, indent=6)}")
                        
                        # Wait and check the actual result
                        await asyncio.sleep(3)
                        print("   📊 Checking result...")
                        await self.get_all_led_params(node_id)
                        
                    else:
                        response_text = await response.text()
                        try:
                            error_data = json.loads(response_text)
                            print(f"   ❌ Error: {json.dumps(error_data, indent=6)}")
                        except:
                            print(f"   ❌ Error: {response_text}")
                
                await asyncio.sleep(2)  # Brief pause between tests
                
            except Exception as e:
                print(f"   ❌ Exception: {e}")
    
    async def test_current_vs_expected(self, node_id: str):
        """Compare current API reading vs expected 56% brightness."""
        print("\n🔍 Current vs Expected Analysis")
        print("=" * 50)
        
        params = await self.get_all_led_params(node_id)
        
        # Analyze current LED Brightness value
        led_brightness = params.get("LED Brightness", None)
        led_hue = params.get("LED Hue", None)
        
        print("📊 Current API Values:")
        print(f"   LED Brightness: {led_brightness}")
        print(f"   LED Hue: {led_hue}")
        print("   Expected: 56% brightness")
        
        if led_brightness is not None:
            if led_brightness == 56:
                print("   ✅ LED Brightness matches expected 56%")
            elif led_brightness == 0:
                print("   ❌ LED appears OFF (brightness = 0)")
            elif led_brightness == 100:
                print("   ❌ LED appears at full brightness (not 56%)")
            else:
                percentage = led_brightness
                print(f"   ⚠️  LED Brightness is {percentage}% (expected 56%)")
        
        # Check if there are other brightness-related parameters
        all_params = {k: v for k, v in params.items() if isinstance(v, (int, float))}
        print("\n🔍 All numeric parameters (potential brightness indicators):")
        for key, value in sorted(all_params.items()):
            if key not in ["LED Brightness", "LED Hue"]:
                print(f"   {key}: {value}")


async def main():
    """Main function to test LED brightness."""
    print("💡 Thermacell LED Brightness Investigation")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tester = LEDBrightnessTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Test with known node
            test_node_id = "JM7UVxmMgPUYUhVJVBWEf6"
            
            # Analyze current state vs expected 56%
            await tester.test_current_vs_expected(test_node_id)
            
            # Test different brightness control approaches
            await tester.test_brightness_control(test_node_id)
            
        else:
            print("   ❌ Authentication failed")
    
    print("\n🎉 LED brightness investigation completed!")


if __name__ == "__main__":
    asyncio.run(main())