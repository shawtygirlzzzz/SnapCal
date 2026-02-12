"""
Database seeding script with Malaysian recipes and ingredients
"""

import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, Recipe, Ingredient, recipe_ingredients

def create_sample_ingredients(db: Session):
    """Create sample ingredients"""
    
    ingredients_data = [
        {
            "name": "Rice",
            "name_bm": "Beras",
            "category": "Grains",
            "calories_per_100g": 130,
            "protein_per_100g": 2.7,
            "carbs_per_100g": 28,
            "fat_per_100g": 0.3,
            "fiber_per_100g": 0.4,
            "sodium_per_100g": 5,
            "avg_price_rm": 2.50,
            "standard_unit": "kg"
        },
        {
            "name": "Chicken Breast",
            "name_bm": "Daging Ayam",
            "category": "Meat",
            "calories_per_100g": 165,
            "protein_per_100g": 31,
            "carbs_per_100g": 0,
            "fat_per_100g": 3.6,
            "fiber_per_100g": 0,
            "sodium_per_100g": 74,
            "avg_price_rm": 12.50,
            "standard_unit": "kg"
        },
        {
            "name": "Coconut Milk",
            "name_bm": "Santan",
            "category": "Dairy",
            "calories_per_100g": 230,
            "protein_per_100g": 2.3,
            "carbs_per_100g": 6,
            "fat_per_100g": 24,
            "fiber_per_100g": 0,
            "sodium_per_100g": 15,
            "avg_price_rm": 2.90,
            "standard_unit": "can"
        },
        {
            "name": "Onion",
            "name_bm": "Bawang",
            "category": "Vegetables",
            "calories_per_100g": 40,
            "protein_per_100g": 1.1,
            "carbs_per_100g": 9.3,
            "fat_per_100g": 0.1,
            "fiber_per_100g": 1.7,
            "sodium_per_100g": 4,
            "avg_price_rm": 4.20,
            "standard_unit": "kg"
        },
        {
            "name": "Garlic",
            "name_bm": "Bawang Putih",
            "category": "Vegetables",
            "calories_per_100g": 149,
            "protein_per_100g": 6.4,
            "carbs_per_100g": 33,
            "fat_per_100g": 0.5,
            "fiber_per_100g": 2.1,
            "sodium_per_100g": 17,
            "avg_price_rm": 20.00,
            "standard_unit": "kg"
        },
        {
            "name": "Chili",
            "name_bm": "Cili",
            "category": "Spices",
            "calories_per_100g": 40,
            "protein_per_100g": 1.9,
            "carbs_per_100g": 7.3,
            "fat_per_100g": 0.4,
            "fiber_per_100g": 1.5,
            "sodium_per_100g": 9,
            "avg_price_rm": 8.00,
            "standard_unit": "kg"
        },
        {
            "name": "Pandan Leaves",
            "name_bm": "Daun Pandan",
            "category": "Herbs",
            "calories_per_100g": 20,
            "protein_per_100g": 1.0,
            "carbs_per_100g": 4.0,
            "fat_per_100g": 0.1,
            "fiber_per_100g": 1.0,
            "sodium_per_100g": 2,
            "avg_price_rm": 3.00,
            "standard_unit": "bunch"
        },
        {
            "name": "Anchovies",
            "name_bm": "Ikan Bilis",
            "category": "Seafood",
            "calories_per_100g": 210,
            "protein_per_100g": 25,
            "carbs_per_100g": 0,
            "fat_per_100g": 8,
            "fiber_per_100g": 0,
            "sodium_per_100g": 2000,
            "avg_price_rm": 25.00,
            "standard_unit": "kg"
        },
        {
            "name": "Peanuts",
            "name_bm": "Kacang Tanah",
            "category": "Nuts",
            "calories_per_100g": 567,
            "protein_per_100g": 26,
            "carbs_per_100g": 16,
            "fat_per_100g": 49,
            "fiber_per_100g": 8.5,
            "sodium_per_100g": 18,
            "avg_price_rm": 8.00,
            "standard_unit": "kg"
        },
        {
            "name": "Cucumber",
            "name_bm": "Timun",
            "category": "Vegetables",
            "calories_per_100g": 16,
            "protein_per_100g": 0.7,
            "carbs_per_100g": 3.6,
            "fat_per_100g": 0.1,
            "fiber_per_100g": 0.5,
            "sodium_per_100g": 2,
            "avg_price_rm": 3.50,
            "standard_unit": "kg"
        },
        {
            "name": "Beef",
            "name_bm": "Daging Lembu",
            "category": "Meat",
            "calories_per_100g": 250,
            "protein_per_100g": 26,
            "carbs_per_100g": 0,
            "fat_per_100g": 15,
            "fiber_per_100g": 0,
            "sodium_per_100g": 72,
            "avg_price_rm": 35.00,
            "standard_unit": "kg"
        },
        {
            "name": "Cooking Oil",
            "name_bm": "Minyak Masak",
            "category": "Cooking",
            "calories_per_100g": 884,
            "protein_per_100g": 0,
            "carbs_per_100g": 0,
            "fat_per_100g": 100,
            "fiber_per_100g": 0,
            "sodium_per_100g": 0,
            "avg_price_rm": 6.80,
            "standard_unit": "liter"
        }
    ]
    
    created_ingredients = {}
    
    for ing_data in ingredients_data:
        # Check if ingredient already exists
        existing = db.query(Ingredient).filter(Ingredient.name == ing_data["name"]).first()
        if not existing:
            ingredient = Ingredient(**ing_data)
            db.add(ingredient)
            db.flush()
            created_ingredients[ing_data["name"]] = ingredient
        else:
            created_ingredients[ing_data["name"]] = existing
    
    db.commit()
    return created_ingredients

