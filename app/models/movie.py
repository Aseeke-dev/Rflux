from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, Float, String, Text
from sqlalchemy.orm import relationship
from app.core.base import Base

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    genres = Column(String(255), nullable=False)
    overview = Column(Text, nullable=True)
    
    embeddings = Column(Vector(384), nullable=True)
    
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")