"""
Recipe API endpoints
Handles detailed recipe information, search, and AI generation
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.schemas import RecipeDetail, RecipeSearchResponse, RecipeListItem
from app.services.recipe_service import RecipeService
from app.services.ai_recipe_service import ai_recipe_service
from app.core.config import settings

router = APIRouter()

# AI Recipe Generation Request Schema
class AIRecipeRequest(BaseModel):
    cuisine_type: str = "Malaysian"
    budget_rm: float = 20.0
    servings: int = 4
    dietary_preferences: Optional[List[str]] = []
    available_ingredients: Optional[List[str]] = []
    cooking_time_limit: Optional[int] = None

@router.post("/generate", response_model=dict)
async def generate_ai_recipe(
    request: AIRecipeRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a custom recipe using AI based on user preferences
    
    This endpoint uses Gemini 2.0 Flash to create personalized recipes
    based on cuisine type, budget, dietary preferences, and available ingredients.
    """
    if not settings.USE_AI_RECIPES:
        raise HTTPException(
            status_code=503,
            detail="AI recipe generation is currently disabled"
        )
    
    if not ai_recipe_service.model:
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please try again later."
        )
    
    try:
        # Generate recipe with AI
        ai_recipe = await ai_recipe_service.generate_recipe(
            cuisine_type=request.cuisine_type,
            budget_rm=request.budget_rm,
            servings=request.servings,
            dietary_preferences=request.dietary_preferences,
            available_ingredients=request.available_ingredients,
            cooking_time_limit=request.cooking_time_limit
        )
        
        if not ai_recipe:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate recipe. Please try with different parameters."
            )
        
        return {
            "success": True,
            "recipe": ai_recipe,
            "source": "ai_generated",
            "model_version": ai_recipe.get("model_version", "gemini-2.0-flash"),
            "cached": ai_recipe.get("cached", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(e)}"
        )

@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe_detail(
    recipe_id: int,
    language: str = Query(default="en", description="Language preference (en/bm)"),
    db: Session = Depends(get_db)
):
    """
    Get detailed recipe information by ID
    
    Returns complete recipe details including ingredients, instructions,
    nutrition information, and cooking times.
    """
    try:
        recipe_service = RecipeService(db)
        recipe_detail = await recipe_service.get_recipe_detail(
            recipe_id=recipe_id,
            language=language
        )
        
        if not recipe_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        return recipe_detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recipe: {str(e)}"
        )

@router.get("/search/", response_model=RecipeSearchResponse)
async def search_recipes(
    q: Optional[str] = Query(None, description="Search query"),
    cuisine_type: Optional[str] = Query(None, description="Cuisine type filter"),
    max_cost_rm: Optional[float] = Query(None, description="Maximum cost per serving"),
    max_prep_time: Optional[int] = Query(None, description="Maximum prep time in minutes"),
    difficulty: Optional[str] = Query(None, description="Difficulty level (easy/medium/hard)"),
    is_vegetarian: Optional[bool] = Query(None, description="Vegetarian recipes only"),
    is_halal: Optional[bool] = Query(None, description="Halal recipes only"),
    limit: int = Query(default=20, le=50, description="Number of results to return"),
    offset: int = Query(default=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search and filter recipes
    
    Supports various filters including cost, preparation time, 
    dietary restrictions, and text search.
    """
    try:
        recipe_service = RecipeService(db)
        
        filters = {
            "search_query": q,
            "cuisine_type": cuisine_type,
            "max_cost_rm": max_cost_rm,
            "max_prep_time": max_prep_time,
            "difficulty": difficulty,
            "is_vegetarian": is_vegetarian,
            "is_halal": is_halal
        }
        
        search_result = await recipe_service.search_recipes(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return search_result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search recipes: {str(e)}"
        )

@router.get("/popular/", response_model=List[RecipeListItem])
async def get_popular_recipes(
    limit: int = Query(default=10, le=20, description="Number of recipes to return"),
    db: Session = Depends(get_db)
):
    """
    Get popular Malaysian recipes
    """
    recipe_service = RecipeService(db)
    popular_recipes = await recipe_service.get_popular_recipes(limit=limit)
    
    return popular_recipes

@router.get("/by-name/{recipe_name}", response_model=RecipeDetail)
async def get_recipe_by_name(
    recipe_name: str,
    language: str = Query(default="en", description="Language preference (en/bm)"),
    db: Session = Depends(get_db)
):
    """
    Get recipe by name (URL-friendly endpoint)
    """
    try:
        recipe_service = RecipeService(db)
        recipe_detail = await recipe_service.get_recipe_by_name(
            recipe_name=recipe_name,
            language=language
        )
        
        if not recipe_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe '{recipe_name}' not found"
            )
        
        return recipe_detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recipe: {str(e)}"
        )

@router.get("/categories/")
async def get_recipe_categories(db: Session = Depends(get_db)):
    """
    Get available recipe categories and cuisine types
    """
    recipe_service = RecipeService(db)
    categories = await recipe_service.get_recipe_categories()
    
    return categories

@router.get("/ingredients/{recipe_id}")
async def get_recipe_ingredients(
    recipe_id: int,
    servings: Optional[int] = Query(default=None, description="Adjust quantities for servings"),
    db: Session = Depends(get_db)
):
    """
    Get ingredient list for a recipe, optionally scaled for different servings
    """
    try:
        recipe_service = RecipeService(db)
        ingredients = await recipe_service.get_recipe_ingredients(
            recipe_id=recipe_id,
            target_servings=servings
        )
        
        if not ingredients:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        return {
            "recipe_id": recipe_id,
            "target_servings": servings,
            "ingredients": ingredients
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ingredients: {str(e)}"
        )

@router.get("/nutrition/{recipe_id}")
async def get_recipe_nutrition(
    recipe_id: int,
    servings: Optional[int] = Query(default=None, description="Adjust nutrition for servings"),
    db: Session = Depends(get_db)
):
    """
    Get detailed nutrition information for a recipe
    """
    try:
        recipe_service = RecipeService(db)
        nutrition = await recipe_service.get_recipe_nutrition(
            recipe_id=recipe_id,
            target_servings=servings
        )
        
        if not nutrition:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        return nutrition
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get nutrition data: {str(e)}"
        )

@router.get("/ai/capabilities")
async def get_ai_capabilities():
    """
    Get information about AI recipe generation capabilities
    """
    return {
        "ai_recipes_enabled": settings.USE_AI_RECIPES,
        "ai_available": ai_recipe_service.model is not None,
        "model_version": ai_recipe_service.model_version if ai_recipe_service.model else None,
        "supported_cuisines": [
            "Malaysian", "Chinese", "Indian", "Thai", "Japanese", 
            "Italian", "Mediterranean", "International"
        ],
        "dietary_preferences": [
            "vegetarian", "halal", "no_beef", "no_pork", "no_seafood",
            "gluten_free", "dairy_free", "low_sodium", "high_protein"
        ],
        "max_budget_rm": 100.0,
        "max_servings": 20,
        "max_cooking_time_minutes": 240
    } 