#!/usr/bin/env python3
"""
Test repeller on/off control and debug API request structure.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class RepellerControlTester:
    """Test repeller control functionality."""
    
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
                    print(f"Authentication failed: {response.status}")
                    print(await response.text())
                    return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    async def get_nodes(self):
        """Get user nodes to find a test device."""
        headers = {"Authorization": self.access_token}
        
        print("🔍 Getting nodes list...")
        nodes_url = f"{self.base_url}/v1/user/nodes"
        async with self.session.get(nodes_url, headers=headers) as response:
            if response.status == 200:
                nodes_data = await response.json()
                print(f"   Nodes response: {json.dumps(nodes_data, indent=2)}")
                return nodes_data.get("nodes", [])
            else:
                print(f"   Failed to get nodes: {response.status}")
                print(f"   Error: {await response.text()}")
                return []
    
    async def get_node_params(self, node_id: str):
        """Get current parameters for a node."""
        headers = {"Authorization": self.access_token}
        
        print(f"📄 Getting params for node {node_id}...")
        params_url = f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}"
        async with self.session.get(params_url, headers=headers) as response:
            if response.status == 200:
                params_data = await response.json()
                print(f"   Current params: {json.dumps(params_data, indent=2)}")
                return params_data
            else:
                print(f"   Failed to get params: {response.status}")
                print(f"   Error: {await response.text()}")
                return {}
    
    async def test_repeller_control(self, node_id: str, turn_on: bool = True):
        """Test turning repeller on or off."""
        headers = {"Authorization": self.access_token}
        
        action = "ON" if turn_on else "OFF"
        print(f"🔄 Testing repeller {action} for node {node_id}...")
        
        # Test different payload structures
        test_payloads = [
            # Structure 1: Direct LIV Hub params
            {
                "node_id": node_id,
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": turn_on
                    }
                }
            },
            
            # Structure 2: Nested structure with device name
            {
                "node_id": node_id,
                "payload": {
                    "LIV Hub": {
                        "Name": "LIV Hub",
                        "Enable Repellers": turn_on
                    }
                }
            },
            
            # Structure 3: Different parameter name variations
            {
                "node_id": node_id,
                "payload": {
                    "LIV Hub": {
                        "enable_repellers": turn_on
                    }
                }
            },
            
            # Structure 4: Boolean as string
            {
                "node_id": node_id,
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": str(turn_on).lower()
                    }
                }
            },
            
            # Structure 5: Integer representation
            {
                "node_id": node_id,
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": 1 if turn_on else 0
                    }
                }
            },
            
            # Structure 6: Different device key
            {
                "node_id": node_id,
                "payload": {
                    "Device1": {
                        "Enable Repellers": turn_on
                    }
                }
            }
        ]
        
        set_params_url = f"{self.base_url}/v1/user/nodes/params"
        
        for i, payload in enumerate(test_payloads, 1):
            print(f"\n   Test {i}: Trying payload structure {i}")
            print(f"   Payload: {json.dumps(payload, indent=6)}")
            
            try:
                timeout = aiohttp.ClientTimeout(total=15)
                async with self.session.put(set_params_url, json=payload, headers=headers, timeout=timeout) as response:
                    print(f"   Status: {response.status}")
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            print(f"   ✅ SUCCESS! Response: {json.dumps(response_data, indent=6)}")
                            return True  # Success, stop testing other payloads
                        except:
                            print(f"   ✅ SUCCESS! (non-JSON response): {response_text}")
                            return True
                    else:
                        try:
                            error_data = json.loads(response_text)
                            print(f"   ❌ Error: {json.dumps(error_data, indent=6)}")
                        except:
                            print(f"   ❌ Error: {response_text}")
                        
                        # Add a small delay between attempts
                        await asyncio.sleep(1)
                            
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        return False
    
    async def test_node_status(self, node_id: str):
        """Check node status after control attempt."""
        headers = {"Authorization": self.access_token}
        
        print(f"📊 Checking status for node {node_id}...")
        status_url = f"{self.base_url}/v1/user/nodes/status?nodeid={node_id}"
        async with self.session.get(status_url, headers=headers) as response:
            if response.status == 200:
                status_data = await response.json()
                print(f"   Status: {json.dumps(status_data, indent=2)}")
                return status_data
            else:
                print(f"   Failed to get status: {response.status}")
                print(f"   Error: {await response.text()}")
                return {}


async def main():
    """Main function to test repeller control."""
    print("🔧 Thermacell Repeller Control Testing")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tester = RepellerControlTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Get available nodes
            nodes = await tester.get_nodes()
            
            if nodes:
                # Test with the first available node
                test_node_id = nodes[0]
                print(f"\n🎯 Testing with node: {test_node_id}")
                
                # Get current params to understand structure
                await tester.get_node_params(test_node_id)
                
                # Test turning ON
                print(f"\n{'='*60}")
                success = await tester.test_repeller_control(test_node_id, turn_on=True)
                
                if success:
                    print("\n⏸️  Waiting 3 seconds...")
                    await asyncio.sleep(3)
                    
                    # Check status after turning on
                    await tester.test_node_status(test_node_id)
                    
                    print(f"\n{'='*60}")
                    # Test turning OFF
                    await tester.test_repeller_control(test_node_id, turn_on=False)
                    
                    print("\n⏸️  Waiting 3 seconds...")
                    await asyncio.sleep(3)
                    
                    # Final status check
                    await tester.test_node_status(test_node_id)
            else:
                print("   ❌ No nodes found!")
        else:
            print("   ❌ Authentication failed")
    
    print("\n✅ Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())