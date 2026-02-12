"""
Meal Planning API endpoints
Handles budget-based meal suggestions with AI integration
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.schemas import MealSuggestionRequest, MealSuggestionResponse, MealSuggestion
from app.services.meal_service import MealService
from app.services.ai_recipe_service import ai_recipe_service
from app.core.config import settings

router = APIRouter()

# AI Meal Plan Request Schema
class AIMealPlanRequest(BaseModel):
    budget_rm: float
    num_people: int = 1
    days: int = 7
    dietary_preferences: List[str] = []
    exclude_ingredients: List[str] = []
    cuisine_preferences: List[str] = ["Malaysian", "Asian"]

@router.post("/ai-plan", response_model=dict)
async def generate_ai_meal_plan(
    request: AIMealPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate an intelligent weekly meal plan using AI
    
    This endpoint uses Gemini 2.0 Flash to create a comprehensive meal plan
    that includes daily meals, shopping list, budget breakdown, and nutrition analysis.
    """
    if not settings.USE_AI_MEAL_PLANNING:
        raise HTTPException(
            status_code=503,
            detail="AI meal planning is currently disabled"
        )
    
    if not ai_recipe_service.model:
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please try again later."
        )
    
    try:
        # Generate meal plan with AI
        meal_plan = await ai_recipe_service.generate_meal_plan(
            budget_rm=request.budget_rm,
            num_people=request.num_people,
            days=request.days,
            dietary_preferences=request.dietary_preferences,
            exclude_ingredients=request.exclude_ingredients,
            cuisine_preferences=request.cuisine_preferences
        )
        
        if not meal_plan:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate meal plan. Please try with different parameters."
            )
        
        return {
            "success": True,
            "meal_plan": meal_plan,
            "source": "ai_generated",
            "model_version": meal_plan.get("model_version", "gemini-2.0-flash"),
            "cached": meal_plan.get("cached", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Meal plan generation failed: {str(e)}"
        )

@router.post("/suggest", response_model=MealSuggestionResponse)
async def suggest_meals(
    request: MealSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Get meal suggestions based on budget and preferences (Hybrid AI + Database)
    
    Returns a list of Malaysian dishes that fit within the specified budget
    per person, considering dietary preferences and restrictions.
    Uses AI-powered suggestions when available, falls back to database recipes.
    """
    try:
        meal_service = MealService(db)
        
        # Get meal suggestions (now includes AI integration)
        suggestions = await meal_service.get_budget_meal_suggestions(
            budget_rm=request.budget_rm,
            num_people=request.num_people,
            dietary_preferences=request.dietary_preferences,
            exclude_ingredients=request.exclude_ingredients
        )
        
        # Calculate aggregated statistics
        if suggestions:
            total_cost = sum(s.estimated_cost_rm * request.num_people for s in suggestions)
            average_cost_per_person = total_cost / len(suggestions) / request.num_people
            total_calories = sum(s.calories_per_serving * request.num_people for s in suggestions)
        else:
            average_cost_per_person = 0.0
            total_calories = 0.0
        
        return MealSuggestionResponse(
            request_budget=request.budget_rm,
            num_people=request.num_people,
            total_suggestions=len(suggestions),
            suggestions=suggestions,
            average_cost_per_person=round(average_cost_per_person, 2),
            total_estimated_calories=round(total_calories, 1)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate meal suggestions: {str(e)}"
        )

@router.get("/popular")
async def get_popular_meals(
    limit: int = 10,
    max_cost_rm: float = None,
    db: Session = Depends(get_db)
):
    """
    Get popular Malaysian meals
    """
    meal_service = MealService(db)
    popular_meals = await meal_service.get_popular_meals(
        limit=limit,
        max_cost_rm=max_cost_rm
    )
    
    return {
        "popular_meals": popular_meals,
        "total_count": len(popular_meals)
    }

@router.get("/budget-breakdown")
async def get_budget_breakdown(
    budget_rm: float,
    num_people: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get budget breakdown analysis for meal planning
    """
    meal_service = MealService(db)
    breakdown = await meal_service.analyze_budget_breakdown(
        budget_rm=budget_rm,
        num_people=num_people
    )
    
    return breakdown

@router.get("/dietary-options")
async def get_dietary_options():
    """
    Get available dietary preference options
    """
    return {
        "dietary_preferences": [
            "vegetarian",
            "halal",
            "no_beef",
            "no_pork", 
            "no_seafood",
            "low_sodium",
            "high_protein",
            "gluten_free",
            "dairy_free",
            "keto",
            "paleo"
        ],
        "cuisine_types": [
            "Malaysian",
            "Chinese",
            "Indian",
            "Malay",
            "Peranakan",
            "Thai",
            "Japanese",
            "Korean",
            "Mediterranean",
            "International"
        ],
        "difficulty_levels": [
            "easy",
            "medium",
            "hard"
        ]
    }

@router.get("/ai/capabilities")
async def get_ai_meal_planning_capabilities():
    """
    Get information about AI meal planning capabilities
    """
    return {
        "ai_meal_planning_enabled": settings.USE_AI_MEAL_PLANNING,
        "ai_available": ai_recipe_service.model is not None,
        "model_version": ai_recipe_service.model_version if ai_recipe_service.model else None,
        "max_days": 30,
        "max_people": 20,
        "max_budget_rm": 1000.0,
        "supported_features": [
            "intelligent_budget_optimization",
            "nutrition_balancing",
            "ingredient_reuse_optimization",
            "seasonal_ingredient_suggestions",
            "shopping_list_generation",
            "meal_prep_scheduling"
        ]
    } 