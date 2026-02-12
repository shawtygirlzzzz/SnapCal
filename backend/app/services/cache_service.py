"""
Cache Service - Smart caching for AI-generated content
"""

import json
import hashlib
from typing import Optional, Dict, Any
from app.core.config import settings

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheService:
    """
    Smart caching service for AI responses
    Falls back to in-memory cache if Redis unavailable
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Any] = {}
        self.cache_enabled = settings.ENABLE_CACHING
        
        # Initialize Redis if available and enabled
        if REDIS_AVAILABLE and self.cache_enabled:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                print("✅ Redis cache connected successfully")
            except Exception as e:
                print(f"⚠️ Redis unavailable, using memory cache: {e}")
                self.redis_client = None
        else:
            print("🔄 Using in-memory cache (Redis disabled)")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        # Sort parameters for consistent keys
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"snapcal:{prefix}:{param_hash}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value"""
        if not self.cache_enabled:
            return None
        
        try:
            if self.redis_client:
                # Get from Redis
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Get from memory cache
                return self.memory_cache.get(key)
        except Exception as e:
            print(f"⚠️ Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> bool:
        """Set cached value"""
        if not self.cache_enabled:
            return False
        
        if ttl is None:
            ttl = settings.CACHE_TTL_SECONDS
        
        try:
            if self.redis_client:
                # Set in Redis
                self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            else:
                # Set in memory cache (no TTL for simplicity)
                self.memory_cache[key] = value
                # Simple memory management - keep max 1000 items
                if len(self.memory_cache) > 1000:
                    # Remove oldest 200 items
                    keys_to_remove = list(self.memory_cache.keys())[:200]
                    for k in keys_to_remove:
                        del self.memory_cache[k]
                return True
        except Exception as e:
            print(f"⚠️ Cache set error: {e}")
        
        return False
    
    async def get_recipe_cache(self, **params) -> Optional[Dict[str, Any]]:
        """Get cached recipe generation result"""
        key = self._generate_cache_key("recipe", **params)
        return await self.get(key)
    
    async def set_recipe_cache(self, result: Dict[str, Any], **params) -> bool:
        """Cache recipe generation result"""
        key = self._generate_cache_key("recipe", **params)
        return await self.set(key, result)
    
    async def get_meal_plan_cache(self, **params) -> Optional[Dict[str, Any]]:
        """Get cached meal plan result"""
        key = self._generate_cache_key("meal_plan", **params)
        return await self.get(key)
    
    async def set_meal_plan_cache(self, result: Dict[str, Any], **params) -> bool:
        """Cache meal plan result"""
        key = self._generate_cache_key("meal_plan", **params)
        return await self.set(key, result)
    
    async def get_food_analysis_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached food analysis result"""
        key = f"snapcal:food_analysis:{image_hash}"
        return await self.get(key)
    
    async def set_food_analysis_cache(self, image_hash: str, result: Dict[str, Any]) -> bool:
        """Cache food analysis result"""
        key = f"snapcal:food_analysis:{image_hash}"
        # Longer TTL for food analysis (6 hours)
        return await self.set(key, result, ttl=6 * 3600)
    
    def clear_memory_cache(self):
        """Clear memory cache"""
        self.memory_cache.clear()
        print("🧹 Memory cache cleared")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "cache_enabled": self.cache_enabled,
            "redis_available": self.redis_client is not None,
            "memory_cache_size": len(self.memory_cache)
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    "redis_used_memory": info.get("used_memory_human"),
                    "redis_connected_clients": info.get("connected_clients"),
                    "redis_total_commands": info.get("total_commands_processed")
                })
            except Exception as e:
                stats["redis_error"] = str(e)
        
        return stats

# Global cache instance
cache_service = CacheService() 