#!/usr/bin/env python3
"""
Final API validation using direct aiohttp without Home Assistant dependencies.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class ThermacellAPITester:
    """Direct API tester without Home Assistant dependencies."""
    
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
        """Authenticate with fixed JWT parsing."""
        try:
            url = f"{self.base_url}/v1/login2"
            data = {
                "user_name": self.username,
                "password": self.password,
            }

            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    
                    # Extract access token
                    self.access_token = auth_data.get("accesstoken")
                    
                    # Extract user ID from ID token
                    id_token = auth_data.get("idtoken")
                    if id_token:
                        id_payload = self._decode_jwt_payload(id_token)
                        if id_payload:
                            self.user_id = id_payload.get("custom:user_id")
                    
                    return self.access_token is not None and self.user_id is not None
                else:
                    error_text = await response.text()
                    print(f"Authentication failed with status {response.status}: {error_text}")
                    return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    async def test_endpoints(self):
        """Test various API endpoints."""
        if not self.access_token:
            print("❌ No access token available")
            return
        
        headers = {"Authorization": self.access_token}
        
        # Test node endpoints
        node_endpoints = [
            f"/v1/user/nodes?user_id={self.user_id}",
            f"/v1/user/nodes",
            f"/v1/user2/nodes",
            f"/v1/user2/nodes?user_id={self.user_id}",
            "/v1/nodes",
        ]
        
        print("🏠 Testing Node Endpoints:")
        for endpoint in node_endpoints:
            await self._test_endpoint("GET", endpoint, headers)
        
        # Test other endpoints  
        other_endpoints = [
            "/v1/user",
            "/v1/user/info", 
            "/v1/user/profile",
            "/v1/me",
        ]
        
        print("\n👤 Testing User Endpoints:")
        for endpoint in other_endpoints:
            await self._test_endpoint("GET", endpoint, headers)
    
    async def _test_endpoint(self, method: str, endpoint: str, headers: dict):
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        print(f"   {method} {endpoint}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.request(method, url, headers=headers, timeout=timeout) as response:
                print(f"     Status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"     ✅ SUCCESS!")
                        print(f"     Response type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"     Keys: {list(data.keys())}")
                            # Print first few characters of response for inspection
                            response_str = json.dumps(data, indent=2)
                            if len(response_str) > 500:
                                print(f"     Sample: {response_str[:500]}...")
                            else:
                                print(f"     Data: {response_str}")
                        elif isinstance(data, list):
                            print(f"     List length: {len(data)}")
                            if data:
                                print(f"     First item type: {type(data[0])}")
                                if isinstance(data[0], dict):
                                    print(f"     First item keys: {list(data[0].keys())}")
                    except json.JSONDecodeError:
                        text = await response.text()
                        print(f"     ✅ SUCCESS! (non-JSON)")
                        print(f"     Response: {text[:200]}...")
                        
                elif response.status in [400, 401, 403, 404, 405]:
                    try:
                        error_data = await response.json()
                        print(f"     ❌ Error: {error_data}")
                    except:
                        error_text = await response.text()
                        print(f"     ❌ Error: {error_text}")
                else:
                    print(f"     ⚠️ Unexpected status")
                    
        except asyncio.TimeoutError:
            print(f"     ⏱️ Timeout")
        except Exception as e:
            print(f"     ❌ Exception: {e}")


async def main():
    """Main test function."""
    print("🚀 Final Thermacell LIV API Validation")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print(f"Base URL: {THERMACELL_API_BASE_URL}")
    print()
    
    async with aiohttp.ClientSession() as session:
        tester = ThermacellAPITester()
        tester.session = session
        
        # Test authentication
        print("1️⃣ Testing Authentication...")
        auth_success = await tester.authenticate()
        
        if auth_success:
            print(f"   ✅ Authentication successful!")
            print(f"   Access token: {tester.access_token[:30]}...")
            print(f"   User ID: {tester.user_id}")
            print()
            
            # Test endpoints
            print("2️⃣ Testing API Endpoints...")
            await tester.test_endpoints()
            
        else:
            print("   ❌ Authentication failed - cannot test endpoints")
        
        print()
        print("✅ Validation completed!")


if __name__ == "__main__":
    asyncio.run(main())