from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.article import CategoryEnum

document_path: Optional[str] = None

class ArticleBase(BaseModel):
    title: str
    problem_description: str
    solution: str
    category: CategoryEnum
    tags: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    problem_description: Optional[str] = None
    solution: Optional[str] = None
    category: Optional[CategoryEnum] = None
    tags: Optional[str] = None

class Article(ArticleBase):
    id: int
    views: int
    created_at: datetime
    updated_at: datetime
    author_id: int

    class Config:
        from_attributes = True