"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # App settings
    APP_NAME: str = "SnapCal+ API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./snapcal.db"
    
    # API settings
    API_V1_STR: str = "/api"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # OpenDOSM API settings - PriceCatcher Integration
    OPENDOSM_BASE_URL: str = "https://api.data.gov.my"
    OPENDOSM_PRICECATCHER_ENDPOINT: str = "/data-catalogue"
    OPENDOSM_STORAGE_BASE: str = "https://storage.data.gov.my"
    
    # PriceCatcher specific dataset IDs
    PRICECATCHER_TRANSACTIONS_ID: str = "pricecatcher"
    PRICECATCHER_PREMISES_ID: str = "pricecatcher_premise"
    PRICECATCHER_ITEMS_ID: str = "pricecatcher_item"
    
    # Data refresh settings
    PRICECATCHER_REFRESH_INTERVAL_HOURS: int = 24  # Refresh daily
    PRICECATCHER_API_TIMEOUT: int = 30  # 30 seconds timeout
    PRICECATCHER_MAX_RETRIES: int = 3
    
    # AI settings (for calorie estimation, recipes, meal planning)
    GEMINI_API_KEY: str = ""  # Set via environment variable
    GEMINI_MODEL: str = "gemini-2.0-flash"
    USE_GEMINI_AI: bool = True  # Set to False to use mock AI
    USE_AI_RECIPES: bool = True  # Enable AI recipe generation
    USE_AI_MEAL_PLANNING: bool = True  # Enable AI meal planning
    MOCK_AI_ENABLED: bool = True  # Fallback when Gemini fails
    MOCK_AI_DELAY: float = 1.0  # Simulate processing time for mock
    
    # Caching settings
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600  # 1 hour cache
    ENABLE_CACHING: bool = True
    
    # Malaysian specific settings
    DEFAULT_CURRENCY: str = "RM"
    DEFAULT_LANGUAGE: str = "en"  # en or bm (Bahasa Malaysia)
    
    # Recipe settings
    DEFAULT_SERVING_SIZE: int = 4
    MAX_RECIPE_STEPS: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure upload directory exists
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(exist_ok=True) 