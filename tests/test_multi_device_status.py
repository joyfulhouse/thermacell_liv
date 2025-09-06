#!/usr/bin/env python3
"""
Unit tests for multi-device support including offline node handling.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import ThermacellLivCoordinator

class TestMultiDeviceSupport:
    """Test multi-device functionality including offline nodes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock Home Assistant
        self.hass = MagicMock()
        
        # Mock API
        self.api = MagicMock()
        
        # Create coordinator with mocked dependencies
        self.coordinator = ThermacellLivCoordinator.__new__(ThermacellLivCoordinator)
        self.coordinator.hass = self.hass
        self.coordinator.api = self.api
        self.coordinator.data = None
        self.coordinator.last_update_success = True
        
    @pytest.mark.asyncio
    async def test_offline_node_status(self):
        """Test that offline nodes show 'Not Connected' status."""
        # Mock API responses for two nodes - one online, one offline
        self.api.get_user_nodes = AsyncMock(return_value=[
            {
                "id": "online_node",
                "node_name": "Online Hub",
                "params": {
                    "LIV Hub": {
                        "Name": "LIV Hub",
                        "Hub ID": "ONLINE123",
                        "LED Hue": 60,
                        "LED Brightness": 50,
                        "Enable Repellers": True,
                        "System Status": 3,
                        "Error": 0,
                        "Refill Life": 75,
                        "System Runtime": 120
                    }
                }
            },
            {
                "id": "offline_node", 
                "node_name": "Offline Hub",
                "params": {
                    "LIV Hub": {
                        "Name": "LIV Hub",
                        "Hub ID": "OFFLINE456",
                        "LED Hue": 0,
                        "LED Brightness": 100,
                        "Enable Repellers": True,
                        "System Status": 3,
                        "Error": 0,
                        "Refill Life": 85,
                        "System Runtime": 200
                    }
                }
            }
        ])
        
        # Mock status responses - online node connected, offline node disconnected
        async def mock_get_node_status(node_id):
            if node_id == "online_node":
                return {
                    "connectivity": {
                        "connected": True,
                        "timestamp": 1757107867638
                    }
                }
            elif node_id == "offline_node":
                return {
                    "connectivity": {
                        "connected": False,
                        "timestamp": 1757183054832
                    }
                }
            return None
            
        self.api.get_node_status = AsyncMock(side_effect=mock_get_node_status)
        
        # Mock config responses
        async def mock_get_node_config(node_id):
            return {
                "info": {
                    "fw_version": "5.3.2",
                    "model": "thermacell-hub"
                }
            }
            
        self.api.get_node_config = AsyncMock(side_effect=mock_get_node_config)
        
        # Test the data update method
        data = await self.coordinator._async_update_data()
        
        # Verify both nodes are present
        assert len(data) == 2
        assert "online_node" in data
        assert "offline_node" in data
        
        # Verify online node status
        online_node = data["online_node"]
        assert online_node["online"] == True
        assert online_node["name"] == "Online Hub"
        
        online_device = online_node["devices"]["LIV Hub"]
        assert online_device["system_status"] == "Protected"  # System status 3 + connected
        assert online_device["power"] == True  # Enable Repellers is True
        
        # Verify offline node status
        offline_node = data["offline_node"]
        assert offline_node["online"] == False
        assert offline_node["name"] == "Offline Hub"
        
        offline_device = offline_node["devices"]["LIV Hub"]
        assert offline_device["system_status"] == "Not Connected"  # Should override other status
        assert offline_device["power"] == True  # Enable Repellers still True but irrelevant
        
    def test_coordinator_helper_methods(self):
        """Test coordinator helper methods with multi-device data."""
        # Set up mock data with online and offline nodes
        self.coordinator.data = {
            "online_node": {
                "name": "Online Hub",
                "online": True,
                "devices": {
                    "LIV Hub": {
                        "power": True,
                        "system_status": "Protected",
                        "refill_life": 75
                    }
                }
            },
            "offline_node": {
                "name": "Offline Hub", 
                "online": False,
                "devices": {
                    "LIV Hub": {
                        "power": True,
                        "system_status": "Not Connected",
                        "refill_life": 85
                    }
                }
            }
        }
        
        # Test is_node_online method
        assert self.coordinator.is_node_online("online_node") == True
        assert self.coordinator.is_node_online("offline_node") == False
        assert self.coordinator.is_node_online("nonexistent_node") == False
        
        # Test get_node_data method
        online_data = self.coordinator.get_node_data("online_node")
        assert online_data is not None
        assert online_data["name"] == "Online Hub"
        assert online_data["online"] == True
        
        offline_data = self.coordinator.get_node_data("offline_node")
        assert offline_data is not None
        assert offline_data["name"] == "Offline Hub"
        assert offline_data["online"] == False
        
        # Test get_device_data method
        online_device = self.coordinator.get_device_data("online_node", "LIV Hub")
        assert online_device is not None
        assert online_device["system_status"] == "Protected"
        assert online_device["power"] == True
        
        offline_device = self.coordinator.get_device_data("offline_node", "LIV Hub")
        assert offline_device is not None
        assert offline_device["system_status"] == "Not Connected"
        assert offline_device["power"] == True  # Power state preserved but irrelevant
        
    def test_entity_availability_logic(self):
        """Test entity availability logic for multi-device scenario."""
        # Set up coordinator data
        self.coordinator.data = {
            "online_node": {
                "name": "Online Hub",
                "online": True,
                "devices": {"LIV Hub": {"power": True}}
            },
            "offline_node": {
                "name": "Offline Hub",
                "online": False, 
                "devices": {"LIV Hub": {"power": True}}
            }
        }
        
        self.coordinator.last_update_success = True
        
        # Simulate entity availability checks (as entities would do them)
        # Online node entities should be available
        online_available = (
            self.coordinator.last_update_success and 
            self.coordinator.is_node_online("online_node")
        )
        assert online_available == True
        
        # Offline node entities should be unavailable  
        offline_available = (
            self.coordinator.last_update_success and
            self.coordinator.is_node_online("offline_node") 
        )
        assert offline_available == False


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio
    
    test = TestMultiDeviceSupport()
    test.setup_method()
    
    print("🧪 Running Multi-Device Tests")
    print("=" * 50)
    
    # Test offline node status
    print("\n1. Testing offline node status...")
    try:
        asyncio.run(test.test_offline_node_status())
        print("✅ Offline node status test passed")
    except Exception as e:
        print(f"❌ Offline node status test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test coordinator methods
    print("\n2. Testing coordinator helper methods...")
    try:
        test.test_coordinator_helper_methods()
        print("✅ Coordinator helper methods test passed")
    except Exception as e:
        print(f"❌ Coordinator helper methods test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test entity availability
    print("\n3. Testing entity availability logic...")
    try:
        test.test_entity_availability_logic()
        print("✅ Entity availability logic test passed")
    except Exception as e:
        print(f"❌ Entity availability logic test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Multi-device tests completed!")