def create_sample_recipes(db: Session, ingredients: dict):
    """Create sample Malaysian recipes"""
    
    recipes_data = [
        {
            "name": "Nasi Lemak",
            "name_bm": "Nasi Lemak",
            "description": "Traditional Malaysian coconut rice dish served with sambal, anchovies, peanuts, and cucumber",
            "description_bm": "Nasi tradisional Malaysia yang dimasak dengan santan, disajikan dengan sambal, ikan bilis, kacang tanah, dan timun",
            "prep_time_minutes": 30,
            "cook_time_minutes": 45,
            "total_time_minutes": 75,
            "servings": 4,
            "difficulty_level": "medium",
            "estimated_cost_rm": 8.50,
            "calories_per_serving": 350,
            "protein_g": 8.0,
            "carbs_g": 45.0,
            "fat_g": 15.0,
            "fiber_g": 2.0,
            "sodium_mg": 450,
            "instructions": """1. Wash rice and drain well
2. In a pot, combine rice with coconut milk and pandan leaves
3. Add salt and bring to boil
4. Reduce heat and simmer until rice is cooked
5. Prepare sambal by blending chili, onion, and garlic
6. Fry sambal until fragrant
7. Deep fry anchovies and peanuts separately
8. Serve rice with sambal, anchovies, peanuts, and sliced cucumber""",
            "cuisine_type": "Malaysian",
            "is_vegetarian": False,
            "is_halal": True,
            "is_popular": True,
            "ingredients": [
                {"name": "Rice", "quantity": 300, "unit": "g"},
                {"name": "Coconut Milk", "quantity": 1, "unit": "can"},
                {"name": "Pandan Leaves", "quantity": 3, "unit": "pieces"},
                {"name": "Chili", "quantity": 100, "unit": "g"},
                {"name": "Onion", "quantity": 150, "unit": "g"},
                {"name": "Garlic", "quantity": 30, "unit": "g"},
                {"name": "Anchovies", "quantity": 50, "unit": "g"},
                {"name": "Peanuts", "quantity": 100, "unit": "g"},
                {"name": "Cucumber", "quantity": 200, "unit": "g"}
            ]
        },
        {
            "name": "Beef Rendang",
            "name_bm": "Rendang Daging",
            "description": "Slow-cooked beef in coconut milk and spices, a signature dish of Malaysia",
            "description_bm": "Daging lembu yang dimasak perlahan-lahan dengan santan dan rempah ratus, hidangan kebanggaan Malaysia",
            "prep_time_minutes": 45,
            "cook_time_minutes": 180,
            "total_time_minutes": 225,
            "servings": 6,
            "difficulty_level": "hard",
            "estimated_cost_rm": 25.00,
            "calories_per_serving": 280,
            "protein_g": 25.0,
            "carbs_g": 8.0,
            "fat_g": 18.0,
            "fiber_g": 1.5,
            "sodium_mg": 380,
            "instructions": """1. Cut beef into chunks
2. Blend chili, onion, garlic into paste
3. Heat oil and fry paste until fragrant
4. Add beef and stir-fry until sealed
5. Add coconut milk gradually
6. Simmer on low heat for 2-3 hours until tender
7. Stir occasionally and add more coconut milk if needed
8. Cook until sauce is thick and dark
9. Serve with steamed rice""",
            "cuisine_type": "Malaysian",
            "is_vegetarian": False,
            "is_halal": True,
            "is_popular": True,
            "ingredients": [
                {"name": "Beef", "quantity": 1000, "unit": "g"},
                {"name": "Coconut Milk", "quantity": 3, "unit": "can"},
                {"name": "Chili", "quantity": 200, "unit": "g"},
                {"name": "Onion", "quantity": 300, "unit": "g"},
                {"name": "Garlic", "quantity": 50, "unit": "g"},
                {"name": "Cooking Oil", "quantity": 100, "unit": "ml"}
            ]
        },
        {
            "name": "Fried Rice",
            "name_bm": "Nasi Goreng",
            "description": "Simple Malaysian-style fried rice with chicken and vegetables",
            "description_bm": "Nasi goreng gaya Malaysia yang mudah dengan ayam dan sayuran",
            "prep_time_minutes": 15,
            "cook_time_minutes": 20,
            "total_time_minutes": 35,
            "servings": 4,
            "difficulty_level": "easy",
            "estimated_cost_rm": 6.00,
            "calories_per_serving": 250,
            "protein_g": 12.0,
            "carbs_g": 38.0,
            "fat_g": 8.0,
            "fiber_g": 1.5,
            "sodium_mg": 400,
            "instructions": """1. Heat oil in wok or large pan
2. Fry garlic and onion until fragrant
3. Add chicken pieces and cook until done
4. Add cold cooked rice and stir-fry
5. Season with soy sauce and salt
6. Add vegetables and stir
7. Serve hot with cucumber slices""",
            "cuisine_type": "Malaysian",
            "is_vegetarian": False,
            "is_halal": True,
            "is_popular": True,
            "ingredients": [
                {"name": "Rice", "quantity": 400, "unit": "g"},
                {"name": "Chicken Breast", "quantity": 200, "unit": "g"},
                {"name": "Onion", "quantity": 100, "unit": "g"},
                {"name": "Garlic", "quantity": 20, "unit": "g"},
                {"name": "Cooking Oil", "quantity": 50, "unit": "ml"}
            ]
        }
    ]
    
    for recipe_data in recipes_data:
        # Extract ingredients list
        recipe_ingredients_list = recipe_data.pop("ingredients")
        
        # Check if recipe already exists
        existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
        if existing:
            continue
        
        # Create recipe
        recipe = Recipe(**recipe_data)
        db.add(recipe)
        db.flush()
        
        # Add ingredients to recipe
        for ing_data in recipe_ingredients_list:
            ingredient = ingredients.get(ing_data["name"])
            if ingredient:
                # Insert into association table
                stmt = recipe_ingredients.insert().values(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=ing_data["quantity"],
                    unit=ing_data["unit"]
                )
                db.execute(stmt)
    
    db.commit()

def seed_database():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed ingredients
        print("📦 Creating ingredients...")
        ingredients = create_sample_ingredients(db)
        print(f"✅ Created {len(ingredients)} ingredients")
        
        # Seed recipes
        print("🍽️ Creating recipes...")
        create_sample_recipes(db, ingredients)
        
        recipe_count = db.query(Recipe).count()
        print(f"✅ Created {recipe_count} recipes")
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 