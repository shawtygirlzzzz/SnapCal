"""
SnapCal+ Backend API
FastAPI application for Malaysian food budget planning
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.api import calorie_router, meal_router, grocery_router, recipe_router, admin_router
from app.core.config import settings
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SnapCal+ API",
    description="Malaysian Food Budget Planner API with calorie estimation and grocery price comparison",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API routers
app.include_router(calorie_router, prefix="/api/calorie", tags=["Calorie Analysis"])
app.include_router(meal_router, prefix="/api/meal", tags=["Meal Planning"])
app.include_router(grocery_router, prefix="/api/grocery", tags=["Grocery Prices"])
app.include_router(recipe_router, prefix="/api/recipe", tags=["Recipes"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin & Monitoring"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SnapCal+ API - Malaysian Food Budget Planner",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "snapcal-backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 