from fastapi import APIRouter
from app.api.v1.endpoints import auth, client, order, upload, cost, user, role, analysis, sys_config

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(role.router, prefix="/system/role", tags=["role"])
api_router.include_router(sys_config.router, prefix="/system/config", tags=["sys-config"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(order.router, prefix="/orders", tags=["order"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
