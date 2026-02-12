#!/usr/bin/env python3
"""
Test script to verify OpenDOSM API integration fix
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_opendosm_integration():
    """Test OpenDOSM integration endpoints"""
    
    print("🧪 Testing OpenDOSM PriceCatcher Integration")
    print(f"Test started at: {datetime.now()}")
    print("="*60)
    
    # Test 1: Basic health check
    print("\n1️⃣ Testing basic server health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure to run: cd backend && uvicorn app.main:app --reload")
        return
    
    # Test 2: OpenDOSM status
    print("\n2️⃣ Testing OpenDOSM API status...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/opendosm/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OpenDOSM status endpoint works")
            print(f"   API Status: {data.get('api_integration', {}).get('status', 'unknown')}")
        else:
            print(f"❌ OpenDOSM status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenDOSM status error: {e}")
    
    # Test 3: Test OpenDOSM connection
    print("\n3️⃣ Testing direct OpenDOSM connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/opendosm/test")
        if response.status_code == 200:
            data = response.json()
            connection_status = data.get('connection_test', {}).get('status', 'unknown')
            print(f"✅ OpenDOSM connection test: {connection_status}")
            
            if connection_status == 'success':
                print("   🎉 OpenDOSM API is working!")
                data_test = data.get('data_test', {})
                print(f"   📊 Transactions available: {data_test.get('transactions_available', False)}")
                print(f"   🏪 Premises available: {data_test.get('premises_available', False)}")
                print(f"   🛒 Items available: {data_test.get('items_available', False)}")
            else:
                print(f"   ❌ Connection failed: {data.get('connection_test', {}).get('error', 'unknown')}")
        else:
            print(f"❌ OpenDOSM test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenDOSM test error: {e}")
    
    # Test 4: Test grocery price comparison
    print("\n4️⃣ Testing grocery price comparison...")
    try:
        test_data = {
            "ingredients": ["rice", "chicken"],
            "location": "Selangor"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/grocery/compare",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            stores = data.get('stores', [])
            print(f"✅ Grocery comparison works! Found {len(stores)} stores")
            
            if stores:
                print("   📊 Sample store data:")
                for i, store in enumerate(stores[:2]):  # Show first 2 stores
                    print(f"   {i+1}. {store.get('premise_name', 'Unknown')} - RM{store.get('total_cost', 0):.2f}")
            else:
                print("   📝 No stores found (using mock/fallback data)")
        else:
            print(f"❌ Grocery comparison failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Grocery comparison error: {e}")
    
    # Test 5: Manual data refresh
    print("\n5️⃣ Testing manual data refresh...")
    try:
        response = requests.post(f"{BASE_URL}/api/admin/opendosm/refresh")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manual refresh: {data.get('message', 'completed')}")
        else:
            print(f"❌ Manual refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual refresh error: {e}")
    
    print(f"\n🏁 Test completed at: {datetime.now()}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_opendosm_integration())