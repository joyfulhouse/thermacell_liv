#!/usr/bin/env python3
"""
Validate Thermacell LIV API endpoints with real credentials.
This script tests actual API calls and verifies request/response formats.
"""
import asyncio
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class ThermacellAPIValidator:
    """Validator for Thermacell LIV API endpoints."""
    
    def __init__(self):
        self.base_url = THERMACELL_API_BASE_URL.rstrip('/')
        self.username = THERMACELL_USERNAME
        self.password = THERMACELL_PASSWORD
        self.access_token = None
        self.user_id = None
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)  # For testing
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_authentication(self):
        """Test authentication endpoint."""
        print("🔐 Testing Authentication Endpoint")
        print("-" * 50)
        
        url = f"{self.base_url}/v1/login2"
        payload = {
            "user_name": self.username,
            "password": self.password
        }
        
        print(f"📤 Request URL: {url}")
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📥 Response body: {response_text}")
                
                if response.status == 200:
                    try:
                        auth_data = json.loads(response_text)
                        self.access_token = auth_data.get("accesstoken")
                        self.user_id = auth_data.get("user_id")
                        
                        print("✅ Authentication successful!")
                        print(f"   Access token: {self.access_token[:20]}..." if self.access_token else "   No access token")
                        print(f"   User ID: {self.user_id}")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON response: {e}")
                        return False
                else:
                    print(f"❌ Authentication failed with status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication request failed: {e}")
            return False
    
    async def test_get_user_nodes(self):
        """Test get user nodes endpoint."""
        if not self.access_token or not self.user_id:
            print("⚠️  Skipping user nodes test - not authenticated")
            return None
            
        print("\n🏠 Testing Get User Nodes Endpoint")
        print("-" * 50)
        
        url = f"{self.base_url}/v1/user2/nodes?user_id={self.user_id}"
        headers = {"Authorization": self.access_token}
        
        print(f"📤 Request URL: {url}")
        print(f"📤 Request headers: {json.dumps(headers, indent=2)}")
        
        try:
            async with self.session.get(url, headers=headers) as response:
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📥 Response body: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        nodes = data.get("node_details", [])
                        
                        print(f"✅ Found {len(nodes)} nodes")
                        for i, node in enumerate(nodes):
                            print(f"   Node {i+1}:")
                            print(f"     ID: {node.get('id')}")
                            print(f"     Name: {node.get('node_name')}")
                            print(f"     Type: {node.get('type')}")
                            print(f"     All keys: {list(node.keys())}")
                        
                        return nodes
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON response: {e}")
                        return None
                else:
                    print(f"❌ Get user nodes failed with status {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Get user nodes request failed: {e}")
            return None
    
    async def test_get_node_status(self, node_id):
        """Test get node status endpoint."""
        if not self.access_token or not node_id:
            print("⚠️  Skipping node status test - missing auth or node_id")
            return None
            
        print(f"\n📊 Testing Get Node Status Endpoint for {node_id}")
        print("-" * 50)
        
        url = f"{self.base_url}/v1/user2/nodes/status?nodeid={node_id}"
        headers = {"Authorization": self.access_token}
        
        print(f"📤 Request URL: {url}")
        print(f"📤 Request headers: {json.dumps(headers, indent=2)}")
        
        try:
            async with self.session.get(url, headers=headers) as response:
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📥 Response body: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        print("✅ Node status retrieved!")
                        print("   Status structure:")
                        self._print_dict_structure(data, indent=6)
                        
                        return data
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON response: {e}")
                        return None
                else:
                    print(f"❌ Get node status failed with status {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Get node status request failed: {e}")
            return None
    
    async def test_set_node_params(self, node_id):
        """Test set node parameters endpoint."""
        if not self.access_token or not node_id:
            print("⚠️  Skipping set node params test - missing auth or node_id")
            return None
            
        print(f"\n⚙️  Testing Set Node Parameters Endpoint for {node_id}")
        print("-" * 50)
        
        url = f"{self.base_url}/v1/user2/nodes/params"
        headers = {"Authorization": self.access_token}
        
        # Test payload - this is a safe read-only-like operation
        payload = {
            "node_id": node_id,
            "payload": {
                "Device1": {
                    "Power": False  # Safe test - turning off
                }
            }
        }
        
        print(f"📤 Request URL: {url}")
        print(f"📤 Request headers: {json.dumps(headers, indent=2)}")
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        # For safety, let's just print what we would send but not actually send it
        print("⚠️  SAFETY: Not actually sending SET command to avoid changing device state")
        print("   Would send PUT request with the payload above")
        
        return None
    
    def _print_dict_structure(self, data, indent=0):
        """Print dictionary structure recursively."""
        spaces = " " * indent
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{spaces}{key}: {type(value).__name__}")
                    if isinstance(value, dict):
                        self._print_dict_structure(value, indent + 2)
                    elif isinstance(value, list) and value:
                        print(f"{spaces}  (list with {len(value)} items)")
                        if value:
                            print(f"{spaces}  Sample item type: {type(value[0]).__name__}")
                            if isinstance(value[0], dict):
                                self._print_dict_structure(value[0], indent + 4)
                else:
                    print(f"{spaces}{key}: {value}")
        elif isinstance(data, list):
            print(f"{spaces}List with {len(data)} items")


async def main():
    """Main validation function."""
    print("🚀 Thermacell LIV API Validation")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print(f"API Base URL: {THERMACELL_API_BASE_URL}")
    print()
    
    async with ThermacellAPIValidator() as validator:
        # Test authentication
        auth_success = await validator.test_authentication()
        
        if not auth_success:
            print("\n❌ Cannot proceed with other tests - authentication failed")
            return
        
        # Test get user nodes
        nodes = await validator.test_get_user_nodes()
        
        if not nodes:
            print("\n⚠️  No nodes found, skipping node status test")
            return
        
        # Test node status for first node
        first_node = nodes[0] if nodes else None
        if first_node and first_node.get('id'):
            node_id = first_node['id']
            await validator.test_get_node_status(node_id)
            await validator.test_set_node_params(node_id)
        
        print("\n✅ API validation completed!")


if __name__ == "__main__":
    asyncio.run(main())