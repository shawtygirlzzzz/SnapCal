"""
Database models for SnapCal+ application
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship between recipes and ingredients
recipe_ingredients = Table(
    'recipe_ingredients',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'), primary_key=True),
    Column('quantity', Float),  # Amount needed
    Column('unit', String(20))  # kg, g, cups, etc.
)

class Recipe(Base):
    """Recipe model for Malaysian dishes"""
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    name_bm = Column(String(100))  # Bahasa Malaysia name
    description = Column(Text)
    description_bm = Column(Text)  # Bahasa Malaysia description
    
    # Cooking details
    prep_time_minutes = Column(Integer, default=0)
    cook_time_minutes = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=0)
    servings = Column(Integer, default=4)
    difficulty_level = Column(String(20), default="medium")  # easy, medium, hard
    
    # Cost and nutrition (per serving)
    estimated_cost_rm = Column(Float, default=0.0)
    calories_per_serving = Column(Float, default=0.0)
    protein_g = Column(Float, default=0.0)
    carbs_g = Column(Float, default=0.0)
    fat_g = Column(Float, default=0.0)
    fiber_g = Column(Float, default=0.0)
    sodium_mg = Column(Float, default=0.0)
    
    # Recipe instructions
    instructions = Column(Text)  # JSON string of steps
    instructions_bm = Column(Text)  # Bahasa Malaysia instructions
    
    # Metadata
    cuisine_type = Column(String(50), default="Malaysian")
    is_vegetarian = Column(Boolean, default=False)
    is_halal = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ingredients = relationship("Ingredient", secondary=recipe_ingredients, back_populates="recipes")

class Ingredient(Base):
    """Ingredient model"""
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    name_bm = Column(String(100))  # Bahasa Malaysia name
    category = Column(String(50))  # vegetables, meat, spices, etc.
    
    # Nutrition per 100g
    calories_per_100g = Column(Float, default=0.0)
    protein_per_100g = Column(Float, default=0.0)
    carbs_per_100g = Column(Float, default=0.0)
    fat_per_100g = Column(Float, default=0.0)
    fiber_per_100g = Column(Float, default=0.0)
    sodium_per_100g = Column(Float, default=0.0)
    
    # Average price in RM per standard unit
    avg_price_rm = Column(Float, default=0.0)
    standard_unit = Column(String(20), default="kg")  # kg, g, pieces, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_ingredients, back_populates="ingredients")

class GroceryPrice(Base):
    """OpenDOSM PriceCatcher grocery price data"""
    __tablename__ = "grocery_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # OpenDOSM fields
    premise_code = Column(String(20), index=True)
    premise_name = Column(String(200))
    premise_address = Column(Text)
    state = Column(String(50))
    
    item_code = Column(String(20), index=True)
    item_name = Column(String(200), index=True)
    item_category = Column(String(100))
    item_subcategory = Column(String(100))
    
    price = Column(Float)
    unit = Column(String(50))
    price_date = Column(DateTime)
    
    # Processed fields
    chain_name = Column(String(100))  # Mapped from premise name (Tesco, 99 Speedmart, etc.)
    normalized_item_name = Column(String(200))  # Cleaned item name for matching
    price_per_kg = Column(Float)  # Normalized price for comparison
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FoodRecognition(Base):
    """Food recognition results from uploaded images"""
    __tablename__ = "food_recognitions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Image details
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(50))
    
    # Recognition results
    recognized_food = Column(String(200))
    recognized_food_bm = Column(String(200))  # Bahasa Malaysia name
    confidence_score = Column(Float, default=0.0)
    estimated_calories = Column(Float, default=0.0)
    estimated_weight_g = Column(Float, default=0.0)
    analysis_notes = Column(Text)  # Additional analysis information
    
    # Nutrition breakdown
    protein_g = Column(Float, default=0.0)
    carbs_g = Column(Float, default=0.0)
    fat_g = Column(Float, default=0.0)
    fiber_g = Column(Float, default=0.0)
    sodium_mg = Column(Float, default=0.0)
    
    # Processing metadata
    processing_time_ms = Column(Integer, default=0)
    model_version = Column(String(20), default="mock_v1")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MealPlan(Base):
    """Generated meal plans based on budget and preferences"""
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request parameters
    budget_rm = Column(Float, nullable=False)
    num_people = Column(Integer, default=1)
    dietary_preferences = Column(String(200))  # JSON string
    
    # Generated plan
    selected_recipes = Column(Text)  # JSON string of recipe IDs and details
    total_cost_rm = Column(Float, default=0.0)
    total_calories = Column(Float, default=0.0)
    cost_per_person = Column(Float, default=0.0)
    
    # Metadata
    generation_algorithm = Column(String(50), default="budget_optimizer_v1")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 