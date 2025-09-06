#!/usr/bin/env python3
"""
Detailed test to understand all possible System Status values.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class DetailedStatusTester:
    """Detailed System Status testing."""
    
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
    
    async def get_status(self, node_id: str) -> dict:
        """Get current status parameters."""
        headers = {"Authorization": self.access_token}
        
        params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        
        async with self.session.get(params_url, headers=headers) as response:
            if response.status == 200:
                params_data = await response.json()
                liv_hub_params = params_data.get("LIV Hub", {})
                
                return {
                    "system_status": liv_hub_params.get("System Status", None),
                    "system_state": liv_hub_params.get("System State", None),
                    "enable_repellers": liv_hub_params.get("Enable Repellers", False),
                    "error": liv_hub_params.get("Error", None),
                    "current_runtime": liv_hub_params.get("Current Runtime", None),
                    "daily_runtime": liv_hub_params.get("Daily Runtime", None),
                    "system_runtime": liv_hub_params.get("System Runtime", None),
                    "warming_timeout": liv_hub_params.get("Warming Timeout", None),
                    "hub_temperature": liv_hub_params.get("Hub Temperature", None),
                }
        return {}
    
    def interpret_system_status(self, status: dict) -> str:
        """Interpret system status based on parameters."""
        system_status = status.get("system_status")
        system_state = status.get("system_state")
        enable_repellers = status.get("enable_repellers", False)
        error = status.get("error", 0)
        
        # Based on observation and common IoT patterns
        if error and error > 0:
            return "Error"
        elif not enable_repellers:
            return "Off"
        elif enable_repellers and system_status == 1:
            return "Off"  # Device commanded off
        elif enable_repellers and system_status == 2:
            return "Warming Up"  # Transitioning/warming
        elif enable_repellers and system_status == 3:
            return "On"  # Fully operational
        elif system_status == 4:
            return "Standby"  # Standby mode
        else:
            return f"Unknown (Status: {system_status}, State: {system_state})"
    
    async def monitor_status_changes(self, node_id: str, duration: int = 30):
        """Monitor status changes over time."""
        print(f"🔄 Monitoring status changes for {duration} seconds...")
        
        start_time = asyncio.get_event_loop().time()
        last_status = None
        
        while (asyncio.get_event_loop().time() - start_time) < duration:
            current_status = await self.get_status(node_id)
            interpreted = self.interpret_system_status(current_status)
            
            if current_status != last_status:
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                print(f"   [{elapsed:2d}s] Status: {interpreted}")
                print(f"         System Status: {current_status.get('system_status')}")
                print(f"         System State: {current_status.get('system_state')}")
                print(f"         Enable Repellers: {current_status.get('enable_repellers')}")
                print(f"         Current Runtime: {current_status.get('current_runtime')}")
                print(f"         Temperature: {current_status.get('hub_temperature')}°C")
                last_status = current_status.copy()
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    async def set_repeller_power(self, node_id: str, power_on: bool) -> bool:
        """Set repeller power."""
        headers = {"Authorization": self.access_token}
        
        url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        payload = {
            "LIV Hub": {
                "Enable Repellers": power_on
            }
        }
        
        try:
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    action = "ON" if power_on else "OFF"
                    print(f"   ✅ Repeller turned {action}")
                    return True
                else:
                    print(f"   ❌ Failed to set power")
                    return False
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    async def comprehensive_status_test(self, node_id: str):
        """Comprehensive test to understand all status codes."""
        print(f"🔬 Comprehensive Status Test")
        print("=" * 60)
        
        # Start with system OFF
        print(f"\n1️⃣ Ensuring system is OFF...")
        await self.set_repeller_power(node_id, False)
        await asyncio.sleep(5)
        
        print(f"\n📊 OFF State monitoring:")
        await self.monitor_status_changes(node_id, 10)
        
        # Turn system ON and monitor warmup
        print(f"\n2️⃣ Turning system ON and monitoring warmup...")
        await self.set_repeller_power(node_id, True)
        
        print(f"\n📊 Warmup and Running State monitoring:")
        await self.monitor_status_changes(node_id, 60)  # Monitor for 1 minute
        
        # Turn system OFF
        print(f"\n3️⃣ Turning system OFF...")
        await self.set_repeller_power(node_id, False)
        
        print(f"\n📊 Shutdown monitoring:")
        await self.monitor_status_changes(node_id, 15)
        
        print(f"\n✅ Comprehensive test completed!")


async def main():
    """Main function for detailed status testing."""
    print("🔬 Thermacell Detailed System Status Analysis")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        tester = DetailedStatusTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Test with known node
            test_node_id = "JM7UVxmMgPUYUhVJVBWEf6"
            
            # Run comprehensive test
            await tester.comprehensive_status_test(test_node_id)
        else:
            print("   ❌ Authentication failed")
    
    print("\n🎉 Detailed analysis completed!")


if __name__ == "__main__":
    asyncio.run(main())