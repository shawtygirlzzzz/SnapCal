"""
OpenDOSM API Client - Real integration with Malaysia's official data portal
Handles PriceCatcher data fetching from data.gov.my
"""

import httpx
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenDOSMClient:
    """
    Client for OpenDOSM data.gov.my API
    Handles PriceCatcher data fetching and processing
    """
    
    def __init__(self):
        self.base_url = settings.OPENDOSM_BASE_URL
        self.storage_base = settings.OPENDOSM_STORAGE_BASE
        self.timeout = settings.PRICECATCHER_API_TIMEOUT
        self.max_retries = settings.PRICECATCHER_MAX_RETRIES
        
    async def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {url}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request timeout after {self.max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"HTTP error after {self.max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)
    
    async def get_pricecatcher_transactions(
        self, 
        limit: int = 1000,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch PriceCatcher transaction data
        
        Args:
            limit: Maximum number of records to fetch
            date_filter: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            List of transaction records
        """
        try:
            url = f"{self.base_url}{settings.OPENDOSM_PRICECATCHER_ENDPOINT}"
            params = {
                "id": settings.PRICECATCHER_TRANSACTIONS_ID,
                "limit": limit
            }
            
            if date_filter:
                params["date"] = date_filter
            
            logger.info(f"Fetching PriceCatcher transactions: limit={limit}")
            
            response_data = await self._make_request(url, params)
            
            # Extract the actual data from the response
            if "data" in response_data:
                transactions = response_data["data"]
                logger.info(f"Successfully fetched {len(transactions)} transaction records")
                return transactions
            else:
                logger.warning("No 'data' field in API response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch PriceCatcher transactions: {e}")
            return []
    
    async def get_premise_lookup(self) -> List[Dict[str, Any]]:
        """
        Fetch premise lookup data for store mapping
        
        Returns:
            List of premise records with store information
        """
        try:
            url = f"{self.base_url}{settings.OPENDOSM_PRICECATCHER_ENDPOINT}"
            params = {
                "id": settings.PRICECATCHER_PREMISES_ID,
                "limit": 10000  # Get all premises
            }
            
            logger.info("Fetching PriceCatcher premise lookup data")
            
            response_data = await self._make_request(url, params)
            
            if "data" in response_data:
                premises = response_data["data"]
                logger.info(f"Successfully fetched {len(premises)} premise records")
                return premises
            else:
                logger.warning("No 'data' field in premise lookup response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch premise lookup: {e}")
            return []
    
    async def get_item_lookup(self) -> List[Dict[str, Any]]:
        """
        Fetch item lookup data for product mapping
        
        Returns:
            List of item records with product information
        """
        try:
            url = f"{self.base_url}{settings.OPENDOSM_PRICECATCHER_ENDPOINT}"
            params = {
                "id": settings.PRICECATCHER_ITEMS_ID,
                "limit": 10000  # Get all items
            }
            
            logger.info("Fetching PriceCatcher item lookup data")
            
            response_data = await self._make_request(url, params)
            
            if "data" in response_data:
                items = response_data["data"]
                logger.info(f"Successfully fetched {len(items)} item records")
                return items
            else:
                logger.warning("No 'data' field in item lookup response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch item lookup: {e}")
            return []
    
    async def get_latest_data_info(self) -> Dict[str, Any]:
        """
        Get metadata about the latest available PriceCatcher data
        
        Returns:
            Dictionary with data availability information
        """
        try:
            url = f"{self.base_url}{settings.OPENDOSM_PRICECATCHER_ENDPOINT}"
            params = {
                "id": settings.PRICECATCHER_TRANSACTIONS_ID,
                "limit": 1  # Just get metadata
            }
            
            response_data = await self._make_request(url, params)
            
            # Extract metadata
            metadata = {
                "last_updated": response_data.get("last_updated"),
                "next_update": response_data.get("next_update"),
                "total_records": response_data.get("total", 0),
                "data_source": "OpenDOSM PriceCatcher API",
                "api_status": "available"
            }
            
            logger.info(f"Latest data info: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get latest data info: {e}")
            return {
                "api_status": "unavailable",
                "error": str(e),
                "last_updated": None,
                "total_records": 0
            }
    
    async def search_prices_by_item(
        self, 
        item_name: str, 
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for specific item prices across stores
        
        Args:
            item_name: Name of item to search for
            state: Optional state filter
            limit: Maximum number of results
            
        Returns:
            List of price records for the specified item
        """
        try:
            # First get recent transactions
            transactions = await self.get_pricecatcher_transactions(limit=limit * 5)
            
            if not transactions:
                return []
            
            # Filter by item name (case-insensitive search)
            item_name_lower = item_name.lower()
            filtered_transactions = []
            
            for transaction in transactions:
                item_field = transaction.get("item", "") or transaction.get("item_name", "")
                if item_name_lower in item_field.lower():
                    # Add state filter if specified
                    if state is None or transaction.get("state", "").lower() == state.lower():
                        filtered_transactions.append(transaction)
                        
                        if len(filtered_transactions) >= limit:
                            break
            
            logger.info(f"Found {len(filtered_transactions)} price records for '{item_name}'")
            return filtered_transactions
            
        except Exception as e:
            logger.error(f"Failed to search prices for '{item_name}': {e}")
            return []
    
    async def get_store_prices(
        self, 
        premise_code: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all prices for a specific store/premise
        
        Args:
            premise_code: Store premise code
            limit: Maximum number of results
            
        Returns:
            List of price records for the specified store
        """
        try:
            transactions = await self.get_pricecatcher_transactions(limit=limit * 5)
            
            if not transactions:
                return []
            
            # Filter by premise code
            store_transactions = [
                transaction for transaction in transactions
                if transaction.get("premise_code") == premise_code
            ][:limit]
            
            logger.info(f"Found {len(store_transactions)} price records for premise {premise_code}")
            return store_transactions
            
        except Exception as e:
            logger.error(f"Failed to get store prices for premise {premise_code}: {e}")
            return []
    
    def map_premise_to_chain(self, premise_name: str) -> str:
        """
        Map premise name to recognizable chain name
        
        Args:
            premise_name: Raw premise name from OpenDOSM
            
        Returns:
            Standardized chain name
        """
        if not premise_name:
            return "Unknown Store"
        
        premise_upper = premise_name.upper()
        
        # Chain mapping based on premise name patterns
        chain_mappings = {
            "TESCO": "Tesco",
            "99 SPEEDMART": "99 Speedmart",
            "GIANT": "Giant",
            "AEON": "AEON",
            "VILLAGE GROCER": "Village Grocer",
            "JAYA GROCER": "Jaya Grocer",
            "ECONSAVE": "ECONSAVE",
            "NSK": "NSK",
            "MYDIN": "Mydin",
            "KK SUPER MART": "KK Super Mart",
            "SPEEDMART": "99 Speedmart",  # Alternative name
            "PASAR RAYA": "Local Grocery Store",
            "HYPERMARKET": "Hypermarket",
            "SUPERMARKET": "Supermarket"
        }
        
        for pattern, chain_name in chain_mappings.items():
            if pattern in premise_upper:
                return chain_name
        
        return "Independent Store"

# Global client instance
opendosm_client = OpenDOSMClient() 