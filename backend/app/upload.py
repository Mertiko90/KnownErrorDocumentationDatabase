from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
import shutil, os
from datetime import datetime

from app.database import get_db
from app.models.article import Article
from app.schemas.routes.auth import get_current_staff_user
from app.models.user import User

router = APIRouter()
UPLOAD_FOLDER = "/app/documents"

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    article_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    article.document_path = filename
    db.commit()

    return {
        "filename": filename,
        "article_id": article.id,
        "message": "File uploaded and linked to article"
    }