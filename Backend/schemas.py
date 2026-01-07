from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ReviewCreate(BaseModel):
    rating: int
    review: str

class ReviewCreateResponse(BaseModel):
    success: bool
    message: str

class SentimentAnalysisResponse(BaseModel):
    overall_sentiment: str
    sentiment_score: int
    key_themes: List[str]
    admin_insight: str
    total_reviews_analyzed: int

class PriorityRecommendation(BaseModel):
    action: str
    priority: str
    reason: str

class RecommendationPriorityResponse(BaseModel):
    priority_recommendations: List[PriorityRecommendation]
    quick_wins: List[str]
    long_term_improvements: List[str]
    total_recommendations_analyzed: int

class RatingsDataResponse(BaseModel):
    ratings: List[int]
    total_reviews: int
    average_rating: float

class ReviewDetail(BaseModel):
    id: UUID
    rating: int
    review_text: Optional[str]
    ai_summary: Optional[str]
    ai_recommended_action: Optional[str]
    ai_response: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models

class AllReviewsResponse(BaseModel):
    reviews: List[ReviewDetail]
    total_count: int