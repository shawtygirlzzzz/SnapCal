"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True

# Calorie Analysis Schemas
class CalorieUploadResponse(BaseSchema):
    """Response for food photo analysis"""
    id: int
    filename: str
    recognized_food: str
    recognized_food_bm: Optional[str] = None  # Bahasa Malaysia name
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    estimated_calories: float
    estimated_weight_g: float
    nutrition: Dict[str, float]  # protein, carbs, fat, fiber, sodium
    processing_time_ms: int
    analysis_notes: Optional[str] = None  # AI analysis notes
    model_version: Optional[str] = None  # AI model version used
    created_at: datetime

class NutritionInfo(BaseSchema):
    """Nutrition information breakdown"""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float

# Meal Planning Schemas
class MealSuggestionRequest(BaseSchema):
    """Request for meal suggestions based on budget"""
    budget_rm: float = Field(..., gt=0, description="Budget in Malaysian Ringgit")
    num_people: int = Field(default=1, ge=1, le=20, description="Number of people")
    dietary_preferences: Optional[List[str]] = Field(default=[], description="vegetarian, halal, etc.")
    exclude_ingredients: Optional[List[str]] = Field(default=[], description="Ingredients to avoid")

class MealSuggestion(BaseSchema):
    """Individual meal suggestion"""
    recipe_id: int
    name: str
    name_bm: Optional[str]
    description: str
    estimated_cost_rm: float
    cost_per_person: float
    calories_per_serving: float
    prep_time_minutes: int
    cook_time_minutes: int
    difficulty_level: str
    servings: int
    is_vegetarian: bool
    is_halal: bool

class MealSuggestionResponse(BaseSchema):
    """Response with meal suggestions"""
    request_budget: float
    num_people: int
    total_suggestions: int
    suggestions: List[MealSuggestion]
    average_cost_per_person: float
    total_estimated_calories: float

# Grocery Comparison Schemas
class GroceryCompareRequest(BaseSchema):
    """Request for grocery price comparison"""
    ingredients: List[str] = Field(..., min_items=1, description="List of ingredient names")
    location: Optional[str] = Field(default=None, description="State or area for filtering")
    max_distance_km: Optional[float] = Field(default=50.0, description="Maximum distance for stores")

class GroceryItem(BaseSchema):
    """Individual grocery item with price"""
    item_name: str
    category: str
    price: float
    unit: str
    price_per_kg: Optional[float]
    premise_name: str
    chain_name: Optional[str]
    state: str
    price_date: datetime

class StoreComparison(BaseSchema):
    """Price comparison for a single store"""
    premise_code: str
    premise_name: str
    chain_name: Optional[str]
    state: str
    address: str
    items: List[GroceryItem]
    total_cost: float
    items_found: int
    items_missing: int

class GroceryCompareResponse(BaseSchema):
    """Response with grocery price comparison"""
    requested_ingredients: List[str]
    location_filter: Optional[str]
    stores: List[StoreComparison]
    cheapest_store: Optional[StoreComparison]
    average_total_cost: float
    price_range: Dict[str, float]  # min, max total costs

# Recipe Schemas
class RecipeStep(BaseSchema):
    """Individual recipe step"""
    step_number: int
    instruction: str
    instruction_bm: Optional[str]
    duration_minutes: Optional[int]
    temperature: Optional[str]

class RecipeIngredient(BaseSchema):
    """Recipe ingredient with quantity"""
    name: str
    name_bm: Optional[str]
    quantity: float
    unit: str
    category: str
    estimated_price_rm: Optional[float]

class RecipeDetail(BaseSchema):
    """Detailed recipe information"""
    id: int
    name: str
    name_bm: Optional[str]
    description: str
    description_bm: Optional[str]
    
    # Timing and difficulty
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    difficulty_level: str
    servings: int
    
    # Cost and nutrition
    estimated_cost_rm: float
    cost_per_serving: float
    nutrition: NutritionInfo
    
    # Recipe content
    ingredients: List[RecipeIngredient]
    instructions: List[RecipeStep]
    
    # Metadata
    cuisine_type: str
    is_vegetarian: bool
    is_halal: bool
    is_popular: bool
    created_at: datetime

class RecipeListItem(BaseSchema):
    """Recipe summary for listing"""
    id: int
    name: str
    name_bm: Optional[str]
    description: str
    estimated_cost_rm: float
    calories_per_serving: float
    prep_time_minutes: int
    cook_time_minutes: int
    difficulty_level: str
    servings: int
    is_vegetarian: bool
    is_halal: bool
    is_popular: bool

class RecipeSearchResponse(BaseSchema):
    """Response for recipe search/listing"""
    total_recipes: int
    recipes: List[RecipeListItem]
    filters_applied: Dict[str, Any]

# Error Schemas
class ErrorResponse(BaseSchema):
    """Standard error response"""
    error: str
    message: str
    status_code: int
    timestamp: datetime

# Health Check Schema
class HealthResponse(BaseSchema):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    uptime_seconds: Optional[float] 