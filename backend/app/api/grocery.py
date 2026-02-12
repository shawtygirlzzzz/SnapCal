"""
Grocery Price Comparison API endpoints
Handles OpenDOSM PriceCatcher data integration
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.schemas import GroceryCompareRequest, GroceryCompareResponse
from app.services.grocery_service import GroceryService

router = APIRouter()

@router.post("/compare", response_model=GroceryCompareResponse)
async def compare_grocery_prices(
    request: GroceryCompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare grocery prices across stores for given ingredients
    
    Uses OpenDOSM PriceCatcher data to find the best prices for
    requested ingredients across different Malaysian retailers.
    """
    try:
        grocery_service = GroceryService(db)
        
        # Get price comparison
        comparison_result = await grocery_service.compare_ingredient_prices(
            ingredients=request.ingredients,
            location=request.location,
            max_distance_km=request.max_distance_km
        )
        
        return comparison_result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare grocery prices: {str(e)}"
        )

@router.get("/stores")
async def get_available_stores(
    state: str = None,
    chain_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Get list of available stores from PriceCatcher data
    """
    grocery_service = GroceryService(db)
    stores = await grocery_service.get_available_stores(
        state=state,
        chain_name=chain_name
    )
    
    return {
        "stores": stores,
        "total_count": len(stores)
    }

@router.get("/items")
async def search_grocery_items(
    search: str = None,
    category: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search for grocery items in the PriceCatcher database
    """
    grocery_service = GroceryService(db)
    items = await grocery_service.search_grocery_items(
        search_term=search,
        category=category,
        limit=limit
    )
    
    return {
        "items": items,
        "search_term": search,
        "category": category,
        "total_results": len(items)
    }

@router.get("/price-trends/{item_name}")
async def get_price_trends(
    item_name: str,
    days: int = 30,
    state: str = None,
    db: Session = Depends(get_db)
):
    """
    Get price trends for a specific item over time
    """
    grocery_service = GroceryService(db)
    trends = await grocery_service.get_price_trends(
        item_name=item_name,
        days=days,
        state=state
    )
    
    return trends

@router.post("/refresh-data")
async def refresh_pricecatcher_data(
    db: Session = Depends(get_db)
):
    """
    Manually trigger refresh of OpenDOSM PriceCatcher data
    """
    try:
        grocery_service = GroceryService(db)
        result = await grocery_service.refresh_pricecatcher_data()
        
        return {
            "status": "success",
            "message": "PriceCatcher data refresh initiated",
            "records_processed": result.get("records_processed", 0),
            "last_updated": result.get("last_updated")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh data: {str(e)}"
        )

@router.get("/chain-mapping")
async def get_chain_mapping():
    """
    Get mapping of premise names to chain names
    """
    return {
        "chain_mappings": {
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
    } 