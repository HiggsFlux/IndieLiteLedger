from typing import Any
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
import logging
from app.schemas.response import ResponseModel, success
from app.core.config import settings

router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@router.post("", response_model=ResponseModel[dict])
async def upload_file(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload a file and return the URL.
    """
    logger.info(f"--- Upload Request Start ---")
    logger.info(f"File name: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Generate unique filename
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            # Fallback for files without extension
            mime_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'application/pdf': '.pdf'
            }
            ext = mime_map.get(file.content_type, '.bin')
            
        filename = f"{uuid.uuid4()}{ext}"
        
        # Ensure upload directory exists
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir, exist_ok=True)
                logger.info(f"Created upload directory: {upload_dir}")
            except Exception as e:
                logger.error(f"Failed to create upload directory {upload_dir}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to create upload directory: {str(e)}")
        
        # Check if directory is writable
        if not os.access(upload_dir, os.W_OK):
            logger.error(f"Upload directory is not writable: {upload_dir}")
            raise HTTPException(status_code=500, detail="Upload directory is not writable")
            
        file_path = os.path.join(upload_dir, filename)
        logger.info(f"Target path: {file_path}")
        
        # Save file with error checking
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except IOError as e:
            logger.error(f"Failed to write file to disk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Disk write error: {str(e)}")
            
        logger.info(f"File saved successfully: {filename}")
        
        # Check if file actually exists after saving
        if not os.path.exists(file_path):
            logger.error(f"File saved but not found on disk: {file_path}")
            raise HTTPException(status_code=500, detail="File verify failed after save")

        # Relative URL for frontend
        url = f"/uploads/{filename}"
        
        return success({
            "name": file.filename,
            "url": url,
            "type": ext.replace('.', '')
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload process failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
    finally:
        logger.info(f"--- Upload Request End ---")
