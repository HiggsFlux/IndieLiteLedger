from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api import deps
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.response import ResponseModel, success
from app.core.security import get_password_hash, verify_password
import uuid

router = APIRouter()

@router.get("", response_model=ResponseModel[List[UserRead]])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return success(users)

@router.post("", response_model=ResponseModel[UserRead])
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    db_obj = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        nickname=user_in.nickname,
        avatar=user_in.avatar,
        role_id=user_in.role_id, # Changed from role to role_id
        is_active=user_in.is_active
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return success(db_obj)

@router.put("/{user_id}", response_model=ResponseModel[UserRead])
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if update_data.get("password"):
        # Verify old password
        if not update_data.get("old_password"):
            raise HTTPException(
                status_code=400,
                detail="修改密码需要提供原密码进行验证",
            )
        
        if not verify_password(update_data["old_password"], user.hashed_password):
            raise HTTPException(
                status_code=400,
                detail="原密码不正确",
            )

        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
        if "old_password" in update_data:
            del update_data["old_password"]
        
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(user)

@router.delete("/{user_id}", response_model=ResponseModel[dict])
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
) -> Any:
    """
    Delete a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    db.delete(user)
    db.commit()
    return success({"ok": True})
