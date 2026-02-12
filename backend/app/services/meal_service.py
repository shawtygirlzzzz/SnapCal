"""
Meal Service - Budget-based meal planning and suggestions
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.models import Recipe, Ingredient
from app.schemas.schemas import MealSuggestion
from app.services.ai_recipe_service import ai_recipe_service
from app.core.config import settings

class MealService:
    """Service for meal planning and budget-based suggestions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_budget_meal_suggestions(
        self,
        budget_rm: float,
        num_people: int,
        dietary_preferences: List[str] = None,
        exclude_ingredients: List[str] = None
    ) -> List[MealSuggestion]:
        """
        Get meal suggestions based on budget and preferences (Hybrid AI + Database)
        
        Args:
            budget_rm: Total budget in Malaysian Ringgit
            num_people: Number of people to serve
            dietary_preferences: List of dietary preferences/restrictions
            exclude_ingredients: List of ingredients to avoid
            
        Returns:
            List of meal suggestions within budget
        """
        suggestions = []
        
        # Try AI-powered meal planning first
        if settings.USE_AI_MEAL_PLANNING and ai_recipe_service.model:
            try:
                print("🧠 Generating AI-powered meal suggestions...")
                ai_meal_plan = await ai_recipe_service.generate_meal_plan(
                    budget_rm=budget_rm,
                    num_people=num_people,
                    days=1,  # Single day for meal suggestions
                    dietary_preferences=dietary_preferences,
                    exclude_ingredients=exclude_ingredients
                )
                
                if ai_meal_plan and "daily_meals" in ai_meal_plan:
                    # Extract meals from AI response
                    daily_meals = ai_meal_plan["daily_meals"][0]["meals"]
                    
                    for meal_type, meal_data in daily_meals.items():
                        suggestions.append(MealSuggestion(
                            recipe_id=0,  # AI-generated, no DB ID
                            name=meal_data["recipe_name"],
                            name_bm=meal_data.get("recipe_name_bm"),
                            description=f"AI-generated {meal_type} dish",
                            estimated_cost_rm=meal_data["estimated_cost_rm"],
                            cost_per_person=meal_data["estimated_cost_rm"] / num_people,
                            calories_per_serving=meal_data["calories_per_serving"],
                            prep_time_minutes=meal_data["prep_time_minutes"],
                            cook_time_minutes=meal_data.get("cook_time_minutes", 20),
                            difficulty_level="medium",
                            servings=num_people,
                            is_vegetarian="vegetarian" in (dietary_preferences or []),
                            is_halal="halal" in (dietary_preferences or []) or True
                        ))
                
                if suggestions:
                    print(f"✅ Generated {len(suggestions)} AI meal suggestions")
                    return suggestions[:10]  # Limit to 10 suggestions
                    
            except Exception as e:
                print(f"⚠️ AI meal planning failed: {e}")
                print("🔄 Falling back to database recipes")
        
        # Fallback to database-based suggestions
        print("📚 Using database recipe suggestions")
        
        # Calculate budget per person
        budget_per_person = budget_rm / num_people
        
        # Start with base query
        query = self.db.query(Recipe)
        
        # Apply dietary filters
        if dietary_preferences:
            if "vegetarian" in dietary_preferences:
                query = query.filter(Recipe.is_vegetarian == True)
            if "halal" in dietary_preferences:
                query = query.filter(Recipe.is_halal == True)
        
        # Filter by budget (cost per serving should be within budget per person)
        query = query.filter(Recipe.estimated_cost_rm <= budget_per_person)
        
        # Get recipes ordered by popularity and cost efficiency
        recipes = query.order_by(
            Recipe.is_popular.desc(),
            Recipe.estimated_cost_rm.asc()
        ).limit(15).all()
        
        # Convert to meal suggestions
        suggestions = []
        for recipe in recipes:
            # Skip if contains excluded ingredients
            if exclude_ingredients and self._recipe_contains_excluded_ingredients(recipe, exclude_ingredients):
                continue
            
            suggestions.append(MealSuggestion(
                recipe_id=recipe.id,
                name=recipe.name,
                name_bm=recipe.name_bm,
                description=recipe.description or "",
                estimated_cost_rm=recipe.estimated_cost_rm,
                cost_per_person=recipe.estimated_cost_rm,
                calories_per_serving=recipe.calories_per_serving,
                prep_time_minutes=recipe.prep_time_minutes,
                cook_time_minutes=recipe.cook_time_minutes,
                difficulty_level=recipe.difficulty_level,
                servings=recipe.servings,
                is_vegetarian=recipe.is_vegetarian,
                is_halal=recipe.is_halal
            ))
        
        # Limit to top suggestions
        return suggestions[:10]
    
    async def get_popular_meals(
        self,
        limit: int = 10,
        max_cost_rm: float = None
    ) -> List[Dict[str, Any]]:
        """Get popular Malaysian meals"""
        
        query = self.db.query(Recipe).filter(Recipe.is_popular == True)
        
        if max_cost_rm:
            query = query.filter(Recipe.estimated_cost_rm <= max_cost_rm)
        
        recipes = query.order_by(
            Recipe.estimated_cost_rm.asc()
        ).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "name_bm": r.name_bm,
                "description": r.description,
                "estimated_cost_rm": r.estimated_cost_rm,
                "calories_per_serving": r.calories_per_serving,
                "prep_time_minutes": r.prep_time_minutes,
                "difficulty_level": r.difficulty_level,
                "is_vegetarian": r.is_vegetarian,
                "is_halal": r.is_halal
            }
            for r in recipes
        ]
    
    async def analyze_budget_breakdown(
        self,
        budget_rm: float,
        num_people: int
    ) -> Dict[str, Any]:
        """Analyze budget breakdown for meal planning"""
        
        budget_per_person = budget_rm / num_people
        
        # Get recipe statistics
        total_recipes = self.db.query(Recipe).count()
        affordable_recipes = self.db.query(Recipe).filter(
            Recipe.estimated_cost_rm <= budget_per_person
        ).count()
        
        # Get cost ranges
        recipes_by_cost = {
            "budget_friendly": self.db.query(Recipe).filter(
                Recipe.estimated_cost_rm <= budget_per_person * 0.7
            ).count(),
            "moderate": self.db.query(Recipe).filter(
                Recipe.estimated_cost_rm > budget_per_person * 0.7,
                Recipe.estimated_cost_rm <= budget_per_person
            ).count(),
            "over_budget": self.db.query(Recipe).filter(
                Recipe.estimated_cost_rm > budget_per_person
            ).count()
        }
        
        # Get average costs
        avg_recipe_cost = self.db.query(Recipe).with_entities(
            Recipe.estimated_cost_rm
        ).all()
        
        if avg_recipe_cost:
            avg_cost = sum(r[0] for r in avg_recipe_cost) / len(avg_recipe_cost)
        else:
            avg_cost = 0.0
        
        return {
            "budget_rm": budget_rm,
            "num_people": num_people,
            "budget_per_person": round(budget_per_person, 2),
            "total_recipes": total_recipes,
            "affordable_recipes": affordable_recipes,
            "affordability_percentage": round((affordable_recipes / total_recipes * 100) if total_recipes > 0 else 0, 1),
            "cost_breakdown": recipes_by_cost,
            "average_recipe_cost": round(avg_cost, 2),
            "recommendations": self._generate_budget_recommendations(budget_per_person, avg_cost)
        }
    
    def _recipe_contains_excluded_ingredients(
        self,
        recipe: Recipe,
        exclude_ingredients: List[str]
    ) -> bool:
        """Check if recipe contains any excluded ingredients"""
        
        recipe_ingredient_names = [
            ingredient.name.lower() for ingredient in recipe.ingredients
        ]
        
        for excluded in exclude_ingredients:
            if excluded.lower() in recipe_ingredient_names:
                return True
        
        return False
    
    def _generate_budget_recommendations(
        self,
        budget_per_person: float,
        avg_cost: float
    ) -> List[str]:
        """Generate budget recommendations based on analysis"""
        
        recommendations = []
        
        if budget_per_person < 5.0:
            recommendations.append("Consider simple dishes like nasi goreng or mee goreng for budget-friendly options")
            recommendations.append("Look for recipes using affordable ingredients like rice, noodles, and eggs")
        elif budget_per_person < 10.0:
            recommendations.append("You have a moderate budget for most Malaysian dishes")
            recommendations.append("Consider dishes with chicken or tofu as protein sources")
        else:
            recommendations.append("Your budget allows for premium ingredients and elaborate dishes")
            recommendations.append("You can explore dishes with seafood, beef, or multiple protein sources")
        
        if budget_per_person < avg_cost:
            recommendations.append(f"Your budget is below average (RM {avg_cost:.2f}). Focus on rice and noodle-based dishes")
        else:
            recommendations.append("Your budget is above average, giving you plenty of meal options")
        
        return recommendations 