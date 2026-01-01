from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.api import deps
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.schemas.response import ResponseModel, success

router = APIRouter()

@router.get("", response_model=ResponseModel[List[RoleRead]])
def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve roles.
    """
    roles = db.query(Role).offset(skip).limit(limit).all()
    return success(roles)

@router.post("", response_model=ResponseModel[RoleRead])
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
) -> Any:
    """
    Create new role.
    """
    role = db.query(Role).filter(Role.code == role_in.code).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="The role with this code already exists.",
        )
    
    db_obj = Role(
        name=role_in.name,
        code=role_in.code,
        description=role_in.description,
        menu_keys=role_in.menu_keys,
        data_scope=role_in.data_scope,
        is_system=role_in.is_system
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return success(db_obj)

@router.put("/{role_id}", response_model=ResponseModel[RoleRead])
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: str,
    role_in: RoleUpdate,
) -> Any:
    """
    Update a role.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="The role with this id does not exist",
        )
        
    update_data = role_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(role, key, value)
        
    db.add(role)
    db.commit()
    db.refresh(role)
    return success(role)

@router.delete("/{role_id}", response_model=ResponseModel[dict])
def delete_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: str,
) -> Any:
    """
    Delete a role.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="The role with this id does not exist",
        )
    
    if role.is_system:
        raise HTTPException(
            status_code=400,
            detail="System roles cannot be deleted",
        )
        
    # Check if any user is assigned to this role
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete role because it is assigned to users",
        )
        
    db.delete(role)
    db.commit()
    return success({"ok": True})
