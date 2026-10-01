from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.movies import MovieResponse, MovieRecomendationResponse

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language search query")
    limit: int = Field(default=5, ge=1, le=20)
    
class ReccommendationListResponse(BaseModel):
    user_id: Optional[int] = None
    feature_type: str
    recommendations: List[MovieRecomendationResponse]
    source: str = "database"