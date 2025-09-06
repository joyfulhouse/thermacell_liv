#!/usr/bin/env python3
"""
Test script to validate Thermacell LIV API endpoints with real credentials.
This script will test the actual API calls and verify request/response formats.
"""
import asyncio
import json
from unittest.mock import MagicMock

from secrets import THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL
from api import ThermacellLivAPI


async def test_real_api():
    """Test the real Thermacell LIV API endpoints."""
    print("🔧 Testing Thermacell LIV API with real credentials...")
    print(f"Username: {THERMACELL_USERNAME}")
    print(f"API Base URL: {THERMACELL_API_BASE_URL}")
    print("-" * 60)
    
    # Create a mock Home Assistant instance
    mock_hass = MagicMock()
    
    # Create API client
    api = ThermacellLivAPI(mock_hass, THERMACELL_USERNAME, THERMACELL_PASSWORD, THERMACELL_API_BASE_URL)
    
    try:
        # Test 1: Authentication
        print("1️⃣ Testing authentication...")
        auth_success = await api.authenticate()
        print(f"   Authentication result: {auth_success}")
        
        if auth_success:
            print(f"   Access token: {api.access_token[:20]}..." if api.access_token else "   No access token")
            print(f"   User ID: {api.user_id}")
        else:
            print("   ❌ Authentication failed!")
            return
        
        print()
        
        # Test 2: Get user nodes
        print("2️⃣ Testing get user nodes...")
        nodes = await api.get_user_nodes()
        print(f"   Found {len(nodes)} nodes")
        
        if nodes:
            print("   Node details:")
            for i, node in enumerate(nodes):
                print(f"     Node {i+1}:")
                print(f"       ID: {node.get('id', 'N/A')}")
                print(f"       Name: {node.get('node_name', 'N/A')}")
                print(f"       Type: {node.get('type', 'N/A')}")
                print(f"       Keys: {list(node.keys())}")
        else:
            print("   ⚠️  No nodes found")
            return
        
        print()
        
        # Test 3: Get node status for first node
        if nodes:
            first_node = nodes[0]
            node_id = first_node.get('id')
            
            if node_id:
                print(f"3️⃣ Testing get node status for node: {node_id}")
                status = await api.get_node_status(node_id)
                
                if status:
                    print("   Status data:")
                    print(f"     Online: {status.get('online', 'N/A')}")
                    print(f"     Connected: {status.get('connected', 'N/A')}")
                    print(f"     Keys: {list(status.keys())}")
                    
                    # Look for device parameters
                    params = status.get('params', {})
                    if params:
                        print("   Device parameters:")
                        for device_name, device_params in params.items():
                            print(f"     {device_name}:")
                            for param_name, param_value in device_params.items():
                                print(f"       {param_name}: {param_value}")
                else:
                    print("   ⚠️  No status data received")
            else:
                print("3️⃣ ⚠️  First node has no ID, skipping status test")
        
        print()
        
        # Test 4: Connection test
        print("4️⃣ Testing connection...")
        connection_ok = await api.test_connection()
        print(f"   Connection test result: {connection_ok}")
        
        print()
        print("✅ API testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during API testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up session if it exists
        if hasattr(api, 'session') and api.session:
            await api.session.close()


def main():
    """Run the API test."""
    asyncio.run(test_real_api())


if __name__ == "__main__":
    main()