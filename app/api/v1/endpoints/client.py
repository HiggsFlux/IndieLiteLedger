from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.client import Client, FollowUp
# Try import Plugin Model
try:
    from app.modules.plugins.commercial_kit.models import LicenseRecord
except ImportError:
    LicenseRecord = None
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientDetailResponse, FollowUpCreate, FollowUpResponse
from app.schemas.response import ResponseModel, success

router = APIRouter()

@router.get("/list", response_model=ResponseModel[List[ClientResponse]])
def read_clients(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    status: Optional[int] = None
) -> Any:
    query = db.query(Client)
    
    # RBAC
    if current_user.role == "STAFF":
        query = query.filter(Client.creator_id == current_user.id)
        
    if name:
        query = query.filter(Client.name.ilike(f"%{name}%"))
    if phone:
        query = query.filter(Client.phone.ilike(f"%{phone}%"))
    if status is not None:
        query = query.filter(Client.status == status)
    
    clients = query.order_by(Client.created_at.desc()).offset(skip).limit(limit).all()
    return success(clients)

@router.post("/", response_model=ResponseModel[ClientResponse])
def create_client(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    client_in: ClientCreate
) -> Any:
    # Check if client exists (optional, e.g. by phone or name)
    if client_in.type == 1: # Enterprise
        existing = db.query(Client).filter(Client.name == client_in.name, Client.type == 1).first()
        if existing:
             raise HTTPException(status_code=400, detail="Enterprise name already exists")
    
    # Simple duplicate check for phone/wechat if provided
    if client_in.phone:
         existing_phone = db.query(Client).filter(Client.phone == client_in.phone).first()
         if existing_phone:
             raise HTTPException(status_code=400, detail="Phone number already exists")
    
    if client_in.wechat:
         existing_wechat = db.query(Client).filter(Client.wechat == client_in.wechat).first()
         if existing_wechat:
             raise HTTPException(status_code=400, detail="Wechat ID already exists")

    client_data = client_in.dict()
    client_data["creator_id"] = current_user.id
    client = Client(**client_data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return success(client)

@router.put("/{id}", response_model=ResponseModel[ClientResponse])
def update_client(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    id: str,
    client_in: ClientUpdate
) -> Any:
    client = db.query(Client).filter(Client.id == id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # RBAC
    if current_user.role == "STAFF" and client.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to update this client")
    
    update_data = client_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.add(client)
    db.commit()
    db.refresh(client)
    return success(client)

@router.get("/{id}", response_model=ResponseModel[ClientDetailResponse])
def read_client(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    id: str
) -> Any:
    client = db.query(Client).filter(Client.id == id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # RBAC
    if current_user.role == "STAFF" and client.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to view this client")
    
    # 1. Flatten extra_info
    extra = client.extra_info or {}
    
    # 2. Get Statistics
    # License Count (by customer_name matching client.name for now)
    license_count = 0
    if LicenseRecord:
        license_count = db.query(LicenseRecord).filter(LicenseRecord.customer_name == client.name).count()
    
    # Last Active (Latest FollowUp created_at)
    last_followup = db.query(FollowUp).filter(FollowUp.client_id == id).order_by(FollowUp.created_at.desc()).first()
    last_active = last_followup.created_at if last_followup else client.updated_at
    
    # Construct response
    client_dict = {
        "id": client.id,
        "type": client.type,
        "status": client.status,
        "source": client.source,
        "level": client.level,
        "tags": client.tags,
        "extra_info": client.extra_info,
        "name": client.name,
        "contact_person": client.contact_person,
        "position": client.position,
        "wechat": client.wechat,
        "phone": client.phone,
        "email": client.email,
        "tax_info": client.tax_info,
        "remark": client.remark,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
        
        # Flattened
        "website": extra.get("website"),
        "tech_tags": extra.get("tech_tags", []),
        "telegram": extra.get("telegram"),
        "contact_role": extra.get("contact_role"),
        "tax_code": extra.get("tax_code"),
        "bank_name": extra.get("bank_name"),
        "bank_account": extra.get("bank_account"),
        "reg_address": extra.get("reg_address"),
        
        # Stats
        "license_count": license_count,
        "last_active": last_active
    }
    
    return success(ClientDetailResponse(**client_dict))

@router.delete("/{id}", response_model=ResponseModel[dict])
def delete_client(
    *,
    db: Session = Depends(deps.get_db),
    id: str
) -> Any:
    client = db.query(Client).filter(Client.id == id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    return success({"ok": True})

# --- FollowUp ---

@router.get("/{id}/followups", response_model=ResponseModel[List[FollowUpResponse]])
def read_followups(
    *,
    db: Session = Depends(deps.get_db),
    id: str
) -> Any:
    followups = db.query(FollowUp).filter(FollowUp.client_id == id).order_by(FollowUp.created_at.desc()).all()
    return success(followups)

@router.post("/followup", response_model=ResponseModel[FollowUpResponse])
def create_followup(
    *,
    db: Session = Depends(deps.get_db),
    followup_in: FollowUpCreate
) -> Any:
    followup = FollowUp(**followup_in.dict())
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return success(followup)
