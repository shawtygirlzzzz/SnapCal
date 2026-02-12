"""
Admin API endpoints
Handles cache management, AI service monitoring, and OpenDOSM integration
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.cache_service import cache_service
from app.services.ai_recipe_service import ai_recipe_service
from app.services.opendosm_client import opendosm_client
from app.services.pricecatcher_processor import pricecatcher_processor
from app.core.config import settings

router = APIRouter()

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics and performance metrics
    """
    try:
        stats = await cache_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "configuration": {
                "cache_enabled": settings.ENABLE_CACHING,
                "cache_ttl_seconds": settings.CACHE_TTL_SECONDS,
                "redis_url": settings.REDIS_URL if settings.REDIS_URL else "Not configured"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )

@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cached data (memory cache only)
    """
    try:
        cache_service.clear_memory_cache()
        return {
            "success": True,
            "message": "Memory cache cleared successfully",
            "note": "Redis cache (if enabled) was not cleared"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/ai/status")
async def get_ai_service_status():
    """
    Get AI service status and configuration
    """
    return {
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "ai_services": {
            "calorie_estimation": {
                "enabled": settings.USE_GEMINI_AI,
                "model_available": ai_recipe_service.model is not None
            },
            "recipe_generation": {
                "enabled": settings.USE_AI_RECIPES,
                "model_available": ai_recipe_service.model is not None
            },
            "meal_planning": {
                "enabled": settings.USE_AI_MEAL_PLANNING,
                "model_available": ai_recipe_service.model is not None
            }
        },
        "fallback_enabled": settings.MOCK_AI_ENABLED,
        "model_version": ai_recipe_service.model_version
    }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all services including OpenDOSM integration
    """
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Database health
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Cache health
    try:
        cache_stats = await cache_service.get_cache_stats()
        health_status["services"]["cache"] = {
            "status": "healthy" if cache_stats["cache_enabled"] else "disabled",
            "redis_available": cache_stats.get("redis_available", False)
        }
    except Exception as e:
        health_status["services"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # AI service health
    ai_available = ai_recipe_service.model is not None
    health_status["services"]["ai"] = {
        "status": "healthy" if ai_available else "degraded",
        "gemini_available": ai_available,
        "fallback_available": settings.MOCK_AI_ENABLED
    }
    
    if not ai_available and not settings.MOCK_AI_ENABLED:
        health_status["status"] = "degraded"
    
    # OpenDOSM PriceCatcher health
    try:
        opendosm_info = await opendosm_client.get_latest_data_info()
        health_status["services"]["opendosm"] = {
            "status": "healthy" if opendosm_info.get("api_status") == "available" else "degraded",
            "api_available": opendosm_info.get("api_status") == "available",
            "last_updated": opendosm_info.get("last_updated"),
            "total_records": opendosm_info.get("total_records", 0),
            "needs_refresh": await pricecatcher_processor.needs_refresh()
        }
        
        if opendosm_info.get("api_status") != "available":
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["services"]["opendosm"] = {
            "status": "unhealthy", 
            "error": str(e),
            "api_available": False
        }
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/config")
async def get_system_config():
    """
    Get system configuration (non-sensitive values only)
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "database_type": "SQLite" if "sqlite" in settings.DATABASE_URL else "Unknown",
        "ai_features": {
            "gemini_model": settings.GEMINI_MODEL,
            "use_ai_recipes": settings.USE_AI_RECIPES,
            "use_ai_meal_planning": settings.USE_AI_MEAL_PLANNING,
            "cache_enabled": settings.ENABLE_CACHING
        },
        "file_upload": {
            "max_file_size_mb": settings.MAX_FILE_SIZE // 1024 // 1024,
            "allowed_types": settings.ALLOWED_IMAGE_TYPES,
            "upload_dir": settings.UPLOAD_DIR
        },
        "opendosm_integration": {
            "base_url": settings.OPENDOSM_BASE_URL,
            "refresh_interval_hours": settings.PRICECATCHER_REFRESH_INTERVAL_HOURS,
            "api_timeout": settings.PRICECATCHER_API_TIMEOUT,
            "max_retries": settings.PRICECATCHER_MAX_RETRIES
        },
        "localization": {
            "default_currency": settings.DEFAULT_CURRENCY,
            "default_language": settings.DEFAULT_LANGUAGE
        }
    }

@router.get("/opendosm/status")
async def get_opendosm_status():
    """
    Get detailed OpenDOSM PriceCatcher integration status
    """
    try:
        # Get API status
        api_info = await opendosm_client.get_latest_data_info()
        
        # Get processor status
        needs_refresh = await pricecatcher_processor.needs_refresh()
        
        # Get cache stats
        cache_stats = await cache_service.get_cache_stats()
        
        return {
            "api_integration": {
                "status": api_info.get("api_status", "unknown"),
                "base_url": settings.OPENDOSM_BASE_URL,
                "last_api_check": api_info.get("last_updated"),
                "total_records_available": api_info.get("total_records", 0),
                "error": api_info.get("error")
            },
            "data_processor": {
                "needs_refresh": needs_refresh,
                "last_refresh": pricecatcher_processor.last_refresh.isoformat() if pricecatcher_processor.last_refresh else None,
                "refresh_interval_hours": settings.PRICECATCHER_REFRESH_INTERVAL_HOURS
            },
            "caching": {
                "cache_enabled": cache_stats.get("cache_enabled", False),
                "redis_available": cache_stats.get("redis_available", False),
                "memory_cache_size": cache_stats.get("memory_cache_size", 0)
            },
            "configuration": {
                "datasets": {
                    "transactions": settings.PRICECATCHER_TRANSACTIONS_ID,
                    "premises": settings.PRICECATCHER_PREMISES_ID,
                    "items": settings.PRICECATCHER_ITEMS_ID
                },
                "api_timeout": settings.PRICECATCHER_API_TIMEOUT,
                "max_retries": settings.PRICECATCHER_MAX_RETRIES
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OpenDOSM status: {str(e)}"
        )

@router.post("/opendosm/refresh")
async def refresh_opendosm_data():
    """
    Manually trigger OpenDOSM PriceCatcher data refresh
    """
    try:
        print("🔄 Manual OpenDOSM data refresh requested")
        
        # Trigger data refresh
        refresh_stats = await pricecatcher_processor.refresh_all_data()
        
        return {
            "success": True,
            "message": "OpenDOSM data refresh completed",
            "stats": refresh_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh OpenDOSM data: {str(e)}"
        )

@router.get("/opendosm/test")
async def test_opendosm_connection():
    """
    Test OpenDOSM API connection and data availability
    """
    from datetime import datetime
    
    try:
        print("🧪 Testing OpenDOSM API connection")
        
        # Test basic API connection
        api_info = await opendosm_client.get_latest_data_info()
        
        # Test data fetching
        sample_transactions = await opendosm_client.get_pricecatcher_transactions(limit=5)
        sample_premises = await opendosm_client.get_premise_lookup()
        sample_items = await opendosm_client.get_item_lookup()
        
        return {
            "connection_test": {
                "status": "success" if api_info.get("api_status") == "available" else "failed",
                "api_info": api_info
            },
            "data_test": {
                "transactions_available": len(sample_transactions) > 0,
                "sample_transaction_count": len(sample_transactions),
                "premises_available": len(sample_premises) > 0,
                "sample_premise_count": len(sample_premises),
                "items_available": len(sample_items) > 0,
                "sample_item_count": len(sample_items)
            },
            "test_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "connection_test": {
                "status": "failed",
                "error": str(e)
            },
            "data_test": {
                "transactions_available": False,
                "premises_available": False,
                "items_available": False
            },
            "test_timestamp": datetime.now().isoformat()
        } 