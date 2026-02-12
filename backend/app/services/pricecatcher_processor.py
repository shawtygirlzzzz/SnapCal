"""
PriceCatcher Data Processor - Transform and cache OpenDOSM data
Handles data cleaning, normalization, and storage for SnapCal+
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.orm import Session

from app.services.opendosm_client import opendosm_client
from app.services.cache_service import cache_service
from app.models.models import GroceryPrice
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class PriceCatcherProcessor:
    """
    Processes and transforms PriceCatcher data for SnapCal+ use
    """
    
    def __init__(self):
        self.cache_ttl = 24 * 3600  # 24 hours cache
        self.last_refresh = None
        
    async def refresh_all_data(self) -> Dict[str, Any]:
        """
        Complete data refresh from OpenDOSM PriceCatcher
        
        Returns:
            Statistics about the refresh operation
        """
        try:
            logger.info("🔄 Starting complete PriceCatcher data refresh")
            start_time = datetime.now()
            
            # Fetch all required data in parallel
            transactions_task = opendosm_client.get_pricecatcher_transactions(limit=5000)
            premises_task = opendosm_client.get_premise_lookup()
            items_task = opendosm_client.get_item_lookup()
            
            # Wait for all requests to complete
            transactions, premises, items = await asyncio.gather(
                transactions_task, premises_task, items_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(transactions, Exception):
                logger.error(f"Failed to fetch transactions: {transactions}")
                transactions = []
            
            if isinstance(premises, Exception):
                logger.error(f"Failed to fetch premises: {premises}")
                premises = []
                
            if isinstance(items, Exception):
                logger.error(f"Failed to fetch items: {items}")
                items = []
            
            # Process the data
            processed_data = await self._process_raw_data(
                transactions, premises, items
            )
            
            # Update database
            db_stats = await self._update_database(processed_data)
            
            # Cache processed data
            await self._cache_processed_data(processed_data)
            
            # Update refresh timestamp
            self.last_refresh = datetime.now()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            refresh_stats = {
                "status": "completed",
                "processing_time_seconds": round(processing_time, 2),
                "raw_transactions": len(transactions) if transactions else 0,
                "raw_premises": len(premises) if premises else 0,
                "raw_items": len(items) if items else 0,
                "processed_records": processed_data.get("total_processed", 0),
                "database_updates": db_stats,
                "last_refresh": self.last_refresh.isoformat(),
                "data_source": "OpenDOSM PriceCatcher API"
            }
            
            logger.info(f"✅ Data refresh completed: {refresh_stats}")
            return refresh_stats
            
        except Exception as e:
            logger.error(f"❌ Data refresh failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None
            }
    
    async def _process_raw_data(
        self, 
        transactions: List[Dict], 
        premises: List[Dict], 
        items: List[Dict]
    ) -> Dict[str, Any]:
        """
        Process raw OpenDOSM data into structured format
        
        Args:
            transactions: Raw transaction data
            premises: Raw premise lookup data
            items: Raw item lookup data
            
        Returns:
            Processed and structured data
        """
        try:
            logger.info("📊 Processing raw PriceCatcher data")
            
            # Create lookup maps for faster processing
            premise_map = {p.get("premise_code", ""): p for p in premises}
            item_map = {i.get("item_code", ""): i for i in items}
            
            processed_stores = {}
            processed_items = {}
            total_processed = 0
            
            for transaction in transactions:
                try:
                    premise_code = transaction.get("premise_code", "")
                    item_code = transaction.get("item_code", "")
                    
                    # Get premise details
                    premise_info = premise_map.get(premise_code, {})
                    item_info = item_map.get(item_code, {})
                    
                    # Process store information
                    if premise_code and premise_code not in processed_stores:
                        processed_stores[premise_code] = self._process_store_data(
                            premise_code, premise_info, transaction
                        )
                    
                    # Process item price data
                    item_key = f"{premise_code}_{item_code}"
                    if item_key not in processed_items:
                        processed_items[item_key] = self._process_item_price(
                            transaction, premise_info, item_info
                        )
                    
                    total_processed += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing transaction: {e}")
                    continue
            
            processed_data = {
                "stores": processed_stores,
                "items": processed_items,
                "total_processed": total_processed,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Processed {total_processed} records into {len(processed_stores)} stores and {len(processed_items)} items")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing raw data: {e}")
            return {"stores": {}, "items": {}, "total_processed": 0}
    
    def _process_store_data(
        self, 
        premise_code: str, 
        premise_info: Dict, 
        transaction: Dict
    ) -> Dict[str, Any]:
        """Process individual store data"""
        
        premise_name = premise_info.get("premise_name", "") or transaction.get("premise", "")
        
        return {
            "premise_code": premise_code,
            "premise_name": premise_name,
            "chain_name": opendosm_client.map_premise_to_chain(premise_name),
            "address": premise_info.get("address", ""),
            "state": premise_info.get("state", "") or transaction.get("state", ""),
            "district": premise_info.get("district", ""),
            "data_source": "OpenDOSM"
        }
    
    def _process_item_price(
        self, 
        transaction: Dict, 
        premise_info: Dict, 
        item_info: Dict
    ) -> Dict[str, Any]:
        """Process individual item price data"""
        
        # Extract price and normalize
        price = self._extract_and_normalize_price(transaction.get("price", 0))
        
        # Get item details
        item_name = item_info.get("item", "") or transaction.get("item", "")
        unit = item_info.get("unit", "") or transaction.get("unit", "kg")
        
        # Normalize price per kg for comparison
        price_per_kg = self._calculate_price_per_kg(price, unit)
        
        return {
            "premise_code": transaction.get("premise_code", ""),
            "premise_name": premise_info.get("premise_name", ""),
            "item_code": transaction.get("item_code", ""),
            "item_name": item_name,
            "category": item_info.get("category", "Food"),
            "subcategory": item_info.get("subcategory", ""),
            "price": price,
            "unit": unit,
            "price_per_kg": price_per_kg,
            "state": premise_info.get("state", ""),
            "price_date": transaction.get("date", datetime.now().strftime("%Y-%m-%d")),
            "data_source": "OpenDOSM"
        }
    
    def _extract_and_normalize_price(self, price_value: Any) -> float:
        """Extract and normalize price value"""
        try:
            if isinstance(price_value, (int, float)):
                return float(price_value)
            elif isinstance(price_value, str):
                # Remove currency symbols and clean up
                cleaned = price_value.replace("RM", "").replace(",", "").strip()
                return float(cleaned)
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_price_per_kg(self, price: float, unit: str) -> float:
        """Calculate normalized price per kg"""
        if not price or not unit:
            return price
        
        unit_lower = unit.lower().strip()
        
        # Unit conversion factors to kg
        conversion_factors = {
            "kg": 1.0,
            "g": 0.001,
            "gram": 0.001,
            "kilogram": 1.0,
            "lb": 0.453592,
            "pound": 0.453592,
            "liter": 1.0,  # Assume similar density to water
            "litre": 1.0,
            "l": 1.0,
            "ml": 0.001,
            "piece": 0.2,  # Estimate for average piece weight
            "pcs": 0.2,
            "each": 0.2,
            "pack": 0.5,  # Estimate for average pack weight
            "packet": 0.5,
            "can": 0.4,   # Average can weight
            "bottle": 0.5  # Average bottle weight
        }
        
        factor = conversion_factors.get(unit_lower, 1.0)
        return price / factor if factor > 0 else price
    
    async def _update_database(self, processed_data: Dict[str, Any]) -> Dict[str, int]:
        """Update database with processed data"""
        try:
            db = SessionLocal()
            
            # Clear old data (older than 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            deleted_count = db.query(GroceryPrice).filter(
                GroceryPrice.created_at < cutoff_date
            ).delete()
            
            # Insert new price data
            inserted_count = 0
            items_data = processed_data.get("items", {})
            
            for item_data in items_data.values():
                try:
                    grocery_price = GroceryPrice(
                        premise_code=item_data["premise_code"],
                        premise_name=item_data["premise_name"],
                        premise_address="",  # Not available in current format
                        state=item_data["state"],
                        item_code=item_data["item_code"],
                        item_name=item_data["item_name"],
                        item_category=item_data["category"],
                        item_subcategory=item_data["subcategory"],
                        price=item_data["price"],
                        unit=item_data["unit"],
                        price_date=datetime.strptime(item_data["price_date"], "%Y-%m-%d"),
                        chain_name=opendosm_client.map_premise_to_chain(item_data["premise_name"]),
                        normalized_item_name=item_data["item_name"].lower().strip(),
                        price_per_kg=item_data["price_per_kg"]
                    )
                    
                    db.add(grocery_price)
                    inserted_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error inserting price record: {e}")
                    continue
            
            # Commit changes
            db.commit()
            db.close()
            
            stats = {
                "deleted_old_records": deleted_count,
                "inserted_new_records": inserted_count
            }
            
            logger.info(f"📀 Database updated: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return {"deleted_old_records": 0, "inserted_new_records": 0}
    
    async def _cache_processed_data(self, processed_data: Dict[str, Any]):
        """Cache processed data for faster access"""
        try:
            # Cache store data
            stores_data = processed_data.get("stores", {})
            await cache_service.set(
                "pricecatcher:stores", 
                stores_data, 
                ttl=self.cache_ttl
            )
            
            # Cache recent items by category
            items_data = processed_data.get("items", {})
            categories = {}
            
            for item_data in items_data.values():
                category = item_data.get("category", "Other")
                if category not in categories:
                    categories[category] = []
                categories[category].append(item_data)
            
            # Cache each category separately
            for category, items in categories.items():
                cache_key = f"pricecatcher:category:{category.lower()}"
                await cache_service.set(cache_key, items, ttl=self.cache_ttl)
            
            logger.info(f"💾 Cached data for {len(stores_data)} stores and {len(categories)} categories")
            
        except Exception as e:
            logger.error(f"Error caching processed data: {e}")
    
    async def get_ingredient_prices(
        self, 
        ingredient_names: List[str], 
        state: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get prices for specific ingredients across stores
        
        Args:
            ingredient_names: List of ingredient names to search for
            state: Optional state filter
            
        Returns:
            Dictionary mapping ingredient names to price lists
        """
        try:
            results = {}
            
            for ingredient in ingredient_names:
                # Try cache first
                cache_key = f"pricecatcher:ingredient:{ingredient.lower()}"
                if state:
                    cache_key += f":{state.lower()}"
                
                cached_result = await cache_service.get(cache_key)
                
                if cached_result:
                    results[ingredient] = cached_result
                else:
                    # Fetch from OpenDOSM API
                    prices = await opendosm_client.search_prices_by_item(
                        ingredient, state=state, limit=50
                    )
                    
                    # Process and normalize prices
                    processed_prices = []
                    for price_data in prices:
                        processed_price = self._process_item_price(
                            price_data, 
                            {"premise_name": price_data.get("premise", "")},
                            {"item": price_data.get("item", "")}
                        )
                        processed_prices.append(processed_price)
                    
                    results[ingredient] = processed_prices
                    
                    # Cache the result
                    await cache_service.set(cache_key, processed_prices, ttl=3600)  # 1 hour cache
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting ingredient prices: {e}")
            return {}
    
    async def needs_refresh(self) -> bool:
        """Check if data needs refreshing"""
        if not self.last_refresh:
            return True
        
        # Check if data is older than refresh interval
        refresh_interval = timedelta(hours=24)  # 24 hours
        return datetime.now() - self.last_refresh > refresh_interval

# Global processor instance
pricecatcher_processor = PriceCatcherProcessor() 