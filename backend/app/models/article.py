from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
import enum

class CategoryEnum(enum.Enum):
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    SECURITY = "security"
    OTHER = "other"

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    problem_description = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    category = Column(Enum(CategoryEnum), default=CategoryEnum.OTHER)
    tags = Column(String)  # Comma-separated tags
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    document_path = Column(String, nullable=True)
    
    # Foreign key to user
    author_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship
    author = relationship("User", back_populates="articles")