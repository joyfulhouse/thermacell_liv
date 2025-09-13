#!/usr/bin/env python3
"""
Test node details and status endpoints with discovered node IDs.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class NodeDetailsTester:
    """Test node details endpoints."""
    
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
    
    async def test_node_details(self):
        """Test node details and status endpoints."""
        headers = {"Authorization": self.access_token}
        
        # Get nodes list
        print("1️⃣ Getting Nodes List...")
        nodes_url = f"{self.base_url}/v1/user/nodes"
        async with self.session.get(nodes_url, headers=headers) as response:
            if response.status == 200:
                nodes_data = await response.json()
                print(f"   Response: {json.dumps(nodes_data, indent=2)}")
                
                node_ids = nodes_data.get("nodes", [])
                print(f"   Found {len(node_ids)} nodes: {node_ids}")
                
                # Test each node
                for i, node_id in enumerate(node_ids):
                    await self._test_node_endpoints(node_id, i+1, headers)
        
    async def _test_node_endpoints(self, node_id: str, node_num: int, headers: dict):
        """Test various endpoints for a specific node."""
        print(f"\n{node_num}️⃣ Testing Node: {node_id}")
        
        # Try different node detail endpoints
        node_endpoints = [
            f"/v1/user/nodes/{node_id}",
            f"/v1/user/nodes/details?nodeid={node_id}",
            f"/v1/user/nodes/status?nodeid={node_id}",
            f"/v1/user/nodes/params?nodeid={node_id}",
            f"/v1/nodes/{node_id}",
            f"/v1/nodes/{node_id}/status",
            f"/v1/nodes/{node_id}/params",
        ]
        
        for endpoint in node_endpoints:
            await self._test_endpoint("GET", endpoint, headers, detailed=True)
    
    async def _test_endpoint(self, method: str, endpoint: str, headers: dict, detailed: bool = False):
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        print(f"   📡 {method} {endpoint}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with self.session.request(method, url, headers=headers, timeout=timeout) as response:
                print(f"      Status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print("      ✅ SUCCESS!")
                        
                        if detailed:
                            response_str = json.dumps(data, indent=8)
                            if len(response_str) > 1000:
                                print(f"      Data (truncated): {response_str[:1000]}...")
                            else:
                                print(f"      Data: {response_str}")
                        else:
                            print(f"      Keys: {list(data.keys()) if isinstance(data, dict) else f'List[{len(data)}]'}")
                            
                    except json.JSONDecodeError:
                        text = await response.text()
                        print(f"      ✅ SUCCESS! (non-JSON): {text[:200]}...")
                        
                elif response.status in [400, 401, 403, 404, 405]:
                    try:
                        error_data = await response.json()
                        print(f"      ❌ {error_data}")
                    except:
                        error_text = await response.text()
                        print(f"      ❌ {error_text}")
                else:
                    print(f"      ⚠️ Status {response.status}")
                    
        except Exception as e:
            print(f"      ❌ Exception: {e}")


async def main():
    """Main function."""
    print("🔍 Thermacell Node Details Testing")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tester = NodeDetailsTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            await tester.test_node_details()
        else:
            print("   ❌ Authentication failed")
    
    print("\n✅ Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())