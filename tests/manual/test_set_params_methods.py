#!/usr/bin/env python3
"""
Test different methods for setting node parameters to find the correct API structure.
"""
import asyncio
import base64
import json
import aiohttp
from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL


class SetParamsMethodTester:
    """Test different methods for setting parameters."""
    
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
                    return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    async def test_different_methods(self, node_id: str):
        """Test different API methods and endpoints for setting parameters."""
        headers = {"Authorization": self.access_token}
        
        # Test different HTTP methods and endpoints
        test_methods = [
            # Method 1: PUT /v1/user/nodes/params (current approach)
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "payload": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
            
            # Method 2: POST /v1/user/nodes/params
            {
                "method": "POST",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "payload": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
            
            # Method 3: PUT with nodeid query parameter
            {
                "method": "PUT", 
                "url": f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}",
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": True
                    }
                }
            },
            
            # Method 4: POST with nodeid query parameter
            {
                "method": "POST",
                "url": f"{self.base_url}/v1/user/nodes/params?nodeid={node_id}",
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": True
                    }
                }
            },
            
            # Method 5: Different payload structure - no nesting
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "LIV Hub": {
                        "Enable Repellers": True
                    }
                }
            },
            
            # Method 6: Try /v1/user2/nodes/params (from docs)
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user2/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "payload": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
            
            # Method 7: Different endpoint pattern
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/nodes/{node_id}/params",
                "payload": {
                    "LIV Hub": {
                        "Enable Repellers": True
                    }
                }
            },
            
            # Method 8: ESP Rainmaker standard format
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "params": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
            
            # Method 9: Try with user_id parameter  
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "user_id": self.user_id,
                    "node_id": node_id,
                    "payload": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
        ]
        
        for i, test_method in enumerate(test_methods, 1):
            print(f"\n🧪 Test {i}: {test_method['method']} {test_method['url'].replace(self.base_url, '')}")
            print(f"   Payload: {json.dumps(test_method['payload'], indent=6)}")
            
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with self.session.request(
                    test_method['method'], 
                    test_method['url'], 
                    json=test_method['payload'], 
                    headers=headers, 
                    timeout=timeout
                ) as response:
                    print(f"   Status: {response.status}")
                    
                    response_text = await response.text()
                    
                    if response.status in [200, 201, 204]:
                        try:
                            response_data = json.loads(response_text)
                            print(f"   ✅ SUCCESS! Response: {json.dumps(response_data, indent=6)}")
                            return test_method  # Return successful method
                        except:
                            print(f"   ✅ SUCCESS! (non-JSON): {response_text}")
                            return test_method
                    else:
                        try:
                            error_data = json.loads(response_text)
                            print(f"   ❌ Error: {json.dumps(error_data, indent=6)}")
                        except:
                            print(f"   ❌ Error: {response_text}")
                
                # Small delay between attempts
                await asyncio.sleep(0.5)
                            
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        return None
    
    async def test_esp_rainmaker_docs(self, node_id: str):
        """Test based on ESP Rainmaker API documentation patterns."""
        headers = {"Authorization": self.access_token}
        
        print(f"\n📖 Testing ESP Rainmaker documented patterns...")
        
        # According to ESP Rainmaker docs, try these patterns:
        rainmaker_tests = [
            # Pattern 1: Standard ESP Rainmaker node parameter update
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    node_id: {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
            
            # Pattern 2: With explicit node_id field
            {
                "method": "PUT",
                "url": f"{self.base_url}/v1/user/nodes/params",
                "payload": {
                    "node_id": node_id,
                    "params": {
                        "LIV Hub": {
                            "Enable Repellers": True
                        }
                    }
                }
            },
        ]
        
        for i, test in enumerate(rainmaker_tests, 1):
            print(f"\n   Rainmaker Pattern {i}: {test['method']} {test['url'].replace(self.base_url, '')}")
            print(f"   Payload: {json.dumps(test['payload'], indent=6)}")
            
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with self.session.request(
                    test['method'], 
                    test['url'], 
                    json=test['payload'], 
                    headers=headers, 
                    timeout=timeout
                ) as response:
                    print(f"   Status: {response.status}")
                    
                    response_text = await response.text()
                    
                    if response.status in [200, 201, 204]:
                        try:
                            response_data = json.loads(response_text)
                            print(f"   ✅ SUCCESS! Response: {json.dumps(response_data, indent=6)}")
                            return test
                        except:
                            print(f"   ✅ SUCCESS! (non-JSON): {response_text}")
                            return test
                    else:
                        try:
                            error_data = json.loads(response_text)
                            print(f"   ❌ Error: {json.dumps(error_data, indent=6)}")
                        except:
                            print(f"   ❌ Error: {response_text}")
                            
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        return None


async def main():
    """Main function to test different parameter setting methods."""
    print("🧪 Thermacell Parameter Setting Method Testing")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        tester = SetParamsMethodTester()
        tester.session = session
        
        print("🔐 Authenticating...")
        if await tester.authenticate():
            print(f"   ✅ Success! User ID: {tester.user_id}")
            
            # Use the first node for testing
            test_node_id = "JM7UVxmMgPUYUhVJVBWEf6"  # From previous test
            
            print(f"\n🎯 Testing parameter setting methods with node: {test_node_id}")
            
            # Test different methods
            successful_method = await tester.test_different_methods(test_node_id)
            
            if not successful_method:
                # Try ESP Rainmaker documented patterns
                successful_method = await tester.test_esp_rainmaker_docs(test_node_id)
            
            if successful_method:
                print(f"\n🎉 Found working method!")
                print(f"   Method: {successful_method['method']}")
                print(f"   URL: {successful_method['url']}")
                print(f"   Payload: {json.dumps(successful_method['payload'], indent=2)}")
            else:
                print(f"\n❌ No working method found. All requests returned errors.")
        else:
            print("   ❌ Authentication failed")
    
    print("\n✅ Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())