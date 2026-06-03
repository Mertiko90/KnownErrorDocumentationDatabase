from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# ⚠️ WICHTIG: Drei Punkte (..) weil routes in schemas/ liegt
from ...database import get_db
from ...models.article import Article
from ...models.user import User
from ..article import Article as ArticleSchema, ArticleCreate, ArticleUpdate
from .auth import get_current_user, get_current_staff_user

router = APIRouter(prefix="/articles", tags=["Articles"])

@router.get("/", response_model=List[ArticleSchema])
def get_all_articles(
    skip: int = 0,
    limit: int = 50,
    category: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Article)
    
    if category:
        query = query.filter(Article.category == category)
    
    if search:
        query = query.filter(
            (Article.title.ilike(f"%{search}%")) |
            (Article.problem_description.ilike(f"%{search}%")) |
            (Article.tags.ilike(f"%{search}%"))
        )
    
    articles = query.offset(skip).limit(limit).all()
    return articles

@router.get("/{article_id}", response_model=ArticleSchema)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    article.views += 1
    db.commit()
    
    return article

@router.post("/", response_model=ArticleSchema, status_code=status.HTTP_201_CREATED)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    db_article = Article(
        **article.model_dump(),
        author_id=current_user.id
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.put("/{article_id}", response_model=ArticleSchema)
def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    db_article = db.query(Article).filter(Article.id == article_id).first()
    
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = article_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_article, key, value)
    
    db.commit()
    db.refresh(db_article)
    return db_article

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    db_article = db.query(Article).filter(Article.id == article_id).first()
    
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    db.delete(db_article)
    db.commit()
    return None