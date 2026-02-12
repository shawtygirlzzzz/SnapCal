#!/usr/bin/env python3
"""
Test script for OpenDOSM PriceCatcher integration
Run this to verify that the integration is working correctly
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.opendosm_client import opendosm_client
from app.services.pricecatcher_processor import pricecatcher_processor
from app.services.grocery_service import GroceryService
from app.core.database import SessionLocal

async def test_opendosm_integration():
    """
    Comprehensive test of OpenDOSM PriceCatcher integration
    """
    print("🧪 Testing OpenDOSM PriceCatcher Integration")
    print("=" * 50)
    
    # Test 1: API Connection
    print("\n1️⃣ Testing API Connection...")
    try:
        api_info = await opendosm_client.get_latest_data_info()
        print(f"✅ API Status: {api_info.get('api_status', 'unknown')}")
        print(f"   Data Source: {api_info.get('data_source', 'N/A')}")
        print(f"   Total Records: {api_info.get('total_records', 0)}")
        
        if api_info.get("error"):
            print(f"⚠️ API Error: {api_info['error']}")
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        return False
    
    # Test 2: Data Fetching
    print("\n2️⃣ Testing Data Fetching...")
    try:
        # Test transaction data
        transactions = await opendosm_client.get_pricecatcher_transactions(limit=10)
        print(f"✅ Fetched {len(transactions)} transaction records")
        
        # Test premise lookup
        premises = await opendosm_client.get_premise_lookup()
        print(f"✅ Fetched {len(premises)} premise records")
        
        # Test item lookup
        items = await opendosm_client.get_item_lookup()
        print(f"✅ Fetched {len(items)} item records")
        
        if transactions:
            sample_tx = transactions[0]
            print(f"   Sample transaction: {sample_tx.get('item', 'N/A')} - RM {sample_tx.get('price', 0)}")
            
    except Exception as e:
        print(f"❌ Data Fetching Failed: {e}")
        return False
    
    # Test 3: Price Search
    print("\n3️⃣ Testing Price Search...")
    try:
        # Search for common items
        test_items = ["chicken", "rice", "onion"]
        
        for item in test_items:
            prices = await opendosm_client.search_prices_by_item(item, limit=5)
            print(f"✅ Found {len(prices)} prices for '{item}'")
            
            if prices:
                sample_price = prices[0]
                premise = sample_price.get("premise", "Unknown Store")
                price = sample_price.get("price", 0)
                print(f"   Sample: {premise} - RM {price}")
                
    except Exception as e:
        print(f"❌ Price Search Failed: {e}")
        return False
    
    # Test 4: Data Processing
    print("\n4️⃣ Testing Data Processor...")
    try:
        # Test ingredient price fetching
        ingredient_prices = await pricecatcher_processor.get_ingredient_prices(
            ["chicken", "rice"], state="Selangor"
        )
        
        for ingredient, prices in ingredient_prices.items():
            print(f"✅ Processed {len(prices)} prices for '{ingredient}'")
            
        print(f"✅ Data processor working correctly")
        
    except Exception as e:
        print(f"❌ Data Processing Failed: {e}")
        return False
    
    # Test 5: Grocery Service Integration
    print("\n5️⃣ Testing Grocery Service Integration...")
    try:
        db = SessionLocal()
        grocery_service = GroceryService(db)
        
        # Test price comparison
        comparison = await grocery_service.compare_ingredient_prices(
            ingredients=["chicken", "rice"],
            location="Selangor"
        )
        
        print(f"✅ Price comparison returned {len(comparison.stores)} stores")
        print(f"   Average cost: RM {comparison.average_total_cost}")
        
        if comparison.cheapest_store:
            print(f"   Cheapest store: {comparison.cheapest_store.premise_name}")
            print(f"   Cheapest cost: RM {comparison.cheapest_store.total_cost}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Grocery Service Integration Failed: {e}")
        return False
    
    # Test 6: Store Mapping
    print("\n6️⃣ Testing Store Mapping...")
    try:
        test_stores = [
            "TESCO EXTRA AMPANG",
            "99 SPEEDMART CHERAS", 
            "GIANT HYPERMARKET SUBANG",
            "PASAR RAYA AHMAD"
        ]
        
        for store in test_stores:
            mapped_name = opendosm_client.map_premise_to_chain(store)
            print(f"✅ '{store}' → '{mapped_name}'")
            
    except Exception as e:
        print(f"❌ Store Mapping Failed: {e}")
        return False
    
    print("\n🎉 All tests passed! OpenDOSM integration is working correctly.")
    print("   You can now use real Malaysian grocery price data in SnapCal+")
    return True

async def test_specific_ingredient(ingredient_name: str):
    """Test search for a specific ingredient"""
    print(f"\n🔍 Testing specific ingredient: '{ingredient_name}'")
    
    try:
        prices = await opendosm_client.search_prices_by_item(ingredient_name, limit=10)
        print(f"Found {len(prices)} price records for '{ingredient_name}':")
        
        for i, price in enumerate(prices[:5], 1):
            premise = price.get("premise", "Unknown")
            item_price = price.get("price", 0)
            unit = price.get("unit", "")
            state = price.get("state", "")
            
            print(f"  {i}. {premise} ({state}): RM {item_price} per {unit}")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")

def main():
    """Main test function"""
    print("SnapCal+ OpenDOSM PriceCatcher Integration Test")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Test specific ingredient
        ingredient = " ".join(sys.argv[1:])
        asyncio.run(test_specific_ingredient(ingredient))
    else:
        # Run full test suite
        success = asyncio.run(test_opendosm_integration())
        
        if success:
            print("\n✅ Integration test completed successfully!")
            print("💡 Tip: Run 'python test_opendosm_integration.py chicken' to test a specific ingredient")
        else:
            print("\n❌ Integration test failed!")
            print("💡 Check your internet connection and OpenDOSM API availability")
            sys.exit(1)

if __name__ == "__main__":
    main() 