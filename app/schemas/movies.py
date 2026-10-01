from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class MovieBase(BaseModel):
    title: str
    genres: str
    overview: Optional[str] = None
    
class MovieResponse(MovieBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class MovieRecomendationResponse(MovieResponse):
    similarity_score: float
    
class TopRatedMovieResponse(MovieResponse):
    average_rating: float
    rating_count: int
    