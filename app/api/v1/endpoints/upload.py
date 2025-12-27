from typing import Any
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from app.schemas.response import ResponseModel, success

router = APIRouter()

# Use absolute path relative to this file's location to avoid issues with working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("", response_model=ResponseModel[dict])
async def upload_file(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload a file and return the URL.
    """
    try:
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # In a real app, this should return a full URL or relative path handled by static file serving
        # Assuming we mount /static/uploads as /uploads
        url = f"/uploads/{filename}"
        
        return success({
            "name": file.filename,
            "url": url,
            "type": ext.replace('.', '')
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
