from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar('T')

class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int

class ResponseModel(BaseModel, Generic[T]):
    code: str = "0000"
    msg: str = "success"
    data: Optional[T] = None

def success(data: T = None, msg: str = "success") -> ResponseModel[T]:
    return ResponseModel(code="0000", msg=msg, data=data)

def error(code: str = "500", msg: str = "error", data: T = None) -> ResponseModel[T]:
    return ResponseModel(code=code, msg=msg, data=data)
