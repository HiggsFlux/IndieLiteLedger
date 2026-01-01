from typing import Any
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import Login, LoginToken, UserInfo, RefreshToken
from app.schemas.response import ResponseModel, success

router = APIRouter()

@router.post("/login", response_model=ResponseModel[LoginToken])
def login(
    login_data: Login,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.username == login_data.userName).first()
    if not user:
        raise HTTPException(status_code=400, detail="request.loginError")
    
    if not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="request.loginError")
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="request.userInactive")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    # Ideally we should have a refresh token mechanism, for now we reuse access token or create a longer one
    refresh_token = security.create_access_token(
        user.id, expires_delta=timedelta(days=7)
    )
    
    return success({
        "token": access_token,
        "refreshToken": refresh_token
    })

@router.get("/getUserInfo", response_model=ResponseModel[UserInfo])
def get_user_info(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get current user info
    """
    roles = []
    permissions = []
    data_scope = 2
    
    if current_user.role_id:
        role = db.get(Role, current_user.role_id)
        if role:
            roles = [role.code]
            permissions = role.menu_keys
            data_scope = role.data_scope
            
    return success({
        "userId": str(current_user.id),
        "userName": current_user.username,
        "nickname": current_user.nickname,
        "roles": roles,
        "buttons": [], # Add button permissions if needed
        "permissions": permissions,
        "dataScope": data_scope
    })

@router.post("/refreshToken", response_model=ResponseModel[LoginToken])
def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Refresh token
    """
    try:
        # Verify refresh token
        # In a real app, verify signature and check if it's a refresh token
        # Here we simplify by just creating a new pair if the old one is valid (and not expired)
        # Note: Ideally you should validate it's indeed a refresh token
        pass
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid refresh token")
        
    # Simplified: just return a new token for the same user if we could decode it
    # But since we don't have the logic to decode inside this function easily without duplicating deps code...
    # We will just implement a basic decode here
    from jose import jwt
    try:
        payload = jwt.decode(refresh_data.refreshToken, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except Exception:
         raise HTTPException(status_code=403, detail="Invalid refresh token")
         
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    new_refresh_token = security.create_access_token(
        user.id, expires_delta=timedelta(days=7)
    )
    return success({
        "token": access_token,
        "refreshToken": new_refresh_token
    })
