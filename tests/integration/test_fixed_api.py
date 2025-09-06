#!/usr/bin/env python3
"""
Test the fixed API client with real endpoints.
"""
import asyncio
import json
import aiohttp
from unittest.mock import MagicMock

from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI


async def test_fixed_api():
    """Test the fixed API client."""
    print("🔧 Testing Fixed Thermacell LIV API Client")
    print("=" * 60)
    print(f"Username: {THERMACELL_USERNAME}")
    print(f"API Base URL: {THERMACELL_API_BASE_URL}")
    print()
    
    # Create a mock Home Assistant instance
    mock_hass = MagicMock()
    
    # Create API client
    api = ThermacellLivAPI(mock_hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    
    try:
        # Test 1: Authentication with fixed JWT parsing
        print("1️⃣ Testing Fixed Authentication...")
        auth_success = await api.authenticate()
        print(f"   Authentication result: {auth_success}")
        
        if auth_success:
            print(f"   Access token: {api.access_token[:20]}..." if api.access_token else "   No access token")
            print(f"   User ID: {api.user_id}")
        else:
            print("   ❌ Authentication failed!")
            return
        
        print()
        
        # Test 2: Try different node endpoints
        print("2️⃣ Testing Different Node Endpoints...")
        
        # Try endpoint variations manually to find the working one
        endpoints_to_try = [
            f"/v1/user/nodes?user_id={api.user_id}",
            f"/v1/user/nodes", 
            f"/v1/user2/nodes",
            f"/v1/user2/nodes?user_id={api.user_id}",
            "/v1/nodes",
            "/user/nodes",
            "/nodes"
        ]
        
        headers = {"Authorization": api.access_token}
        working_endpoint = None
        
        for endpoint in endpoints_to_try:
            url = f"{api.base_url}{endpoint}"
            print(f"   Trying: {endpoint}")
            
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with api.session.get(url, headers=headers, timeout=timeout) as response:
                    print(f"     Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"     ✅ SUCCESS! Response: {json.dumps(data, indent=6)}")
                        working_endpoint = endpoint
                        break
                    elif response.status in [400, 401, 403, 404]:
                        error_text = await response.text()
                        print(f"     ❌ Error: {error_text}")
                    else:
                        print(f"     ⚠️  Unexpected status: {response.status}")
                        
            except Exception as e:
                print(f"     ❌ Exception: {e}")
        
        if working_endpoint:
            print(f"\n✅ Working endpoint found: {working_endpoint}")
            
            # Test node status if we have nodes
            # For now, we'll skip since we need actual node data
        else:
            print("\n⚠️  No working node endpoint found. This could mean:")
            print("   - No devices are registered to this account")
            print("   - Different API authentication scope needed")
            print("   - API has different endpoint structure")
        
        print()
        
        # Test 3: Check what other endpoints work
        print("3️⃣ Testing Other Endpoints...")
        
        other_endpoints = [
            "/v1/user/info",
            "/v1/user/profile",
            "/v1/user/devices",
            "/v1/user",
            "/v1/me",
            "/me",
            "/user"
        ]
        
        for endpoint in other_endpoints:
            url = f"{api.base_url}{endpoint}"
            print(f"   Trying: {endpoint}")
            
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with api.session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"     ✅ SUCCESS! Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    else:
                        print(f"     Status: {response.status}")
                        
            except Exception as e:
                print(f"     Exception: {e}")
        
        print()
        print("✅ API testing completed!")
        
    except Exception as e:
        print(f"❌ Error during API testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up session if it exists
        if hasattr(api, 'session') and api.session:
            await api.session.close()


if __name__ == "__main__":
    asyncio.run(test_fixed_api())