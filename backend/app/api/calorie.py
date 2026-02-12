"""
Calorie Analysis API endpoints
Handles food photo upload and calorie estimation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import time
import uuid
from pathlib import Path
from PIL import Image
import io

from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import CalorieUploadResponse
from app.services.calorie_service import CalorieService
from app.models.models import FoodRecognition

router = APIRouter()

@router.post("/upload", response_model=CalorieUploadResponse)
async def upload_food_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload food image for calorie estimation
    
    Accepts image files (JPEG, PNG, WebP) and returns:
    - Recognized food name
    - Estimated calories
    - Nutrition breakdown
    - Confidence score
    """
    start_time = time.time()
    
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read and validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    try:
        # Validate that it's a valid image
        image = Image.open(io.BytesIO(contents))
        image.verify()
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = Path(settings.UPLOAD_DIR) / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process image with mock AI service
        calorie_service = CalorieService()
        recognition_result = await calorie_service.analyze_food_image(
            image_path=str(file_path),
            filename=unique_filename
        )
        
        # Save results to database
        food_recognition = FoodRecognition(
            filename=unique_filename,
            file_path=str(file_path),
            file_size=len(contents),
            mime_type=file.content_type,
            recognized_food=recognition_result["food_name"],
            recognized_food_bm=recognition_result.get("food_name_bm"),
            confidence_score=recognition_result["confidence"],
            estimated_calories=recognition_result["calories"],
            estimated_weight_g=recognition_result["weight_g"],
            protein_g=recognition_result["nutrition"]["protein_g"],
            carbs_g=recognition_result["nutrition"]["carbs_g"],
            fat_g=recognition_result["nutrition"]["fat_g"],
            fiber_g=recognition_result["nutrition"]["fiber_g"],
            sodium_mg=recognition_result["nutrition"]["sodium_mg"],
            analysis_notes=recognition_result.get("analysis_notes"),
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        db.add(food_recognition)
        db.commit()
        db.refresh(food_recognition)
        
        # Return response
        return CalorieUploadResponse(
            id=food_recognition.id,
            filename=unique_filename,
            recognized_food=recognition_result["food_name"],
            recognized_food_bm=recognition_result.get("food_name_bm"),
            confidence_score=recognition_result["confidence"],
            estimated_calories=recognition_result["calories"],
            estimated_weight_g=recognition_result["weight_g"],
            nutrition=recognition_result["nutrition"],
            processing_time_ms=food_recognition.processing_time_ms,
            analysis_notes=recognition_result.get("analysis_notes"),
            model_version=recognition_result.get("model_version"),
            created_at=food_recognition.created_at
        )
        
    except Exception as e:
        # Clean up file if processing failed
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )

@router.get("/history")
async def get_calorie_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get history of calorie analysis results
    """
    recognitions = db.query(FoodRecognition)\
        .order_by(FoodRecognition.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    total_count = db.query(FoodRecognition).count()
    
    return {
        "total_count": total_count,
        "items": [
            {
                "id": r.id,
                "filename": r.filename,
                "recognized_food": r.recognized_food,
                "estimated_calories": r.estimated_calories,
                "confidence_score": r.confidence_score,
                "created_at": r.created_at
            }
            for r in recognitions
        ],
        "limit": limit,
        "offset": offset
    } 