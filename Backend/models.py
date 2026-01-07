from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid

class Review(Base):
    __tablename__ = "Review"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_recommended_action = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
