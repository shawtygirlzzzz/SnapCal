"""
API Endpoints Package

This package contains all the API route handlers for SnapCal+:
- calorie: Food image analysis and calorie estimation
- meal: AI-powered meal planning and suggestions  
- grocery: Price comparison using OpenDOSM data
- recipe: Recipe management and AI generation
- admin: System monitoring and cache management
"""

# Import all routers for easy access
from .calorie import router as calorie_router
from .meal import router as meal_router
from .grocery import router as grocery_router
from .recipe import router as recipe_router
from .admin import router as admin_router

# Define what's available for "from api import *"
__all__ = [
    'calorie_router',
    'meal_router', 
    'grocery_router',
    'recipe_router',
    'admin_router'
]

# Package metadata
__version__ = "1.0.0"
__description__ = "SnapCal+ API endpoints with AI integration" 