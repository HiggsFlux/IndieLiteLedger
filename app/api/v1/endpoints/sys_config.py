from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api import deps
from app.models.sys_config import SysConfig
from app.schemas.sys_config import SysConfigCreate, SysConfigRead, SysConfigUpdate
from app.schemas.response import ResponseModel, success

router = APIRouter()

@router.get("/public", response_model=ResponseModel[List[SysConfigRead]])
def read_public_configs(
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve public configurations.
    """
    configs = db.query(SysConfig).filter(SysConfig.is_public == True).all()
    return success(configs)

@router.get("", response_model=ResponseModel[List[SysConfigRead]])
def read_configs(
    group_code: str = None,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve all configurations (optionally filtered by group).
    """
    query = db.query(SysConfig)
    if group_code:
        query = query.filter(SysConfig.group_code == group_code)
    configs = query.all()
    return success(configs)

@router.post("", response_model=ResponseModel[SysConfigRead])
def create_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: SysConfigCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Create new configuration.
    """
    config = db.query(SysConfig).filter(SysConfig.config_key == config_in.config_key).first()
    if config:
        raise HTTPException(
            status_code=400,
            detail="The configuration with this key already exists.",
        )
    
    db_obj = SysConfig.from_orm(config_in)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return success(db_obj)

@router.put("/{config_key}", response_model=ResponseModel[SysConfigRead])
def update_config(
    *,
    db: Session = Depends(deps.get_db),
    config_key: str,
    config_in: SysConfigUpdate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Update a configuration.
    """
    config = db.query(SysConfig).filter(SysConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuration not found",
        )
    
    update_data = config_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    db.add(config)
    db.commit()
    db.refresh(config)
    return success(config)

@router.put("/bulk/update", response_model=ResponseModel[List[SysConfigRead]])
def update_configs_bulk(
    *,
    db: Session = Depends(deps.get_db),
    configs_in: Dict[str, str], # key: value map
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Bulk update configurations by key-value pairs.
    """
    updated_configs = []
    for key, value in configs_in.items():
        config = db.query(SysConfig).filter(SysConfig.config_key == key).first()
        if config:
            config.config_value = value
            db.add(config)
            updated_configs.append(config)
    
    db.commit()
    # Refresh all
    for config in updated_configs:
        db.refresh(config)
        
    return success(updated_configs)
