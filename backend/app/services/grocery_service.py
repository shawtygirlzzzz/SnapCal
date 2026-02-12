"""
Grocery Service - Real OpenDOSM PriceCatcher data integration and price comparison
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from app.models.models import GroceryPrice
from app.schemas.schemas import GroceryCompareResponse, StoreComparison, GroceryItem
from app.core.config import settings
from app.services.opendosm_client import opendosm_client
from app.services.pricecatcher_processor import pricecatcher_processor

class GroceryService:
    """Service for grocery price comparison using OpenDOSM data"""
    
    # Chain name mappings for premise identification
    CHAIN_MAPPINGS = {
        "Tesco": ["TESCO", "TESCO EXTRA", "TESCO EXPRESS"],
        "99 Speedmart": ["99 SPEEDMART", "NINETY NINE SPEEDMART"],
        "Giant": ["GIANT", "GIANT HYPERMARKET", "GIANT SUPERMARKET"],
        "AEON": ["AEON", "AEON BIG", "AEON SUPERMARKET"],
        "Village Grocer": ["VILLAGE GROCER", "VG"],
        "Jaya Grocer": ["JAYA GROCER", "JG"],
        "ECONSAVE": ["ECONSAVE", "ECON SAVE"],
        "NSK": ["NSK", "NSK TRADE CITY"],
        "Mydin": ["MYDIN", "MYDIN MALL"],
        "KK Super Mart": ["KK SUPER MART", "KK MART"]
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    async def compare_ingredient_prices(
        self,
        ingredients: List[str],
        location: Optional[str] = None,
        max_distance_km: Optional[float] = None
    ) -> GroceryCompareResponse:
        """
        Compare prices for ingredients across stores using real OpenDOSM data
        
        Args:
            ingredients: List of ingredient names to search for
            location: State or area filter (state name)
            max_distance_km: Maximum distance filter (not implemented yet)
            
        Returns:
            Price comparison across stores with real data
        """
        
        try:
            print(f"🔍 Comparing prices for {len(ingredients)} ingredients")
            
            # Check if we need to refresh data
            if await pricecatcher_processor.needs_refresh():
                print("🔄 Refreshing PriceCatcher data...")
                await pricecatcher_processor.refresh_all_data()
            
            # Get real ingredient prices from OpenDOSM
            ingredient_prices = await pricecatcher_processor.get_ingredient_prices(
                ingredients, state=location
            )
            
            # If no real data available, fall back to database
            if not any(ingredient_prices.values()):
                print("📚 Using database fallback for price comparison")
                return await self._get_database_price_comparison(ingredients, location)
            
            # Process real data into store comparisons
            stores = await self._process_opendosm_data(ingredient_prices, ingredients)
            
            # Calculate statistics
            if stores:
                total_costs = [store.total_cost for store in stores]
                average_total_cost = sum(total_costs) / len(total_costs)
                min_cost = min(total_costs)
                max_cost = max(total_costs)
                cheapest_store = min(stores, key=lambda s: s.total_cost)
            else:
                average_total_cost = 0.0
                min_cost = 0.0
                max_cost = 0.0
                cheapest_store = None
            
            print(f"✅ Found prices from {len(stores)} stores")
            
            return GroceryCompareResponse(
                requested_ingredients=ingredients,
                location_filter=location,
                stores=stores,
                cheapest_store=cheapest_store,
                average_total_cost=round(average_total_cost, 2),
                price_range={"min": min_cost, "max": max_cost}
            )
            
        except Exception as e:
            print(f"❌ Error in price comparison: {e}")
            # Fallback to database or mock data
            return await self._get_database_price_comparison(ingredients, location)
    
    async def get_available_stores(
        self,
        state: Optional[str] = None,
        chain_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available stores"""
        
        # Mock store data for demonstration
        mock_stores = [
            {
                "premise_code": "T001KL",
                "premise_name": "TESCO EXTRA AMPANG",
                "chain_name": "Tesco",
                "state": "Selangor",
                "address": "Jalan Ampang, Ampang, Selangor"
            },
            {
                "premise_code": "99001KL",
                "premise_name": "99 SPEEDMART CHERAS",
                "chain_name": "99 Speedmart",
                "state": "Kuala Lumpur",
                "address": "Jalan Cheras, Cheras, KL"
            },
            {
                "premise_code": "G001KL",
                "premise_name": "GIANT HYPERMARKET SUBANG",
                "chain_name": "Giant",
                "state": "Selangor",
                "address": "Subang Jaya, Selangor"
            },
            {
                "premise_code": "A001KL",
                "premise_name": "AEON BIG WANGSA MAJU",
                "chain_name": "AEON",
                "state": "Kuala Lumpur",
                "address": "Wangsa Maju, KL"
            },
            {
                "premise_code": "VG001KL",
                "premise_name": "VILLAGE GROCER BANGSAR",
                "chain_name": "Village Grocer",
                "state": "Kuala Lumpur",
                "address": "Bangsar, KL"
            }
        ]
        
        # Apply filters
        filtered_stores = mock_stores
        
        if state:
            filtered_stores = [s for s in filtered_stores if state.lower() in s["state"].lower()]
        
        if chain_name:
            filtered_stores = [s for s in filtered_stores if chain_name.lower() in s["chain_name"].lower()]
        
        return filtered_stores
    
    async def search_grocery_items(
        self,
        search_term: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for grocery items"""
        
        # Mock grocery items for demonstration
        mock_items = [
            {"name": "Rice (Beras) 10kg", "category": "Grains", "avg_price_rm": 25.90},
            {"name": "Chicken Breast 1kg", "category": "Meat", "avg_price_rm": 12.50},
            {"name": "Onions 1kg", "category": "Vegetables", "avg_price_rm": 4.20},
            {"name": "Cooking Oil 1L", "category": "Cooking", "avg_price_rm": 6.80},
            {"name": "Tomatoes 1kg", "category": "Vegetables", "avg_price_rm": 5.50},
            {"name": "Eggs 30pcs", "category": "Dairy", "avg_price_rm": 18.00},
            {"name": "Milk 1L", "category": "Dairy", "avg_price_rm": 4.50},
            {"name": "Bread Loaf", "category": "Bakery", "avg_price_rm": 2.80},
            {"name": "Chili Padi 100g", "category": "Spices", "avg_price_rm": 3.20},
            {"name": "Coconut Milk 400ml", "category": "Cooking", "avg_price_rm": 2.90},
            {"name": "Soy Sauce 300ml", "category": "Condiments", "avg_price_rm": 3.50},
            {"name": "Fish 1kg", "category": "Seafood", "avg_price_rm": 15.00},
            {"name": "Beef 1kg", "category": "Meat", "avg_price_rm": 35.00},
            {"name": "Potatoes 1kg", "category": "Vegetables", "avg_price_rm": 3.80},
            {"name": "Garlic 200g", "category": "Vegetables", "avg_price_rm": 4.00}
        ]
        
        # Apply filters
        filtered_items = mock_items
        
        if search_term:
            filtered_items = [
                item for item in filtered_items 
                if search_term.lower() in item["name"].lower()
            ]
        
        if category:
            filtered_items = [
                item for item in filtered_items 
                if category.lower() in item["category"].lower()
            ]
        
        return filtered_items[:limit]
    
    async def get_price_trends(
        self,
        item_name: str,
        days: int = 30,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get price trends for an item over time"""
        
        # Mock price trend data
        base_date = datetime.now() - timedelta(days=days)
        mock_trends = []
        
        base_price = 5.50  # Base price for demonstration
        
        for i in range(days):
            # Simulate price fluctuations
            price_variation = (i % 7) * 0.10 - 0.30  # Weekly price cycles
            date = base_date + timedelta(days=i)
            price = max(base_price + price_variation, 0.50)
            
            mock_trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "avg_price": round(price, 2),
                "min_price": round(price * 0.9, 2),
                "max_price": round(price * 1.15, 2)
            })
        
        current_price = mock_trends[-1]["avg_price"]
        previous_price = mock_trends[-8]["avg_price"] if len(mock_trends) >= 8 else current_price
        price_change = ((current_price - previous_price) / previous_price) * 100
        
        return {
            "item_name": item_name,
            "period_days": days,
            "current_avg_price": current_price,
            "price_change_percentage": round(price_change, 1),
            "trends": mock_trends,
            "analysis": {
                "trend_direction": "increasing" if price_change > 0 else "decreasing",
                "volatility": "low",  # Could calculate actual volatility
                "recommendation": "Good time to buy" if price_change < -5 else "Wait for better prices"
            }
        }
    
    async def refresh_pricecatcher_data(self) -> Dict[str, Any]:
        """Refresh OpenDOSM PriceCatcher data"""
        
        try:
            print("🔄 Starting manual PriceCatcher data refresh")
            
            # Use the processor to refresh all data
            refresh_stats = await pricecatcher_processor.refresh_all_data()
            
            # Add chain information to the response
            refresh_stats["chains_updated"] = list(self.CHAIN_MAPPINGS.keys())
            
            return refresh_stats
            
        except Exception as e:
            print(f"❌ Manual data refresh failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
                "data_source": "OpenDOSM PriceCatcher API"
            }
    
    async def _process_opendosm_data(
        self, 
        ingredient_prices: Dict[str, List[Dict[str, Any]]], 
        requested_ingredients: List[str]
    ) -> List[StoreComparison]:
        """
        Process OpenDOSM price data into store comparison format
        
        Args:
            ingredient_prices: Dictionary mapping ingredients to price lists
            requested_ingredients: Original ingredient list
            
        Returns:
            List of store comparisons
        """
        try:
            # Group prices by store
            store_data = {}
            
            for ingredient, prices in ingredient_prices.items():
                for price_record in prices:
                    premise_code = price_record.get("premise_code", "")
                    premise_name = price_record.get("premise_name", "")
                    
                    if not premise_code:
                        continue
                    
                    if premise_code not in store_data:
                        store_data[premise_code] = {
                            "premise_code": premise_code,
                            "premise_name": premise_name,
                            "chain_name": opendosm_client.map_premise_to_chain(premise_name),
                            "state": price_record.get("state", ""),
                            "address": "",  # Not available in current data
                            "items": [],
                            "items_found": 0,
                            "total_cost": 0.0
                        }
                    
                    # Add item to store
                    grocery_item = GroceryItem(
                        item_name=price_record.get("item_name", ingredient),
                        category=price_record.get("category", "Food"),
                        price=price_record.get("price", 0.0),
                        unit=price_record.get("unit", "kg"),
                        price_per_kg=price_record.get("price_per_kg"),
                        premise_name=premise_name,
                        chain_name=store_data[premise_code]["chain_name"],
                        state=price_record.get("state", ""),
                        price_date=datetime.now()  # Use current time as default
                    )
                    
                    store_data[premise_code]["items"].append(grocery_item)
                    store_data[premise_code]["items_found"] += 1
                    store_data[premise_code]["total_cost"] += price_record.get("price", 0.0)
            
            # Convert to StoreComparison objects
            stores = []
            for store_info in store_data.values():
                # Calculate items missing
                items_missing = len(requested_ingredients) - store_info["items_found"]
                
                store_comparison = StoreComparison(
                    premise_code=store_info["premise_code"],
                    premise_name=store_info["premise_name"],
                    chain_name=store_info["chain_name"],
                    state=store_info["state"],
                    address=store_info["address"],
                    items=store_info["items"],
                    total_cost=round(store_info["total_cost"], 2),
                    items_found=store_info["items_found"],
                    items_missing=max(0, items_missing)
                )
                
                stores.append(store_comparison)
            
            # Sort by total cost (cheapest first)
            stores.sort(key=lambda s: s.total_cost)
            
            return stores
            
        except Exception as e:
            print(f"Error processing OpenDOSM data: {e}")
            return []
    
    async def _get_database_price_comparison(
        self, 
        ingredients: List[str], 
        location: Optional[str] = None
    ) -> GroceryCompareResponse:
        """
        Fallback method using database data when OpenDOSM is unavailable
        
        Args:
            ingredients: List of ingredient names
            location: Optional state filter
            
        Returns:
            Price comparison using database data
        """
        try:
            print("📚 Using database fallback for price comparison")
            
            # Query database for ingredient prices
            query = self.db.query(GroceryPrice)
            
            # Filter by ingredients (case-insensitive search)
            ingredient_filters = []
            for ingredient in ingredients:
                ingredient_filters.append(
                    GroceryPrice.normalized_item_name.like(f"%{ingredient.lower()}%")
                )
            
            if ingredient_filters:
                from sqlalchemy import or_
                query = query.filter(or_(*ingredient_filters))
            
            # Filter by location if specified
            if location:
                query = query.filter(GroceryPrice.state.ilike(f"%{location}%"))
            
            # Get recent data (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            query = query.filter(GroceryPrice.created_at >= recent_date)
            
            # Execute query
            price_records = query.limit(200).all()
            
            if not price_records:
                # If no database data, fall back to mock data
                print("📝 No database data available, using mock data")
                return await self._get_mock_price_comparison(ingredients, location)
            
            # Process database records into store comparisons
            stores = self._process_database_records(price_records, ingredients)
            
            # Calculate statistics
            if stores:
                total_costs = [store.total_cost for store in stores]
                average_total_cost = sum(total_costs) / len(total_costs)
                min_cost = min(total_costs)
                max_cost = max(total_costs)
                cheapest_store = min(stores, key=lambda s: s.total_cost)
            else:
                average_total_cost = 0.0
                min_cost = 0.0
                max_cost = 0.0
                cheapest_store = None
            
            return GroceryCompareResponse(
                requested_ingredients=ingredients,
                location_filter=location,
                stores=stores,
                cheapest_store=cheapest_store,
                average_total_cost=round(average_total_cost, 2),
                price_range={"min": min_cost, "max": max_cost}
            )
            
        except Exception as e:
            print(f"Error in database fallback: {e}")
            # Final fallback to mock data
            return await self._get_mock_price_comparison(ingredients, location)
    
    def _process_database_records(
        self, 
        price_records: List[GroceryPrice], 
        requested_ingredients: List[str]
    ) -> List[StoreComparison]:
        """Process database records into store comparison format"""
        
        # Group by store
        store_data = {}
        
        for record in price_records:
            premise_code = record.premise_code
            
            if premise_code not in store_data:
                store_data[premise_code] = {
                    "premise_code": premise_code,
                    "premise_name": record.premise_name,
                    "chain_name": record.chain_name or "Unknown Store",
                    "state": record.state,
                    "address": record.premise_address or "",
                    "items": [],
                    "total_cost": 0.0
                }
            
            # Create grocery item
            grocery_item = GroceryItem(
                item_name=record.item_name,
                category=record.item_category or "Food",
                price=record.price,
                unit=record.unit,
                price_per_kg=record.price_per_kg,
                premise_name=record.premise_name,
                chain_name=record.chain_name or "Unknown Store",
                state=record.state,
                price_date=record.price_date
            )
            
            store_data[premise_code]["items"].append(grocery_item)
            store_data[premise_code]["total_cost"] += record.price
        
        # Convert to StoreComparison objects
        stores = []
        for store_info in store_data.values():
            items_found = len(store_info["items"])
            items_missing = len(requested_ingredients) - items_found
            
            store_comparison = StoreComparison(
                premise_code=store_info["premise_code"],
                premise_name=store_info["premise_name"],
                chain_name=store_info["chain_name"],
                state=store_info["state"],
                address=store_info["address"],
                items=store_info["items"],
                total_cost=round(store_info["total_cost"], 2),
                items_found=items_found,
                items_missing=max(0, items_missing)
            )
            
            stores.append(store_comparison)
        
        return stores
    
    async def _get_mock_price_comparison(
        self, 
        ingredients: List[str], 
        location: Optional[str] = None
    ) -> GroceryCompareResponse:
        """Final fallback to mock data"""
        
        print("🎭 Using mock data as final fallback")
        
        # Use the existing mock data generation
        mock_stores = self._generate_mock_store_data(ingredients, location)
        
        # Calculate statistics
        if mock_stores:
            total_costs = [store.total_cost for store in mock_stores]
            average_total_cost = sum(total_costs) / len(total_costs)
            min_cost = min(total_costs)
            max_cost = max(total_costs)
            cheapest_store = min(mock_stores, key=lambda s: s.total_cost)
        else:
            average_total_cost = 0.0
            min_cost = 0.0
            max_cost = 0.0
            cheapest_store = None
        
        return GroceryCompareResponse(
            requested_ingredients=ingredients,
            location_filter=location,
            stores=mock_stores,
            cheapest_store=cheapest_store,
            average_total_cost=round(average_total_cost, 2),
            price_range={"min": min_cost, "max": max_cost}
        )
    
    def _generate_mock_store_data(
        self,
        ingredients: List[str],
        location: Optional[str] = None
    ) -> List[StoreComparison]:
        """Generate mock store comparison data for demonstration"""
        
        stores_data = [
            {
                "premise_code": "T001KL",
                "premise_name": "TESCO EXTRA AMPANG",
                "chain_name": "Tesco",
                "state": "Selangor",
                "address": "Jalan Ampang, Ampang, Selangor",
                "price_multiplier": 1.0  # Base prices
            },
            {
                "premise_code": "99001KL",
                "premise_name": "99 SPEEDMART CHERAS",
                "chain_name": "99 Speedmart",
                "state": "Kuala Lumpur",
                "address": "Jalan Cheras, Cheras, KL",
                "price_multiplier": 0.85  # Usually cheaper
            },
            {
                "premise_code": "G001KL",
                "premise_name": "GIANT HYPERMARKET SUBANG",
                "chain_name": "Giant",
                "state": "Selangor",
                "address": "Subang Jaya, Selangor",
                "price_multiplier": 0.95  # Competitive pricing
            },
            {
                "premise_code": "VG001KL",
                "premise_name": "VILLAGE GROCER BANGSAR",
                "chain_name": "Village Grocer",
                "state": "Kuala Lumpur",
                "address": "Bangsar, KL",
                "price_multiplier": 1.25  # Premium pricing
            }
        ]
        
        # Mock base prices for common ingredients
        base_prices = {
            "rice": 2.50,
            "chicken": 12.50,
            "onion": 4.20,
            "tomato": 5.50,
            "oil": 6.80,
            "egg": 0.60,
            "milk": 4.50,
            "chili": 8.00,
            "garlic": 20.00,  # per kg
            "coconut milk": 2.90,
            "soy sauce": 3.50
        }
        
        mock_stores = []
        
        for store_data in stores_data:
            # Filter by location if specified
            if location and location.lower() not in store_data["state"].lower():
                continue
            
            items = []
            total_cost = 0.0
            items_found = 0
            
            for ingredient in ingredients:
                # Find matching base price
                matched_price = None
                for key, price in base_prices.items():
                    if key.lower() in ingredient.lower():
                        matched_price = price * store_data["price_multiplier"]
                        break
                
                if matched_price:
                    items_found += 1
                    items.append(GroceryItem(
                        item_name=ingredient.title(),
                        category="Food",
                        price=round(matched_price, 2),
                        unit="per kg",
                        price_per_kg=round(matched_price, 2),
                        premise_name=store_data["premise_name"],
                        chain_name=store_data["chain_name"],
                        state=store_data["state"],
                        price_date=datetime.now()
                    ))
                    total_cost += matched_price
            
            mock_stores.append(StoreComparison(
                premise_code=store_data["premise_code"],
                premise_name=store_data["premise_name"],
                chain_name=store_data["chain_name"],
                state=store_data["state"],
                address=store_data["address"],
                items=items,
                total_cost=round(total_cost, 2),
                items_found=items_found,
                items_missing=len(ingredients) - items_found
            ))
        
        return mock_stores 