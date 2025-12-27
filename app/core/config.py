from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import model_validator
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    PROJECT_NAME: str = "IndieLiteLedger"
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

    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if self.SQLALCHEMY_DATABASE_URI:
            return self
        
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
