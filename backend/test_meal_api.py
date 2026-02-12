#!/usr/bin/env python3
"""
Test script for Meal Planning API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"\n{'='*60}")
        print(f"{method} {endpoint}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, default=str)[:500]}...")
        else:
            print("❌ FAILED")
            print(f"Error: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Could not connect to {BASE_URL}")
        print("Make sure the backend server is running!")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all meal planning API tests"""
    print(f"🧪 Testing Meal Planning API at {BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    
    # Test 1: Health check
    print("\n🏥 Testing basic connectivity...")
    health_ok = test_endpoint("GET", "/health")
    
    if not health_ok:
        print("\n❌ Cannot connect to backend. Please start the server first:")
        print("cd backend && uvicorn app.main:app --reload")
        return
    
    # Test 2: AI Capabilities
    print("\n🤖 Testing AI capabilities...")
    test_endpoint("GET", "/api/meal/ai/capabilities")
    
    # Test 3: Dietary Options
    print("\n🥗 Testing dietary options...")
    test_endpoint("GET", "/api/meal/dietary-options")
    
    # Test 4: Popular Meals
    print("\n⭐ Testing popular meals...")
    test_endpoint("GET", "/api/meal/popular", params={"limit": 3})
    
    # Test 5: Budget Breakdown
    print("\n💰 Testing budget breakdown...")
    test_endpoint("GET", "/api/meal/budget-breakdown", 
                 params={"budget_rm": 100, "num_people": 4})
    
    # Test 6: Meal Suggestions
    print("\n🍽️ Testing meal suggestions...")
    suggestion_data = {
        "budget_rm": 25.0,
        "num_people": 2,
        "dietary_preferences": ["halal"],
        "exclude_ingredients": []
    }
    test_endpoint("POST", "/api/meal/suggest", data=suggestion_data)
    
    # Test 7: AI Meal Plan (this might take longer)
    print("\n🧠 Testing AI meal plan generation...")
    meal_plan_data = {
        "budget_rm": 150.0,
        "num_people": 4,
        "days": 3,  # Shorter test
        "dietary_preferences": ["halal"],
        "exclude_ingredients": ["beef"],
        "cuisine_preferences": ["Malaysian"]
    }
    test_endpoint("POST", "/api/meal/ai-plan", data=meal_plan_data)
    
    print(f"\n🎉 All tests completed at: {datetime.now()}")

if __name__ == "__main__":
    main()