from typing import List, Optional
from pydantic import BaseModel

class Login(BaseModel):
    userName: str
    password: str

class LoginToken(BaseModel):
    token: str
    refreshToken: str

class UserInfo(BaseModel):
    userId: str
    userName: str
    nickname: str
    roles: List[str]
    buttons: List[str]
    permissions: List[str] = []
    dataScope: int = 2

class RefreshToken(BaseModel):
    refreshToken: str
