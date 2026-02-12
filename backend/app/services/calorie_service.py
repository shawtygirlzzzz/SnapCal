"""
Calorie Service - Gemini 2.0 Flash AI for food recognition and nutrition estimation
"""

import asyncio
import random
import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai
from PIL import Image
from app.core.config import settings

class CalorieService:
    """
    AI service for food recognition and calorie estimation using Gemini 2.0 Flash
    Falls back to mock AI if Gemini fails or is disabled
    """
    
    # Mock database of Malaysian foods with nutrition data (fallback)
    MALAYSIAN_FOODS = {
        "nasi lemak": {
            "calories_per_100g": 350,
            "protein_g": 8.0,
            "carbs_g": 45.0,
            "fat_g": 15.0,
            "fiber_g": 2.0,
            "sodium_mg": 450,
            "typical_serving_g": 250
        },
        "rendang": {
            "calories_per_100g": 280,
            "protein_g": 25.0,
            "carbs_g": 8.0,
            "fat_g": 18.0,
            "fiber_g": 1.5,
            "sodium_mg": 380,
            "typical_serving_g": 150
        },
        "char kuey teow": {
            "calories_per_100g": 320,
            "protein_g": 12.0,
            "carbs_g": 35.0,
            "fat_g": 14.0,
            "fiber_g": 2.5,
            "sodium_mg": 520,
            "typical_serving_g": 200
        },
        "laksa": {
            "calories_per_100g": 180,
            "protein_g": 8.0,
            "carbs_g": 22.0,
            "fat_g": 7.0,
            "fiber_g": 3.0,
            "sodium_mg": 650,
            "typical_serving_g": 300
        },
        "satay": {
            "calories_per_100g": 270,
            "protein_g": 28.0,
            "carbs_g": 5.0,
            "fat_g": 15.0,
            "fiber_g": 0.5,
            "sodium_mg": 420,
            "typical_serving_g": 80
        },
        "roti canai": {
            "calories_per_100g": 300,
            "protein_g": 7.0,
            "carbs_g": 38.0,
            "fat_g": 13.0,
            "fiber_g": 1.5,
            "sodium_mg": 350,
            "typical_serving_g": 120
        },
        "mee goreng": {
            "calories_per_100g": 290,
            "protein_g": 10.0,
            "carbs_g": 40.0,
            "fat_g": 11.0,
            "fiber_g": 2.0,
            "sodium_mg": 480,
            "typical_serving_g": 180
        },
        "cendol": {
            "calories_per_100g": 160,
            "protein_g": 2.0,
            "carbs_g": 35.0,
            "fat_g": 3.0,
            "fiber_g": 1.0,
            "sodium_mg": 25,
            "typical_serving_g": 250
        },
        "teh tarik": {
            "calories_per_100g": 80,
            "protein_g": 3.0,
            "carbs_g": 12.0,
            "fat_g": 2.5,
            "fiber_g": 0.0,
            "sodium_mg": 40,
            "typical_serving_g": 200
        },
        "nasi goreng": {
            "calories_per_100g": 250,
            "protein_g": 6.0,
            "carbs_g": 38.0,
            "fat_g": 8.0,
            "fiber_g": 1.5,
            "sodium_mg": 400,
            "typical_serving_g": 220
        },
        "ayam penyet": {
            "calories_per_100g": 200,
            "protein_g": 22.0,
            "carbs_g": 5.0,
            "fat_g": 10.0,
            "fiber_g": 1.0,
            "sodium_mg": 350,
            "typical_serving_g": 180
        },
        "tom yam": {
            "calories_per_100g": 60,
            "protein_g": 8.0,
            "carbs_g": 5.0,
            "fat_g": 1.5,
            "fiber_g": 1.0,
            "sodium_mg": 800,
            "typical_serving_g": 300
        }
    }
    
    def __init__(self):
        self.model_version = "gemini-2.0-flash"
        self.gemini_model = None
        
        # Initialize Gemini if API key is provided
        if settings.GEMINI_API_KEY and settings.USE_GEMINI_AI:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
                print(f"✅ Gemini {settings.GEMINI_MODEL} initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize Gemini: {e}")
                print("🔄 Will use mock AI as fallback")
                self.gemini_model = None
        else:
            print("🔄 Using mock AI (Gemini disabled or no API key)")
    
    async def analyze_food_image(self, image_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze food image and return recognition results
        
        Args:
            image_path: Path to the uploaded image
            filename: Original filename
            
        Returns:
            Dictionary with food recognition and nutrition data
        """
        
        # Try Gemini first if available
        if self.gemini_model and settings.USE_GEMINI_AI:
            try:
                return await self._analyze_with_gemini(image_path, filename)
            except Exception as e:
                print(f"⚠️ Gemini analysis failed: {e}")
                print("🔄 Falling back to mock AI")
        
        # Fallback to mock AI
        return await self._analyze_with_mock_ai(image_path, filename)
    
    async def _analyze_with_gemini(self, image_path: str, filename: str) -> Dict[str, Any]:
        """Analyze food image using Gemini 2.0 Flash"""
        
        # Load and process image
        image = Image.open(image_path)
        
        # Prepare prompt for Malaysian food recognition
        prompt = self._create_analysis_prompt()
        
        try:
            # Generate response from Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.gemini_model.generate_content([prompt, image])
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Clean up response (remove markdown formatting if present)
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            analysis = json.loads(response_text)
            
            # Validate and format response
            return self._format_gemini_response(analysis)
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini JSON response: {e}")
            print(f"Raw response: {response.text[:200]}...")
            raise Exception("Invalid JSON response from Gemini")
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            raise e
    
    def _create_analysis_prompt(self) -> str:
        """Create analysis prompt for Gemini"""
        
        return """Analyze this food image and identify the dish. Focus on Malaysian, Southeast Asian, and common international cuisines.

Please provide a detailed analysis in the following JSON format:

{
  "food_name": "Name of the dish in English",
  "food_name_bm": "Name in Bahasa Malaysia (if applicable)",
  "confidence": 0.85,
  "estimated_weight_g": 250,
  "nutrition_per_100g": {
    "calories": 280,
    "protein_g": 12.5,
    "carbs_g": 35.0,
    "fat_g": 8.5,
    "fiber_g": 2.0,
    "sodium_mg": 450
  },
  "total_nutrition": {
    "calories": 700,
    "protein_g": 31.25,
    "carbs_g": 87.5,
    "fat_g": 21.25,
    "fiber_g": 5.0,
    "sodium_mg": 1125
  },
  "analysis_notes": "Brief description of the dish and portion estimation reasoning"
}

Instructions:
1. Identify the food as accurately as possible
2. If it's Malaysian cuisine, provide both English and Bahasa Malaysia names
3. Estimate the serving weight in grams based on visual cues
4. Provide realistic nutrition values per 100g
5. Calculate total nutrition based on estimated weight
6. Confidence should be 0.7-0.95 based on image clarity and food recognition certainty
7. If you're unsure, choose the most likely similar dish and note uncertainty in analysis_notes
8. For mixed dishes, estimate average values across components

Return only the JSON object, no additional text."""

    def _format_gemini_response(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format Gemini response to match expected format"""
        
        # Extract data with fallbacks
        food_name = analysis.get("food_name", "Unknown Dish")
        confidence = min(max(analysis.get("confidence", 0.8), 0.0), 1.0)
        estimated_weight = analysis.get("estimated_weight_g", 200)
        
        # Get nutrition data
        total_nutrition = analysis.get("total_nutrition", {})
        
        return {
            "food_name": food_name.title(),
            "food_name_bm": analysis.get("food_name_bm"),
            "confidence": round(confidence, 2),
            "calories": round(total_nutrition.get("calories", 250), 1),
            "weight_g": round(estimated_weight, 1),
            "nutrition": {
                "protein_g": round(total_nutrition.get("protein_g", 10.0), 1),
                "carbs_g": round(total_nutrition.get("carbs_g", 30.0), 1),
                "fat_g": round(total_nutrition.get("fat_g", 8.0), 1),
                "fiber_g": round(total_nutrition.get("fiber_g", 2.0), 1),
                "sodium_mg": round(total_nutrition.get("sodium_mg", 400), 1)
            },
            "model_version": self.model_version,
            "analysis_notes": analysis.get("analysis_notes", "")
        }
    
    async def _analyze_with_mock_ai(self, image_path: str, filename: str) -> Dict[str, Any]:
        """Fallback mock AI analysis"""
        
        # Simulate processing time
        if settings.MOCK_AI_ENABLED:
            await asyncio.sleep(settings.MOCK_AI_DELAY)
        
        # Mock food recognition - randomly select a Malaysian food
        recognized_food = random.choice(list(self.MALAYSIAN_FOODS.keys()))
        food_data = self.MALAYSIAN_FOODS[recognized_food]
        
        # Simulate confidence based on "image quality" (random for mock)
        confidence = random.uniform(0.75, 0.95)
        
        # Estimate serving size with some randomness
        serving_size_multiplier = random.uniform(0.8, 1.3)
        estimated_weight_g = food_data["typical_serving_g"] * serving_size_multiplier
        
        # Calculate nutrition based on estimated weight
        calories = (food_data["calories_per_100g"] * estimated_weight_g) / 100
        protein_g = (food_data["protein_g"] * estimated_weight_g) / 100
        carbs_g = (food_data["carbs_g"] * estimated_weight_g) / 100
        fat_g = (food_data["fat_g"] * estimated_weight_g) / 100
        fiber_g = (food_data["fiber_g"] * estimated_weight_g) / 100
        sodium_mg = (food_data["sodium_mg"] * estimated_weight_g) / 100
        
        return {
            "food_name": recognized_food.title(),
            "confidence": round(confidence, 2),
            "calories": round(calories, 1),
            "weight_g": round(estimated_weight_g, 1),
            "nutrition": {
                "protein_g": round(protein_g, 1),
                "carbs_g": round(carbs_g, 1),
                "fat_g": round(fat_g, 1),
                "fiber_g": round(fiber_g, 1),
                "sodium_mg": round(sodium_mg, 1)
            },
            "model_version": "mock_v1"
        }
    
    def get_food_nutrition_data(self, food_name: str) -> Dict[str, Any]:
        """
        Get nutrition data for a specific food item
        
        Args:
            food_name: Name of the food item
            
        Returns:
            Nutrition data dictionary
        """
        food_name_lower = food_name.lower()
        
        if food_name_lower in self.MALAYSIAN_FOODS:
            return self.MALAYSIAN_FOODS[food_name_lower]
        
        # Return default values for unknown foods
        return {
            "calories_per_100g": 200,
            "protein_g": 5.0,
            "carbs_g": 25.0,
            "fat_g": 8.0,
            "fiber_g": 1.0,
            "sodium_mg": 300,
            "typical_serving_g": 150
        }
    
    def estimate_calories_from_description(self, food_description: str, estimated_weight_g: float = None) -> Dict[str, Any]:
        """
        Estimate calories from text description
        
        Args:
            food_description: Description of the food
            estimated_weight_g: Optional weight estimate
            
        Returns:
            Calorie and nutrition estimates
        """
        # Simple keyword matching for mock implementation
        food_description_lower = food_description.lower()
        
        matched_food = None
        for food_name in self.MALAYSIAN_FOODS.keys():
            if food_name in food_description_lower:
                matched_food = food_name
                break
        
        if not matched_food:
            # Default to a generic Malaysian dish
            matched_food = "nasi goreng"
        
        food_data = self.MALAYSIAN_FOODS[matched_food]
        
        # Use provided weight or default serving size
        if estimated_weight_g is None:
            estimated_weight_g = food_data["typical_serving_g"]
        
        # Calculate nutrition
        calories = (food_data["calories_per_100g"] * estimated_weight_g) / 100
        protein_g = (food_data["protein_g"] * estimated_weight_g) / 100
        carbs_g = (food_data["carbs_g"] * estimated_weight_g) / 100
        fat_g = (food_data["fat_g"] * estimated_weight_g) / 100
        fiber_g = (food_data["fiber_g"] * estimated_weight_g) / 100
        sodium_mg = (food_data["sodium_mg"] * estimated_weight_g) / 100
        
        return {
            "food_name": matched_food.title(),
            "confidence": 0.8,  # Lower confidence for text-based matching
            "calories": round(calories, 1),
            "weight_g": round(estimated_weight_g, 1),
            "nutrition": {
                "protein_g": round(protein_g, 1),
                "carbs_g": round(carbs_g, 1),
                "fat_g": round(fat_g, 1),
                "fiber_g": round(fiber_g, 1),
                "sodium_mg": round(sodium_mg, 1)
            }
        } 