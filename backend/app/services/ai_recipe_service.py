"""
AI Recipe Service - Gemini-powered recipe generation and meal planning
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from app.core.config import settings
from app.services.cache_service import cache_service

class AIRecipeService:
    """
    AI-powered recipe generation and meal planning using Gemini 2.0 Flash
    """
    
    def __init__(self):
        self.model = None
        self.model_version = "gemini-2.0-flash"
        
        # Initialize Gemini if available
        if settings.GEMINI_API_KEY and settings.USE_GEMINI_AI:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
                print("✅ AI Recipe Service initialized with Gemini 2.0 Flash")
            except Exception as e:
                print(f"⚠️ Failed to initialize AI Recipe Service: {e}")
                self.model = None
    
    async def generate_recipe(
        self,
        cuisine_type: str = "Malaysian",
        budget_rm: float = 20.0,
        servings: int = 4,
        dietary_preferences: List[str] = None,
        available_ingredients: List[str] = None,
        cooking_time_limit: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a recipe using AI based on parameters
        
        Args:
            cuisine_type: Type of cuisine (Malaysian, Chinese, Indian, etc.)
            budget_rm: Budget in Malaysian Ringgit
            servings: Number of servings
            dietary_preferences: List of dietary preferences/restrictions
            available_ingredients: List of ingredients user already has
            cooking_time_limit: Maximum cooking time in minutes
            
        Returns:
            Generated recipe data or None if failed
        """
        
        # Check cache first
        cache_params = {
            "cuisine_type": cuisine_type,
            "budget_rm": budget_rm,
            "servings": servings,
            "dietary_preferences": dietary_preferences or [],
            "available_ingredients": available_ingredients or [],
            "cooking_time_limit": cooking_time_limit
        }
        
        cached_result = await cache_service.get_recipe_cache(**cache_params)
        if cached_result:
            print("📦 Recipe served from cache")
            return cached_result
        
        if not self.model:
            print("⚠️ AI model not available, cannot generate recipe")
            return None
        
        try:
            prompt = self._create_recipe_generation_prompt(
                cuisine_type, budget_rm, servings, dietary_preferences,
                available_ingredients, cooking_time_limit
            )
            
            # Generate recipe with Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse and validate response
            recipe_data = self._parse_recipe_response(response.text)
            
            if recipe_data:
                # Cache the result
                await cache_service.set_recipe_cache(recipe_data, **cache_params)
                print("🤖 Recipe generated with AI")
                return recipe_data
            else:
                print("❌ Failed to parse AI recipe response")
                return None
                
        except Exception as e:
            print(f"❌ AI recipe generation failed: {e}")
            return None
    
    async def generate_meal_plan(
        self,
        budget_rm: float,
        num_people: int,
        days: int = 7,
        dietary_preferences: List[str] = None,
        exclude_ingredients: List[str] = None,
        cuisine_preferences: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an intelligent meal plan using AI
        
        Args:
            budget_rm: Total budget in RM
            num_people: Number of people
            days: Number of days to plan for
            dietary_preferences: Dietary restrictions/preferences
            exclude_ingredients: Ingredients to avoid
            cuisine_preferences: Preferred cuisine types
            
        Returns:
            Generated meal plan or None if failed
        """
        
        # Check cache first
        cache_params = {
            "budget_rm": budget_rm,
            "num_people": num_people,
            "days": days,
            "dietary_preferences": dietary_preferences or [],
            "exclude_ingredients": exclude_ingredients or [],
            "cuisine_preferences": cuisine_preferences or []
        }
        
        cached_result = await cache_service.get_meal_plan_cache(**cache_params)
        if cached_result:
            print("📦 Meal plan served from cache")
            return cached_result
        
        if not self.model:
            print("⚠️ AI model not available, cannot generate meal plan")
            return None
        
        try:
            prompt = self._create_meal_plan_prompt(
                budget_rm, num_people, days, dietary_preferences,
                exclude_ingredients, cuisine_preferences
            )
            
            # Generate meal plan with Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse and validate response
            meal_plan_data = self._parse_meal_plan_response(response.text)
            
            if meal_plan_data:
                # Cache the result
                await cache_service.set_meal_plan_cache(meal_plan_data, **cache_params)
                print("🧠 Meal plan generated with AI")
                return meal_plan_data
            else:
                print("❌ Failed to parse AI meal plan response")
                return None
                
        except Exception as e:
            print(f"❌ AI meal plan generation failed: {e}")
            return None
    
    def _create_recipe_generation_prompt(
        self,
        cuisine_type: str,
        budget_rm: float,
        servings: int,
        dietary_preferences: List[str],
        available_ingredients: List[str],
        cooking_time_limit: int
    ) -> str:
        """Create prompt for recipe generation"""
        
        dietary_str = ", ".join(dietary_preferences) if dietary_preferences else "None"
        ingredients_str = ", ".join(available_ingredients) if available_ingredients else "None"
        time_constraint = f"Maximum cooking time: {cooking_time_limit} minutes" if cooking_time_limit else "No time limit"
        
        return f"""Generate a {cuisine_type} recipe with the following requirements:

Budget: RM {budget_rm} total
Servings: {servings} people
Dietary preferences: {dietary_str}
Available ingredients: {ingredients_str}
Time constraint: {time_constraint}

Please provide a detailed recipe in the following JSON format:

{{
  "recipe_name": "Name of the dish",
  "recipe_name_bm": "Nama dalam Bahasa Malaysia (if Malaysian cuisine)",
  "description": "Brief description of the dish",
  "cuisine_type": "{cuisine_type}",
  "difficulty_level": "easy/medium/hard",
  "prep_time_minutes": 20,
  "cook_time_minutes": 30,
  "total_time_minutes": 50,
  "servings": {servings},
  "estimated_cost_rm": {budget_rm},
  "cost_per_serving": 5.0,
  "nutrition_per_serving": {{
    "calories": 350,
    "protein_g": 15.0,
    "carbs_g": 45.0,
    "fat_g": 12.0,
    "fiber_g": 3.0,
    "sodium_mg": 600
  }},
  "ingredients": [
    {{
      "name": "Ingredient name",
      "quantity": 200,
      "unit": "g",
      "estimated_price_rm": 3.50
    }}
  ],
  "instructions": [
    {{
      "step": 1,
      "instruction": "Detailed step description",
      "duration_minutes": 5,
      "tips": "Optional cooking tips"
    }}
  ],
  "is_vegetarian": false,
  "is_halal": true,
  "cooking_tips": "Additional tips and variations",
  "storage_instructions": "How to store leftovers"
}}

Requirements:
1. Use authentic {cuisine_type} flavors and techniques
2. Stay within the RM {budget_rm} budget using realistic Malaysian prices
3. Consider dietary preferences: {dietary_str}
4. Optimize nutrition balance for {servings} people
5. Provide step-by-step instructions with timing
6. Include practical cooking tips
7. If available ingredients are provided, try to incorporate them

Return only the JSON object, no additional text."""

    def _create_meal_plan_prompt(
        self,
        budget_rm: float,
        num_people: int,
        days: int,
        dietary_preferences: List[str],
        exclude_ingredients: List[str],
        cuisine_preferences: List[str]
    ) -> str:
        """Create prompt for meal planning"""
        
        dietary_str = ", ".join(dietary_preferences) if dietary_preferences else "None"
        exclude_str = ", ".join(exclude_ingredients) if exclude_ingredients else "None"
        cuisine_str = ", ".join(cuisine_preferences) if cuisine_preferences else "Malaysian, Asian, International"
        
        return f"""Create an intelligent meal plan with the following requirements:

Total Budget: RM {budget_rm}
People: {num_people}
Duration: {days} days
Dietary preferences: {dietary_str}
Avoid ingredients: {exclude_str}
Cuisine preferences: {cuisine_str}

Please generate a comprehensive meal plan in the following JSON format:

{{
  "meal_plan_summary": {{
    "total_budget_rm": {budget_rm},
    "budget_per_person_per_day": 12.5,
    "num_people": {num_people},
    "days": {days},
    "estimated_total_cost": 350.0,
    "budget_utilization_percentage": 95.5
  }},
  "daily_meals": [
    {{
      "day": 1,
      "date": "2024-01-01",
      "meals": {{
        "breakfast": {{
          "recipe_name": "Malaysian Breakfast Dish",
          "estimated_cost_rm": 8.0,
          "prep_time_minutes": 15,
          "calories_per_serving": 300,
          "key_ingredients": ["eggs", "bread", "coffee"]
        }},
        "lunch": {{
          "recipe_name": "Lunch Dish",
          "estimated_cost_rm": 12.0,
          "prep_time_minutes": 30,
          "calories_per_serving": 450,
          "key_ingredients": ["rice", "chicken", "vegetables"]
        }},
        "dinner": {{
          "recipe_name": "Dinner Dish", 
          "estimated_cost_rm": 15.0,
          "prep_time_minutes": 45,
          "calories_per_serving": 500,
          "key_ingredients": ["fish", "vegetables", "spices"]
        }}
      }},
      "daily_nutrition": {{
        "total_calories": 1250,
        "protein_g": 45.0,
        "carbs_g": 150.0,
        "fat_g": 35.0
      }},
      "daily_cost_rm": 35.0
    }}
  ],
  "shopping_list": [
    {{
      "ingredient": "Rice",
      "total_quantity": "2 kg",
      "estimated_cost_rm": 5.0,
      "store_suggestions": ["99 Speedmart", "Tesco"]
    }}
  ],
  "budget_breakdown": {{
    "groceries_rm": 280.0,
    "contingency_rm": 20.0,
    "savings_rm": 50.0
  }},
  "nutrition_analysis": {{
    "daily_avg_calories": 1200,
    "weekly_protein_g": 315.0,
    "nutrition_balance": "Well-balanced with adequate protein and vegetables"
  }},
  "cooking_schedule": {{
    "meal_prep_days": ["Sunday"],
    "quick_meals": ["Monday breakfast", "Wednesday lunch"],
    "cooking_tips": "Prepare rice in bulk, marinate proteins in advance"
  }}
}}

Requirements:
1. Optimize for Malaysian grocery prices and availability
2. Balance nutrition across all {days} days
3. Respect dietary preferences: {dietary_str}
4. Avoid ingredients: {exclude_str}
5. Focus on cuisine types: {cuisine_str}
6. Minimize food waste through ingredient reuse
7. Include practical meal prep suggestions
8. Provide realistic cooking times for working families
9. Stay within budget with 5% buffer for price variations
10. Consider seasonal ingredients for better prices

Return only the JSON object, no additional text."""

    def _parse_recipe_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse and validate recipe response from AI"""
        try:
            # Clean up response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            recipe_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["recipe_name", "ingredients", "instructions", "estimated_cost_rm"]
            for field in required_fields:
                if field not in recipe_data:
                    print(f"❌ Missing required field: {field}")
                    return None
            
            # Add metadata
            recipe_data["generated_by"] = "ai"
            recipe_data["model_version"] = self.model_version
            
            return recipe_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse recipe JSON: {e}")
            print(f"Raw response: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Recipe parsing error: {e}")
            return None
    
    def _parse_meal_plan_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse and validate meal plan response from AI"""
        try:
            # Clean up response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            meal_plan_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["meal_plan_summary", "daily_meals", "shopping_list"]
            for field in required_fields:
                if field not in meal_plan_data:
                    print(f"❌ Missing required field: {field}")
                    return None
            
            # Add metadata
            meal_plan_data["generated_by"] = "ai"
            meal_plan_data["model_version"] = self.model_version
            
            return meal_plan_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse meal plan JSON: {e}")
            print(f"Raw response: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Meal plan parsing error: {e}")
            return None

# Global AI recipe service instance
ai_recipe_service = AIRecipeService() 