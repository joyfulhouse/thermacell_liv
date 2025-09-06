#!/usr/bin/env python3
"""
Test to examine System Status values and understand the different states.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class SystemStatusTester:
    """Test System Status values."""
    
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
    
    async def analyze_system_status(self, node_id: str):
        """Analyze System Status and related parameters."""
        headers = {"Authorization": self.access_token}
        
        print(f"🔍 Analyzing System Status for node {node_id}...")
        params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        
        async with self.session.get(params_url, headers=headers) as response:
            if response.status == 200:
                params_data = await response.json()
                liv_hub_params = params_data.get("LIV Hub", {})
                
                # Extract all status-related parameters
                system_status = liv_hub_params.get("System Status", None)
                system_state = liv_hub_params.get("System State", None)
                enable_repellers = liv_hub_params.get("Enable Repellers", False)
                system_shutoff = liv_hub_params.get("System Shutoff", None)
                error = liv_hub_params.get("Error", None)
                warming_timeout = liv_hub_params.get("Warming Timeout", None)
                current_runtime = liv_hub_params.get("Current Runtime", None)
                
                print(f"📊 Status Parameters:")
                print(f"   System Status: {system_status}")
                print(f"   System State: {system_state}")
                print(f"   Enable Repellers: {enable_repellers}")
                print(f"   System Shutoff: {system_shutoff}")
                print(f"   Error: {error}")
                print(f"   Warming Timeout: {warming_timeout}")
                print(f"   Current Runtime: {current_runtime}")
                
                # Try to interpret the status
                self.interpret_status(system_status, system_state, enable_repellers, error)
                
                return {
                    "system_status": system_status,
                    "system_state": system_state,
                    "enable_repellers": enable_repellers,
                    "system_shutoff": system_shutoff,
                    "error": error,
                    "warming_timeout": warming_timeout,
                    "current_runtime": current_runtime
                }
        return {}
    
    def interpret_status(self, system_status: int, system_state: int, enable_repellers: bool, error: int):
        """Try to interpret what the status values mean."""
        print(f"\n🧠 Status Interpretation:")
        
        # Try to guess based on common patterns
        if error and error > 0:
            print(f"   🚨 Error state detected (Error: {error})")
        elif not enable_repellers:
            print(f"   ⭕ System appears to be OFF (Enable Repellers: False)")
        elif enable_repellers and system_status == 3 and system_state == 3:
            print(f"   ✅ System appears to be ON and READY")
        elif enable_repellers and system_status != system_state:
            print(f"   🔄 System may be WARMING UP or transitioning")
        else:
            print(f"   ❓ Unknown state - need more data points")
    
    async def test_different_states(self, node_id: str):
        """Test system in different states to understand status codes."""
        print(f"\n🧪 Testing different system states...")
        
        # Get initial state
        print(f"\n1️⃣ Initial State:")
        initial = await self.analyze_system_status(node_id)
        
        # Turn system ON and check status during warmup
        print(f"\n2️⃣ Turning System ON:")
        await self.set_repeller_power(node_id, True)
        
        # Check status immediately after turning on (might be warming up)
        print(f"\n3️⃣ Status immediately after turning ON:")
        warmup = await self.analyze_system_status(node_id)
        
        # Wait a bit and check again
        print(f"\n⏳ Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        print(f"\n4️⃣ Status after 10 seconds:")
        running = await self.analyze_system_status(node_id)
        
        # Turn system OFF
        print(f"\n5️⃣ Turning System OFF:")
        await self.set_repeller_power(node_id, False)
        
        print(f"\n6️⃣ Status after turning OFF:")
        final = await self.analyze_system_status(node_id)
        
        # Summarize findings
        print(f"\n📝 Summary of Status Codes:")
        print(f"   OFF State:      System Status = {final.get('system_status')}, System State = {final.get('system_state')}")
        print(f"   ON (Initial):   System Status = {warmup.get('system_status')}, System State = {warmup.get('system_state')}")
        print(f"   ON (Running):   System Status = {running.get('system_status')}, System State = {running.get('system_state')}")
    
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
                return response.status == 200
        except Exception:
            return False


async def main():
    """Main function to test System Status."""
    print("🔍 Thermacell System Status Analysis")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tester = SystemStatusTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Test with known node
            test_node_id = "JM7UVxmMgPUYUhVJVBWEf6"
            
            # Analyze different states
            await tester.test_different_states(test_node_id)
        else:
            print("   ❌ Authentication failed")
    
    print("\n🎉 System Status analysis completed!")


if __name__ == "__main__":
    asyncio.run(main())