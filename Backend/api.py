from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from schemas import (
    ReviewCreate, 
    ReviewCreateResponse, 
    SentimentAnalysisResponse, 
    RecommendationPriorityResponse,
    RatingsDataResponse,
    AllReviewsResponse
)
from models import Review
from database import get_db
from Prediction import chain  # your LangChain chain
from analytics import sentiment_chain, priority_chain  # analytics chains

router = APIRouter(prefix="/api")

@router.post("/reviews", response_model=ReviewCreateResponse)
def submit_review(data: ReviewCreate, db: Session = Depends(get_db)):

    # Guard: long review
    if data.review and len(data.review) > 2000:
        raise HTTPException(status_code=400, detail="Review too long")

    # --- LLM call (server-side only) ---
    try:
        llm_output = chain.invoke({
            "rating": data.rating,
            "review": data.review
        })
    except Exception:
        llm_output = {
            "ai_summary": "Summary unavailable.",
            "ai_recommended_action": "Manual review recommended.",
            "ai_user_response": "Thank you for your feedback."
        }

    # --- Backend-owned fields ---
    review_id = uuid.uuid4()
    created_at = datetime.utcnow()

    # --- Persist EVERYTHING (admin + user data) ---
    review = Review(
        id=review_id,
        rating=data.rating,
        review_text=data.review,
        ai_summary=llm_output["ai_summary"],                  # admin-only
        ai_recommended_action=llm_output["ai_recommended_action"],  # admin-only
        ai_response=llm_output["ai_user_response"],           # user-facing
        created_at=created_at
    )

    db.add(review)
    db.commit()

    # --- User response (NO summary, NO recommendation) ---
    return {
        "success": True,
        "message": llm_output["ai_user_response"]
    }


@router.get("/analytics/sentiment", response_model=SentimentAnalysisResponse)
def get_overall_sentiment(db: Session = Depends(get_db)):
    """
    Admin endpoint: Analyzes the last 20 reviews for overall sentiment.
    Uses rating, review_text, and ai_summary to generate insights.
    """
    
    # Get last 20 reviews from database
    reviews = db.query(Review).order_by(Review.created_at.desc()).limit(20).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")
    
    # Format reviews data for LLM (only rating and AI summary)
    reviews_data = []
    for review in reviews:
        reviews_data.append(
            f"Rating: {review.rating}/5\n"
            f"Summary: {review.ai_summary}"
        )
    
    reviews_text = "\n\n".join(reviews_data)
    
    # Call sentiment analysis chain
    try:
        sentiment_output = sentiment_chain.invoke({
            "reviews_data": reviews_text
        })
        
        # Add total count
        sentiment_output["total_reviews_analyzed"] = len(reviews)
        
        return sentiment_output
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to analyze sentiment: {str(e)}"
        )


@router.get("/analytics/recommendations", response_model=RecommendationPriorityResponse)
def get_priority_recommendations(db: Session = Depends(get_db)):
    """
    Admin endpoint: Analyzes the last 50 AI-generated recommendations and creates a priority list.
    """
    
    # Get last 50 reviews with recommendations
    reviews = db.query(Review).filter(
        Review.ai_recommended_action.isnot(None)
    ).order_by(Review.created_at.desc()).limit(50).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No recommendations found")
    
    # Format recommendations data for LLM
    recommendations_data = []
    for i, review in enumerate(reviews, 1):
        recommendations_data.append(
            f"{i}. (Rating: {review.rating}/5) {review.ai_recommended_action}"
        )
    
    recommendations_text = "\n".join(recommendations_data)
    
    # Call priority analysis chain
    try:
        priority_output = priority_chain.invoke({
            "recommendations_data": recommendations_text
        })
        
        # Add total count
        priority_output["total_recommendations_analyzed"] = len(reviews)
        
        return priority_output
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to prioritize recommendations: {str(e)}"
        )


@router.get("/analytics/ratings", response_model=RatingsDataResponse)
def get_all_ratings(db: Session = Depends(get_db)):
    """
    Admin endpoint: Returns all ratings for visualization.
    Useful for creating charts, histograms, and trend analysis.
    """
    
    # Get all reviews
    reviews = db.query(Review).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")
    
    # Extract all ratings
    ratings = [review.rating for review in reviews]
    
    # Calculate average
    average_rating = sum(ratings) / len(ratings)
    
    return {
        "ratings": ratings,
        "total_reviews": len(ratings),
        "average_rating": round(average_rating, 2)
    }


@router.get("/admin/reviews", response_model=AllReviewsResponse)
def get_all_reviews(db: Session = Depends(get_db)):
    """
    Admin endpoint: Returns all reviews sorted by newest first.
    Includes full details: rating, review text, AI analysis, and timestamps.
    """
    
    # Get all reviews, sorted by created_at descending (newest first)
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")
    
    return {
        "reviews": reviews,
        "total_count": len(reviews)
    }

