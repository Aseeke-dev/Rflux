from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RatingCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating scale between 0.5 and 5.0")
    
class RatingResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)