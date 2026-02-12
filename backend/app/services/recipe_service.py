"""
Recipe Service - Recipe information, search, and detailed data
"""

import json
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional, Dict, Any
from app.models.models import Recipe, Ingredient, recipe_ingredients
from app.schemas.schemas import (
    RecipeDetail, RecipeListItem, RecipeSearchResponse, 
    RecipeStep, RecipeIngredient, NutritionInfo
)

class RecipeService:
    """Service for recipe information and search"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_recipe_detail(
        self,
        recipe_id: int,
        language: str = "en"
    ) -> Optional[RecipeDetail]:
        """
        Get detailed recipe information by ID
        
        Args:
            recipe_id: Recipe ID
            language: Language preference (en/bm)
            
        Returns:
            Detailed recipe information or None if not found
        """
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        
        if not recipe:
            return None
        
        # Parse instructions JSON
        instructions = self._parse_recipe_instructions(recipe.instructions, recipe.instructions_bm, language)
        
        # Get ingredients with quantities
        ingredients = self._get_recipe_ingredients_with_quantities(recipe, None)
        
        # Build nutrition info
        nutrition = NutritionInfo(
            calories=recipe.calories_per_serving,
            protein_g=recipe.protein_g,
            carbs_g=recipe.carbs_g,
            fat_g=recipe.fat_g,
            fiber_g=recipe.fiber_g,
            sodium_mg=recipe.sodium_mg
        )
        
        return RecipeDetail(
            id=recipe.id,
            name=recipe.name_bm if language == "bm" and recipe.name_bm else recipe.name,
            name_bm=recipe.name_bm,
            description=recipe.description_bm if language == "bm" and recipe.description_bm else recipe.description,
            description_bm=recipe.description_bm,
            prep_time_minutes=recipe.prep_time_minutes,
            cook_time_minutes=recipe.cook_time_minutes,
            total_time_minutes=recipe.total_time_minutes,
            difficulty_level=recipe.difficulty_level,
            servings=recipe.servings,
            estimated_cost_rm=recipe.estimated_cost_rm,
            cost_per_serving=recipe.estimated_cost_rm,
            nutrition=nutrition,
            ingredients=ingredients,
            instructions=instructions,
            cuisine_type=recipe.cuisine_type,
            is_vegetarian=recipe.is_vegetarian,
            is_halal=recipe.is_halal,
            is_popular=recipe.is_popular,
            created_at=recipe.created_at
        )
    
    async def get_recipe_by_name(
        self,
        recipe_name: str,
        language: str = "en"
    ) -> Optional[RecipeDetail]:
        """Get recipe by name"""
        
        # Search by name or name_bm
        recipe = self.db.query(Recipe).filter(
            or_(
                Recipe.name.ilike(f"%{recipe_name}%"),
                Recipe.name_bm.ilike(f"%{recipe_name}%")
            )
        ).first()
        
        if not recipe:
            return None
        
        return await self.get_recipe_detail(recipe.id, language)
    
    async def search_recipes(
        self,
        filters: Dict[str, Any],
        limit: int = 20,
        offset: int = 0
    ) -> RecipeSearchResponse:
        """
        Search recipes with filters
        
        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Search results with recipes and metadata
        """
        query = self.db.query(Recipe)
        
        # Apply text search
        if filters.get("search_query"):
            search_term = filters["search_query"]
            query = query.filter(
                or_(
                    Recipe.name.ilike(f"%{search_term}%"),
                    Recipe.name_bm.ilike(f"%{search_term}%"),
                    Recipe.description.ilike(f"%{search_term}%"),
                    Recipe.description_bm.ilike(f"%{search_term}%")
                )
            )
        
        # Apply filters
        if filters.get("cuisine_type"):
            query = query.filter(Recipe.cuisine_type.ilike(f"%{filters['cuisine_type']}%"))
        
        if filters.get("max_cost_rm"):
            query = query.filter(Recipe.estimated_cost_rm <= filters["max_cost_rm"])
        
        if filters.get("max_prep_time"):
            query = query.filter(Recipe.prep_time_minutes <= filters["max_prep_time"])
        
        if filters.get("difficulty"):
            query = query.filter(Recipe.difficulty_level == filters["difficulty"])
        
        if filters.get("is_vegetarian") is not None:
            query = query.filter(Recipe.is_vegetarian == filters["is_vegetarian"])
        
        if filters.get("is_halal") is not None:
            query = query.filter(Recipe.is_halal == filters["is_halal"])
        
        # Get total count
        total_recipes = query.count()
        
        # Apply pagination and ordering
        recipes = query.order_by(
            Recipe.is_popular.desc(),
            Recipe.estimated_cost_rm.asc()
        ).offset(offset).limit(limit).all()
        
        # Convert to list items
        recipe_items = [
            RecipeListItem(
                id=r.id,
                name=r.name,
                name_bm=r.name_bm,
                description=r.description or "",
                estimated_cost_rm=r.estimated_cost_rm,
                calories_per_serving=r.calories_per_serving,
                prep_time_minutes=r.prep_time_minutes,
                cook_time_minutes=r.cook_time_minutes,
                difficulty_level=r.difficulty_level,
                servings=r.servings,
                is_vegetarian=r.is_vegetarian,
                is_halal=r.is_halal,
                is_popular=r.is_popular
            )
            for r in recipes
        ]
        
        return RecipeSearchResponse(
            total_recipes=total_recipes,
            recipes=recipe_items,
            filters_applied={k: v for k, v in filters.items() if v is not None}
        )
    
    async def get_popular_recipes(self, limit: int = 10) -> List[RecipeListItem]:
        """Get popular recipes"""
        
        recipes = self.db.query(Recipe).filter(
            Recipe.is_popular == True
        ).order_by(
            Recipe.estimated_cost_rm.asc()
        ).limit(limit).all()
        
        return [
            RecipeListItem(
                id=r.id,
                name=r.name,
                name_bm=r.name_bm,
                description=r.description or "",
                estimated_cost_rm=r.estimated_cost_rm,
                calories_per_serving=r.calories_per_serving,
                prep_time_minutes=r.prep_time_minutes,
                cook_time_minutes=r.cook_time_minutes,
                difficulty_level=r.difficulty_level,
                servings=r.servings,
                is_vegetarian=r.is_vegetarian,
                is_halal=r.is_halal,
                is_popular=r.is_popular
            )
            for r in recipes
        ]
    
    async def get_recipe_categories(self) -> Dict[str, Any]:
        """Get available recipe categories"""
        
        # Get unique cuisine types
        cuisine_types = self.db.query(Recipe.cuisine_type).distinct().all()
        cuisine_types = [ct[0] for ct in cuisine_types if ct[0]]
        
        # Get difficulty levels
        difficulty_levels = self.db.query(Recipe.difficulty_level).distinct().all()
        difficulty_levels = [dl[0] for dl in difficulty_levels if dl[0]]
        
        return {
            "cuisine_types": cuisine_types,
            "difficulty_levels": difficulty_levels,
            "dietary_options": ["vegetarian", "halal"],
            "cost_ranges": [
                {"label": "Budget (< RM 5)", "max_cost": 5.0},
                {"label": "Moderate (RM 5-10)", "min_cost": 5.0, "max_cost": 10.0},
                {"label": "Premium (> RM 10)", "min_cost": 10.0}
            ]
        }
    
    async def get_recipe_ingredients(
        self,
        recipe_id: int,
        target_servings: Optional[int] = None
    ) -> Optional[List[RecipeIngredient]]:
        """Get ingredients for a recipe, optionally scaled"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return None
        
        return self._get_recipe_ingredients_with_quantities(recipe, target_servings)
    
    async def get_recipe_nutrition(
        self,
        recipe_id: int,
        target_servings: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get nutrition information for a recipe"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return None
        
        # Calculate scaling factor
        scale_factor = 1.0
        if target_servings and target_servings != recipe.servings:
            scale_factor = target_servings / recipe.servings
        
        return {
            "recipe_id": recipe_id,
            "servings": target_servings or recipe.servings,
            "per_serving": {
                "calories": recipe.calories_per_serving,
                "protein_g": recipe.protein_g,
                "carbs_g": recipe.carbs_g,
                "fat_g": recipe.fat_g,
                "fiber_g": recipe.fiber_g,
                "sodium_mg": recipe.sodium_mg
            },
            "total": {
                "calories": round(recipe.calories_per_serving * (target_servings or recipe.servings), 1),
                "protein_g": round(recipe.protein_g * (target_servings or recipe.servings), 1),
                "carbs_g": round(recipe.carbs_g * (target_servings or recipe.servings), 1),
                "fat_g": round(recipe.fat_g * (target_servings or recipe.servings), 1),
                "fiber_g": round(recipe.fiber_g * (target_servings or recipe.servings), 1),
                "sodium_mg": round(recipe.sodium_mg * (target_servings or recipe.servings), 1)
            }
        }
    
    def _parse_recipe_instructions(
        self,
        instructions_en: str,
        instructions_bm: str,
        language: str
    ) -> List[RecipeStep]:
        """Parse recipe instructions from JSON string"""
        
        try:
            # Try to parse as JSON first
            instructions_text = instructions_bm if language == "bm" and instructions_bm else instructions_en
            
            if instructions_text:
                # If it's already JSON, parse it
                if instructions_text.startswith('['):
                    steps_data = json.loads(instructions_text)
                    return [
                        RecipeStep(
                            step_number=i + 1,
                            instruction=step.get("instruction", ""),
                            instruction_bm=step.get("instruction_bm"),
                            duration_minutes=step.get("duration_minutes"),
                            temperature=step.get("temperature")
                        )
                        for i, step in enumerate(steps_data)
                    ]
                else:
                    # If it's plain text, split by lines/sentences
                    steps = instructions_text.split('\n')
                    return [
                        RecipeStep(
                            step_number=i + 1,
                            instruction=step.strip(),
                            instruction_bm=None,
                            duration_minutes=None,
                            temperature=None
                        )
                        for i, step in enumerate(steps) if step.strip()
                    ]
            
            return []
            
        except json.JSONDecodeError:
            # Fallback to plain text parsing
            steps = instructions_en.split('\n') if instructions_en else []
            return [
                RecipeStep(
                    step_number=i + 1,
                    instruction=step.strip(),
                    instruction_bm=None,
                    duration_minutes=None,
                    temperature=None
                )
                for i, step in enumerate(steps) if step.strip()
            ]
    
    def _get_recipe_ingredients_with_quantities(
        self,
        recipe: Recipe,
        target_servings: Optional[int]
    ) -> List[RecipeIngredient]:
        """Get ingredients with quantities for a recipe"""
        
        # Calculate scaling factor
        scale_factor = 1.0
        if target_servings and target_servings != recipe.servings:
            scale_factor = target_servings / recipe.servings
        
        ingredients = []
        
        # Get ingredients from the many-to-many relationship
        for ingredient in recipe.ingredients:
            # Get quantity from association table
            association = self.db.query(recipe_ingredients).filter(
                and_(
                    recipe_ingredients.c.recipe_id == recipe.id,
                    recipe_ingredients.c.ingredient_id == ingredient.id
                )
            ).first()
            
            if association:
                quantity = association.quantity * scale_factor if association.quantity else 0.0
                unit = association.unit or "piece"
            else:
                quantity = 0.0
                unit = "piece"
            
            ingredients.append(RecipeIngredient(
                name=ingredient.name,
                name_bm=ingredient.name_bm,
                quantity=round(quantity, 2),
                unit=unit,
                category=ingredient.category or "Other",
                estimated_price_rm=ingredient.avg_price_rm
            ))
        
        return ingredients 