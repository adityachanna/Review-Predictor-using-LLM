from pydantic import BaseModel
from typing import List

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