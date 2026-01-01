from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import model_validator
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    PROJECT_NAME: str = "TalkMyDataBoss"
    PROJECT_VERSION: str = "0.1.0"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "change_this_to_a_secure_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    MYSQL_SERVER: Optional[str] = None
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DB: Optional[str] = None
    MYSQL_PORT: Optional[str] = "3306"

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Uploads
    # Default to a local 'uploads' directory relative to the app
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if os.getenv("DATABASE_URL"):
            self.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
            # If UPLOAD_DIR is not set in environment, stick to default
            # But let's check for Docker storage mount regardless
        
        # In Docker, we might have /app/storage mounted
        storage_dir = "/app/storage"
        # Always prefer /app/storage if it exists (Docker volume mount)
        if os.path.isdir(storage_dir):
            print(f"Detected Docker storage mount at {storage_dir}")
            self.UPLOAD_DIR = os.path.join(storage_dir, "uploads")
            
            # Ensure upload dir exists immediately
            try:
                os.makedirs(self.UPLOAD_DIR, exist_ok=True)
                print(f"Ensured upload directory exists: {self.UPLOAD_DIR}")
            except Exception as e:
                print(f"Warning: Could not create upload dir {self.UPLOAD_DIR}: {e}")

            # Also use storage for sqlite if not using MySQL
            if not (self.MYSQL_SERVER and self.MYSQL_USER and self.MYSQL_DB) and not self.SQLALCHEMY_DATABASE_URI:
                self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(storage_dir, 'sql_app.db')}"
        else:
            print(f"No Docker storage found at {storage_dir}, using default local paths")
            # Ensure local upload dir exists
            try:
                os.makedirs(self.UPLOAD_DIR, exist_ok=True)
            except Exception:
                pass

        if not self.SQLALCHEMY_DATABASE_URI:
             if self.MYSQL_SERVER and self.MYSQL_USER and self.MYSQL_DB:
                self.SQLALCHEMY_DATABASE_URI = (
                    f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
                    f"{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
                )
             else:
                self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'sql_app.db')}"
            
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
