#!/usr/bin/env python3
"""
Analyze the Thermacell API response format and extract necessary data.
"""
import asyncio
import base64
import json
from secrets import THERMACELL_API_BASE_URL, THERMACELL_PASSWORD, THERMACELL_USERNAME

import aiohttp


def decode_jwt_payload(jwt_token):
    """Decode JWT token payload without verification."""
    try:
        # JWT tokens have 3 parts separated by dots
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None

        # Decode the payload (middle part)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))

        return decoded_json
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None


async def analyze_authentication_response():
    """Analyze the authentication response structure."""
    print("🔍 Analyzing Thermacell Authentication Response")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        url = f"{THERMACELL_API_BASE_URL.rstrip('/')}/v1/login2"
        payload = {
            "user_name": THERMACELL_USERNAME,
            "password": THERMACELL_PASSWORD
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                auth_data = await response.json()

                print("📋 Authentication Response Structure:")
                print(json.dumps(auth_data, indent=2))
                print()

                # Extract tokens
                access_token = auth_data.get("accesstoken")
                id_token = auth_data.get("idtoken")

                if access_token:
                    print("🔑 Access Token Analysis:")
                    access_payload = decode_jwt_payload(access_token)
                    if access_payload:
                        print(json.dumps(access_payload, indent=2))
                        print(f"Username from access token: {access_payload.get('username')}")
                        print()

                if id_token:
                    print("🆔 ID Token Analysis:")
                    id_payload = decode_jwt_payload(id_token)
                    if id_payload:
                        print(json.dumps(id_payload, indent=2))
                        print(f"User ID from ID token: {id_payload.get('custom:user_id')}")
                        print(f"Email from ID token: {id_payload.get('email')}")
                        print()

                # Test the get nodes endpoint with extracted user_id
                if access_token and id_token:
                    id_payload = decode_jwt_payload(id_token)
                    user_id = id_payload.get('custom:user_id') if id_payload else None

                    if user_id:
                        print(f"🏠 Testing Get Nodes with extracted user_id: {user_id}")
                        await test_get_nodes(session, access_token, user_id)

            else:
                print(f"❌ Authentication failed: {response.status}")
                print(await response.text())


async def test_get_nodes(session, access_token, user_id):
    """Test the get nodes endpoint with proper user_id."""
    url = f"{THERMACELL_API_BASE_URL.rstrip('/')}/v1/user2/nodes?user_id={user_id}"
    headers = {"Authorization": access_token}

    print(f"📤 Request URL: {url}")
    print(f"📤 Request headers: Authorization: {access_token[:20]}...")

    try:
        async with session.get(url, headers=headers) as response:
            print(f"📥 Response status: {response.status}")

            if response.status == 200:
                data = await response.json()
                print("📥 Response structure:")
                print(json.dumps(data, indent=2))

                nodes = data.get("node_details", [])
                print(f"\n✅ Found {len(nodes)} nodes")

                # Test node status for first node
                if nodes:
                    first_node = nodes[0]
                    node_id = first_node.get('id')
                    if node_id:
                        await test_node_status(session, access_token, node_id)
            else:
                print(f"❌ Get nodes failed: {response.status}")
                error_text = await response.text()
                print(f"Error response: {error_text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")


async def test_node_status(session, access_token, node_id):
    """Test the node status endpoint."""
    url = f"{THERMACELL_API_BASE_URL.rstrip('/')}/v1/user2/nodes/status?nodeid={node_id}"
    headers = {"Authorization": access_token}

    print(f"\n📊 Testing Node Status for {node_id}")
    print(f"📤 Request URL: {url}")

    try:
        async with session.get(url, headers=headers) as response:
            print(f"📥 Response status: {response.status}")

            if response.status == 200:
                data = await response.json()
                print("📥 Node Status Response structure:")
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Get node status failed: {response.status}")
                error_text = await response.text()
                print(f"Error response: {error_text}")

    except Exception as e:
        print(f"❌ Node status request failed: {e}")


if __name__ == "__main__":
    asyncio.run(analyze_authentication_response())
