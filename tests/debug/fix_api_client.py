#!/usr/bin/env python3
"""
Fix the API client based on the real API response analysis.
"""
import json
import base64


def decode_jwt_payload(jwt_token):
    """Decode JWT token payload without verification."""
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))
        
        return decoded_json
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None


def analyze_auth_response():
    """Analyze what needs to be fixed in the API client."""
    print("🔧 API Client Issues Found:")
    print("=" * 50)
    
    print("1. ✅ Authentication endpoint: `/v1/login2` - CORRECT")
    print("   - Request format: {'user_name': username, 'password': password}")
    print("   - Response contains: accesstoken, idtoken, refreshtoken")
    print()
    
    print("2. ❌ User ID extraction: NEEDS FIXING")
    print("   - Current: expects 'user_id' in auth response")
    print("   - Actual: user_id is in idtoken JWT as 'custom:user_id'")
    print("   - Fix: decode idtoken and extract custom:user_id")
    print()
    
    print("3. ❌ Get nodes endpoint: NEEDS INVESTIGATION") 
    print("   - Current: `/v1/user2/nodes?user_id={user_id}`")
    print("   - Status: Returns 400 Bad Request")
    print("   - Possible fixes:")
    print("     a) Try different API version: /v1/user/nodes")
    print("     b) Try different parameter format")
    print("     c) Check if user has any devices registered")
    print()
    
    print("4. ✅ Headers: CORRECT")
    print("   - Authorization header with access token works")
    print()

def generate_api_client_fixes():
    """Generate the fixes needed for the API client."""
    print("\n🔧 Recommended API Client Fixes:")
    print("=" * 50)
    
    fixes = """
1. Fix authenticate() method in api.py:

async def authenticate(self) -> bool:
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
                _LOGGER.error(f"Authentication failed with status {response.status}: {error_text}")
                return False
    except Exception as e:
        _LOGGER.error(f"Authentication error: {e}")
        return False

def _decode_jwt_payload(self, jwt_token: str) -> dict:
    '''Decode JWT token payload.'''
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

2. Try different get_user_nodes() endpoints:

# Try version 1 (original):
url = f"{self.base_url}/v1/user/nodes?user_id={self.user_id}"

# If that fails, try without user_id parameter:
url = f"{self.base_url}/v1/user/nodes"

# Or try different format:
url = f"{self.base_url}/v1/user2/nodes"
"""
    print(fixes)


if __name__ == "__main__":
    analyze_auth_response()
    generate_api_client_fixes()