from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from fastapi.responses import HTMLResponse
from zipfile import ZipFile
import os
from lxml import etree

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

@router.get("/{article_id}/template", response_class=HTMLResponse)
def get_article_template(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    UPLOAD_FOLDER = "/app/documents"
    doc_content = ""

    if article.document_path:
        file_path = os.path.join(UPLOAD_FOLDER, article.document_path)
        if os.path.exists(file_path):
            try:
                with ZipFile(file_path) as z:
                    with z.open("word/document.xml") as f:
                        tree = etree.parse(f)
                        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                        paragraphs = []
                        for p in tree.findall(".//w:p", ns):
                            texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
                            if texts:
                                paragraphs.append("".join(texts))
                doc_content = "\n".join(paragraphs)
            except:
                pass

    cat = article.category.value if hasattr(article.category, "value") else str(article.category)
    date = article.created_at.strftime("%d.%m.%Y") if article.created_at else "—"
    tags = article.tags or "—"

    body_html = f"""
    <div class="section">
        <div class="section-label">Problem Description</div>
        <div class="section-body">{article.problem_description}</div>
    </div>
    <div class="section">
        <div class="section-label">Solution</div>
        <div class="section-body solution-body">{article.solution}</div>
    </div>"""

    if doc_content:
        body_html += f"""
    <div class="section">
        <div class="section-label">Word Document Content</div>
        <div class="section-body" style="font-size:13px;">{doc_content}</div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{article.title}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
<style>
  body{{font-family:'DM Sans',sans-serif;max-width:800px;margin:40px auto;padding:0 2rem;color:#1a1a1a}}
  .header{{border-bottom:2px solid #185FA5;padding-bottom:1rem;margin-bottom:2rem}}
  .logo{{font-family:'DM Serif Display',serif;font-size:18px;color:#185FA5;margin-bottom:.5rem}}
  h1{{font-family:'DM Serif Display',serif;font-size:26px;margin:0}}
  .meta{{display:flex;gap:2rem;margin:1rem 0;font-size:13px;color:#666;flex-wrap:wrap}}
  .section{{margin-bottom:2rem}}
  .section-label{{font-size:11px;font-weight:500;color:#185FA5;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}}
  .section-body{{background:#f8f8f6;border-left:3px solid #185FA5;padding:14px 16px;border-radius:0 8px 8px 0;font-size:14px;line-height:1.7;white-space:pre-wrap}}
  .solution-body{{background:#EAF3DE;border-left-color:#3B6D11}}
  .cat-badge{{display:inline-block;font-size:11px;padding:3px 10px;border-radius:100px;background:#E6F1FB;color:#185FA5;font-weight:500}}
  .tag{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:100px;background:#f0f0ee;color:#666;margin-right:4px}}
  .print-btn{{position:fixed;top:20px;right:20px;background:#185FA5;color:white;border:none;padding:8px 18px;border-radius:8px;cursor:pointer;font-size:13px;font-family:'DM Sans',sans-serif}}
  .print-btn:hover{{background:#0C447C}}
  @media print{{.print-btn{{display:none}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨 Print / PDF</button>
<div class="header">
  <div class="logo">KEDB.portal</div>
  <h1>{article.title}</h1>
  <div class="meta">
    <span><strong>Date:</strong> {date}</span>
    <span><strong>Category:</strong> <span class="cat-badge">{cat.upper()}</span></span>
    <span><strong>Views:</strong> {article.views}</span>
    {"<span><strong>Tags:</strong> " + "".join(f'<span class="tag">{t.strip()}</span>' for t in tags.split(",")) + "</span>" if article.tags else ""}
  </div>
</div>
{body_html}
</body></html>"""
    return HTMLResponse(content=html)

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